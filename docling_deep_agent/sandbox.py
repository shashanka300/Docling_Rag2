"""
sandbox.py
─────────────────────────────────────────────────────────────────────────────
Custom Docker sandbox backend for the Deep Agents code sub-agent.

Why this exists
───────────────
Deep Agents officially supports Modal, Daytona, and Runloop sandboxes.
All are cloud-managed. For a fully local, zero-signup demo we implement the
same protocol using docker-py — the standard Docker SDK for Python.

How it maps to the official protocol
──────────────────────────────────────
The Deep Agents `BaseSandbox` requires one method: execute(command) → result.
Every filesystem tool (read_file, write_file, ls, glob, grep) is built on top
of execute() by the base class. We implement the same interface:

    DockerSandbox.execute(command: str) → ExecuteResult
        .output    : str   — combined stdout + stderr
        .exit_code : int
        .truncated : bool

Additionally we implement upload_files() and download_files() for seeding
extracted code from Docling into the container and retrieving outputs.

Security boundaries
───────────────────
• No host filesystem mount — container has no access to your files.
• No environment variable pass-through — your secrets stay on the host.
• Network disabled by default (network_mode="none").
• Memory and CPU hard-capped via Docker resource constraints.
• Each task() call gets a fresh container; it's removed after execute().

Requirements
────────────
    pip install docker
    # Docker Desktop or Docker Engine must be running locally.

Usage
─────
    sandbox = DockerSandbox.create()
    try:
        result = sandbox.execute("python --version")
        print(result.output)
    finally:
        sandbox.stop()
"""

from __future__ import annotations

import logging
import tarfile
import tempfile
import textwrap
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Optional

import docker
from docker.models.containers import Container

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Container image
# python:3.11-slim with scientific + code-analysis packages pre-baked.
# The Dockerfile string is used to build the image on first use.
# ─────────────────────────────────────────────────────────────────────────────

_SANDBOX_IMAGE = "docling-code-sandbox:latest"

_DOCKERFILE = textwrap.dedent("""\
    FROM python:3.11-slim

    # System deps for scientific packages
    RUN apt-get update && apt-get install -y --no-install-recommends \\
        build-essential gcc g++ \\
        && rm -rf /var/lib/apt/lists/*

    # Python packages available inside the sandbox
    RUN pip install --no-cache-dir \\
        pandas==2.2.* \\
        numpy==1.26.* \\
        sympy==1.13.* \\
        matplotlib==3.9.* \\
        scipy==1.14.* \\
        scikit-learn==1.5.* \\
        tabulate

    WORKDIR /workspace
""")


# ─────────────────────────────────────────────────────────────────────────────
# Result dataclass — mirrors the Deep Agents sandbox contract
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ExecuteResult:
    """
    Result of a sandbox execute() call.

    Matches the interface expected by Deep Agents' BaseSandbox —
    any tool that calls execute() receives this object.
    """
    output: str       # Combined stdout + stderr
    exit_code: int    # 0 = success
    truncated: bool = False  # True if output was clipped to MAX_OUTPUT_BYTES


MAX_OUTPUT_BYTES = 32_768   # 32 KB — prevents context window flooding


# ─────────────────────────────────────────────────────────────────────────────
# DockerSandbox
# ─────────────────────────────────────────────────────────────────────────────

class DockerSandbox:
    """
    Local Docker sandbox implementing the Deep Agents sandbox protocol.

    The code sub-agent uses this as its backend. When Deep Agents sees a
    backend that implements execute(), it automatically adds the `execute`
    tool to that agent's tool list and routes all filesystem operations
    through it.

    Parameters
    ----------
    container    : Running Docker container.
    docker_client: Connected docker.DockerClient.
    network_mode : "none" (default) = no internet. "bridge" = outbound ok.
    mem_limit    : Memory cap string e.g. "256m", "1g".
    cpu_period   : Docker cpu_period in microseconds.
    cpu_quota    : Docker cpu_quota — fraction of cpu_period available.
                   cpu_quota=50000 with cpu_period=100000 = 50% of one core.
    """

    def __init__(
        self,
        container: Container,
        docker_client: docker.DockerClient,
    ) -> None:
        self._container = container
        self._client    = docker_client
        self._stopped   = False

    # ── Factory ──────────────────────────────────────────────────────────────

    @classmethod
    def create(
        cls,
        network_mode: str = "none",
        mem_limit: str = "512m",
        cpu_period: int = 100_000,
        cpu_quota: int = 50_000,
        build_image: bool = True,
    ) -> "DockerSandbox":
        """
        Build the sandbox image (if needed) and start a container.

        Parameters
        ----------
        network_mode : "none" = isolated, "bridge" = outbound network access.
        mem_limit    : Memory cap for the container.
        cpu_period / cpu_quota : CPU throttle (default = 50% of one core).
        build_image  : If True, rebuild the image if it doesn't exist.

        Returns
        -------
        DockerSandbox instance wrapping the running container.
        """
        client = docker.from_env()

        # ── Build image if needed ─────────────────────────────────────────
        if build_image:
            try:
                client.images.get(_SANDBOX_IMAGE)
                logger.info("Sandbox image '%s' already exists", _SANDBOX_IMAGE)
            except docker.errors.ImageNotFound:
                logger.info("Building sandbox image '%s' …", _SANDBOX_IMAGE)
                cls._build_image(client)

        # ── Start container ───────────────────────────────────────────────
        container = client.containers.run(
            image=_SANDBOX_IMAGE,
            command="sleep infinity",    # Keep alive — we exec into it
            detach=True,
            network_mode=network_mode,
            mem_limit=mem_limit,
            cpu_period=cpu_period,
            cpu_quota=cpu_quota,
            # Security hardening
            read_only=False,            # /workspace needs writes
            security_opt=["no-new-privileges:true"],
            cap_drop=["ALL"],           # Drop all Linux capabilities
            tmpfs={"/tmp": "size=64m"}, # Writable /tmp in memory only
            environment={},             # Empty env — no host vars leaked
            user="nobody",             # Non-root execution
        )

        logger.info(
            "Sandbox container started: %s (mem=%s, net=%s)",
            container.short_id, mem_limit, network_mode,
        )
        return cls(container=container, docker_client=client)

    @classmethod
    def _build_image(cls, client: docker.DockerClient) -> None:
        """Build the sandbox Docker image from the inline Dockerfile."""
        dockerfile_bytes = _DOCKERFILE.encode()
        fileobj = BytesIO(dockerfile_bytes)

        # docker-py needs a tar archive containing the Dockerfile
        tar_buffer = BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
            info = tarfile.TarInfo(name="Dockerfile")
            info.size = len(dockerfile_bytes)
            tar.addfile(info, BytesIO(dockerfile_bytes))
        tar_buffer.seek(0)

        image, logs = client.images.build(
            fileobj=tar_buffer,
            custom_context=True,
            tag=_SANDBOX_IMAGE,
            rm=True,
        )
        for log in logs:
            if "stream" in log:
                logger.debug("Docker build: %s", log["stream"].rstrip())
        logger.info("Sandbox image built: %s", _SANDBOX_IMAGE)

    # ── Core protocol method ─────────────────────────────────────────────────

    def execute(self, command: str) -> ExecuteResult:
        """
        Run a shell command inside the container and return the result.

        This is the single method required by the Deep Agents sandbox protocol.
        All filesystem tools (read_file, write_file, ls …) built by BaseSandbox
        call this method under the hood.

        Parameters
        ----------
        command : Shell command string. Runs as /bin/sh -c "{command}".

        Returns
        -------
        ExecuteResult with .output, .exit_code, .truncated.
        """
        if self._stopped:
            raise RuntimeError("Sandbox has been stopped. Create a new instance.")

        try:
            exit_code, output_raw = self._container.exec_run(
                cmd=["/bin/sh", "-c", command],
                stdout=True,
                stderr=True,
                demux=False,
            )
        except Exception as exc:
            logger.error("Container exec_run failed: %s", exc)
            return ExecuteResult(output=str(exc), exit_code=1)

        output_bytes: bytes = output_raw or b""
        truncated = False

        if len(output_bytes) > MAX_OUTPUT_BYTES:
            output_bytes = output_bytes[:MAX_OUTPUT_BYTES]
            truncated = True

        output = output_bytes.decode("utf-8", errors="replace")

        if truncated:
            output += (
                "\n\n[Output truncated — too large for context window. "
                "Use read_file to access the full result.]"
            )
            logger.warning("Command output truncated at %d bytes", MAX_OUTPUT_BYTES)

        logger.debug(
            "execute() exit_code=%d | cmd='%s…' | output_len=%d",
            exit_code, command[:60], len(output),
        )
        return ExecuteResult(
            output=output,
            exit_code=exit_code,
            truncated=truncated,
        )

    # ── File transfer API ────────────────────────────────────────────────────

    def upload_files(self, files: list[tuple[str, bytes]]) -> None:
        """
        Copy files from the host into the container.

        Used by the code sub-agent to seed Docling-extracted code/formula
        content into /workspace/ before calling execute().

        Parameters
        ----------
        files : List of (absolute_container_path, content_bytes) tuples.
                Example: [("/workspace/formula.py", b"import sympy\n...")]
        """
        if not files:
            return

        # Build an in-memory tar archive
        tar_buffer = BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
            for path_str, content in files:
                path = Path(path_str)
                info = tarfile.TarInfo(name=str(path).lstrip("/"))
                info.size = len(content)
                tar.addfile(info, BytesIO(content))
        tar_buffer.seek(0)

        # put_archive uploads to the container
        # We target "/" so the relative paths inside the tar are preserved.
        self._container.put_archive("/", tar_buffer)
        logger.info("Uploaded %d file(s) to sandbox", len(files))

    def download_files(self, paths: list[str]) -> list[dict]:
        """
        Retrieve files from the container after execution.

        Parameters
        ----------
        paths : List of absolute container paths.

        Returns
        -------
        List of dicts: [{"path": str, "content": bytes | None, "error": str | None}]
        """
        results = []
        for path_str in paths:
            try:
                bits, _ = self._container.get_archive(path_str)
                raw = b"".join(bits)
                tar_buf = BytesIO(raw)
                with tarfile.open(fileobj=tar_buf) as tar:
                    members = tar.getmembers()
                    if members:
                        f = tar.extractfile(members[0])
                        content = f.read() if f else b""
                    else:
                        content = b""
                results.append({"path": path_str, "content": content, "error": None})
            except Exception as exc:
                results.append({"path": path_str, "content": None, "error": str(exc)})
                logger.warning("Failed to download '%s': %s", path_str, exc)

        return results

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def stop(self) -> None:
        """
        Stop and remove the container.

        Always call this in a finally block. The container consumes RAM
        and a Docker socket connection until explicitly stopped.

        Example
        -------
        sandbox = DockerSandbox.create()
        try:
            result = sandbox.execute("python script.py")
        finally:
            sandbox.stop()
        """
        if self._stopped:
            return
        try:
            self._container.stop(timeout=5)
            self._container.remove(force=True)
            self._stopped = True
            logger.info("Sandbox container stopped and removed")
        except Exception as exc:
            logger.warning("Error during sandbox cleanup: %s", exc)

    def __enter__(self) -> "DockerSandbox":
        return self

    def __exit__(self, *args) -> None:
        self.stop()

    # ── Convenience: run a code snippet end-to-end ──────────────────────────

    def run_code_snippet(
        self,
        code: str,
        filename: str = "script.py",
        timeout_seconds: int = 30,
    ) -> ExecuteResult:
        """
        Seed a code string as a file and execute it. Convenience wrapper
        used by the code sub-agent for quick one-shot evaluations.

        Parameters
        ----------
        code     : Python source code string.
        filename : Name to save the file as under /workspace/.
        timeout  : Not enforced at SDK level — use Docker's exec timeout
                   if you need hard limits (future extension point).
        """
        container_path = f"/workspace/{filename}"
        self.upload_files([(container_path, code.encode())])
        return self.execute(f"python {container_path}")

    # ── Properties ───────────────────────────────────────────────────────────

    @property
    def container_id(self) -> str:
        return self._container.short_id

    @property
    def is_running(self) -> bool:
        if self._stopped:
            return False
        try:
            self._container.reload()
            return self._container.status == "running"
        except Exception:
            return False


# ─────────────────────────────────────────────────────────────────────────────
# LangChain tool wrapper
# Exposes sandbox execution as a named tool the code sub-agent can call.
# ─────────────────────────────────────────────────────────────────────────────

def make_execute_tool(sandbox: DockerSandbox):
    """
    Return a LangChain @tool that runs commands in the given sandbox.

    The code sub-agent receives this tool in its tool list so it can
    execute Python code isolated from the host machine.

    Parameters
    ----------
    sandbox : A running DockerSandbox instance.

    Returns
    -------
    A LangChain tool function bound to this sandbox.
    """
    from langchain_core.tools import tool as lc_tool

    @lc_tool
    def execute_in_sandbox(command: str) -> str:
        """
        Execute a shell command inside the isolated Docker sandbox.

        Use this to run Python scripts, install packages (pip install …),
        or evaluate extracted code and formulas safely.

        Parameters
        ----------
        command : Shell command. Examples:
                  "python /workspace/formula.py"
                  "pip install sympy && python /workspace/eval.py"
                  "ls /workspace"

        Returns
        -------
        Combined stdout + stderr and the exit code.
        """
        result = sandbox.execute(command)
        status = "SUCCESS" if result.exit_code == 0 else f"FAILED (exit {result.exit_code})"
        return f"[{status}]\n{result.output}"

    return execute_in_sandbox


def make_upload_tool(sandbox: DockerSandbox):
    """
    Return a LangChain @tool for seeding code files into the sandbox.
    The code sub-agent uses this before calling execute_in_sandbox.
    """
    from langchain_core.tools import tool as lc_tool

    @lc_tool
    def upload_code_to_sandbox(filename: str, code: str) -> str:
        """
        Write a code string into /workspace/<filename> inside the sandbox.

        Call this before execute_in_sandbox to seed the file you want to run.

        Parameters
        ----------
        filename : Filename only (no path). Saved to /workspace/<filename>.
        code     : Full Python source code as a string.
        """
        path = f"/workspace/{filename}"
        try:
            sandbox.upload_files([(path, code.encode())])
            return f"File written to {path} ({len(code)} bytes)"
        except Exception as exc:
            return f"Upload failed: {exc}"

    return upload_code_to_sandbox
