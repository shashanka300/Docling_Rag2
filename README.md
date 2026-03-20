# Docling Deep Agent RAG System

A production-ready **Agentic RAG (Retrieval-Augmented Generation)** system that combines Docling v2's advanced document parsing with Deep Agents orchestration for intelligent document Q&A.

## 🎯 Overview

This system processes multi-format documents (PDF, DOCX, PPTX, XLSX, images) and provides an AI-powered question-answering interface with specialized sub-agents for different content types. Built for enterprise use cases requiring grounded, citation-backed responses.

### Key Features

- 🤖 **Self-Reflecting AI**: Automatically grades retrieved context quality and refines queries
- 📄 **Multi-Format Support**: PDF, DOCX, PPTX, XLSX, CSV, XML, Images
- 🔍 **Semantic Search**: Qdrant vector store with metadata filtering
- 🎨 **Visual Understanding**: VLM-based figure captioning (SmolVLM-256M)
- 🧮 **Code Execution**: Isolated Docker sandbox for safe formula/code evaluation
- 📊 **Table Intelligence**: Specialized agent for structured data analysis
- 🔒 **Enterprise Security**: Network isolation, resource limits, non-root execution
- ☁️ **Cloud Storage**: IBM Cloud Object Storage integration for media files

## 🏗️ Architecture

```
User Query
    ↓
┌─────────────────────────────────────┐
│   Orchestrator (MiniMax-M2.7)       │
│   • Task Planning (write_todos)     │
│   • Self-Reflection Loop            │
│   • Memory Management               │
└─────────────────────────────────────┘
    ↓
┌───────────┬───────────┬───────────┬───────────┐
│  Ingest   │   Table   │   Image   │   Code    │
│  Agent    │   Agent   │   Agent   │   Agent   │
│           │           │           │           │
│ • Parse   │ • Analyze │ • VLM     │ • Execute │
│ • Chunk   │   tables  │   caption │   safely  │
│ • Embed   │ • Stats   │ • Charts  │ • Docker  │
└───────────┴───────────┴───────────┴───────────┘
    ↓
┌─────────────────────────────────────┐
│   Qdrant Vector Store (In-Memory)  │
│   • 384-dim embeddings              │
│   • Metadata filtering              │
│   • Cosine similarity search        │
└─────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Docker** (Desktop or Colima) — for code execution sandbox
- **Ollama** with MiniMax-M2.7 model

### Docker Setup (macOS)

You can run Docker on macOS using either Docker Desktop or the lighter-weight **Colima** (no GUI, no license fees).

#### Option A: Docker Desktop
Download and install from [docker.com](https://www.docker.com/products/docker-desktop/), then start it.

#### Option B: Colima (recommended for macOS)

```bash
# Install via Homebrew
brew install colima docker docker-compose

# Start Colima with resource limits (adjust to your machine)
colima start --cpu 4 --memory 8 --disk 50

# Verify Docker is working
docker info
docker run --rm hello-world
```

**Colima common commands:**
```bash
colima start          # Start the VM (run after reboot)
colima stop           # Stop the VM
colima status         # Check if running
colima start --edit   # Edit CPU/memory/disk config
```

> **Note:** The code-agent sandbox requires Docker to be running before you start the agent. With Colima, run `colima start` first. You can add it to your shell profile to auto-start: `colima start --foreground &`.

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/shashanka300/Docling_Rag2.git
cd Docling_Rag2
```

2. **Install dependencies using UV** (recommended)
```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install
uv sync
```

Or using pip:
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. **Set up Ollama with MiniMax-M2.7**
```bash
# Install Ollama from https://ollama.ai
ollama pull minimax-m2.7:cloud
```

4. **Configure environment** (optional)
```bash
# Create .env file for IBM COS credentials (if using cloud storage)
cp .env.example .env
# Edit .env with your credentials
```

5. **Prepare your documents**
```bash
# Create data directory
mkdir -p data
# Add your PDF, DOCX, or other supported files
```

### Running the Agent

**Interactive Mode:**
```bash
python docling_deep_agent/agent.py
```

**Demo Mode:**
```bash
python docling_deep_agent/agent.py --demo
```

**Programmatic Usage:**
```python
from docling_deep_agent.agent import run_agent

answer = run_agent("What are the key findings in the report?")
print(answer)
```

## 📚 Usage Examples

### 1. Ingest a Document
```
You: Ingest the file data/annual_report.pdf
Agent: Ingested 'data/annual_report.pdf' → 127 chunks stored 
       (95 text, 18 table, 14 picture). Texts: 342, Tables: 18, Pictures: 14.
```

### 2. Ask Questions with Citations
```
You: What were the Q3 revenue figures?
Agent: According to the Financial Summary table (page 12), Q3 revenue was 
       $2.4M, representing a 14.3% increase from Q2's $2.1M.
       Source: annual_report.pdf, pages 12-13
```

### 3. Analyze Tables
```
You: Compare the top 3 revenue items between Q2 and Q3
Agent: [Delegates to table-agent]
       Top 3 revenue items Q3 vs Q2:
       1. Product Sales: $1.2M (+18%) vs $1.0M
       2. Services: $800K (+10%) vs $725K
       3. Licensing: $400K (+5%) vs $380K
```

### 4. Execute Code/Formulas
```
You: Find the pricing formula and calculate it for x=42
Agent: [Delegates to code-agent]
       Formula: price = base_rate * (1 + x/100)
       Execution: price = 40 * (1 + 42/100) = $56.80
       Source: pricing_policy.pdf, page 8
```

### 5. Analyze Figures
```
You: What does Figure 3 show?
Agent: [Delegates to image-agent]
       Figure 3 (page 15) shows a bar chart comparing quarterly revenue 
       trends. The chart indicates steady growth across all quarters with 
       Q3 showing the highest performance.
```

## 🔧 Configuration

### Document Enrichment Levels

Control processing depth in your code:

```python
from docling_deep_agent.parser import EnrichmentConfig

# Minimal - fast, basic extraction
config = EnrichmentConfig.minimal()

# Code - enables code language detection + LaTeX formulas
config = EnrichmentConfig.for_code_agent()

# Image - enables VLM captioning + picture classification
config = EnrichmentConfig.for_image_agent()

# Full - all enrichments enabled (slower but richest metadata)
config = EnrichmentConfig.full()
```

### Chunking Strategy

```python
from docling_deep_agent.chunker import ChunkerConfig

config = ChunkerConfig(
    tokenizer="sentence-transformers/all-MiniLM-L6-v2",
    max_tokens=512,
    min_confidence=0.5,  # Filter low-quality chunks
    merge_peers=True,
    use_hierarchical=False
)
```

### Vector Store Options

```python
# In-memory (default - no setup required)
from qdrant_client import QdrantClient
client = QdrantClient(":memory:")

# Docker (persistent storage)
client = QdrantClient(url="http://localhost:6333")

# Cloud (production)
client = QdrantClient(
    url="https://your-cluster.qdrant.io",
    api_key="your-api-key"
)
```

### IBM Cloud Object Storage (Optional)

For media file management, configure COS in `.env`:

```bash
COS_ENDPOINT=https://s3.us-south.cloud-object-storage.appdomain.cloud
COS_API_KEY_ID=your_api_key
COS_INSTANCE_CRN=your_instance_crn
COS_BUCKET_NAME=your_bucket_name
COS_REGION=us-south
```

## 📁 Project Structure

```
docling_deep_agent/
├── agent.py          # Main orchestrator with self-reflection
├── parser.py         # Multi-format document parser (Docling v2)
├── chunker.py        # Chunking + confidence filtering + grading
├── store.py          # Qdrant vector store + retrieval tools
├── subagents.py      # Specialist sub-agents (ingest, table, image, code)
└── sandbox.py        # Docker-based code execution environment

cos_service.py        # IBM Cloud Object Storage integration
pyproject.toml        # Project dependencies (UV format)
requirements.txt      # Pip requirements
README.md            # This file
.gitignore           # Excludes .env, data/, docs/
```

## 🔐 Security Features

The Docker sandbox provides enterprise-grade isolation:

- ✅ **No host filesystem access** - Container is fully isolated
- ✅ **Network disabled** - `network_mode="none"` by default
- ✅ **Resource limits** - 512MB RAM, 50% CPU cap
- ✅ **Non-root execution** - Runs as `nobody` user
- ✅ **Capability dropping** - All Linux capabilities removed
- ✅ **Output truncation** - 32KB limit prevents context flooding
- ✅ **Temporary filesystem** - `/tmp` in memory only

## 🎓 How It Works

### 1. Document Ingestion Pipeline
```
PDF/DOCX/Image → Docling Parser → Confidence Filter → Chunks → Embeddings → Qdrant
```

### 2. Query Processing Flow
```
Question → Orchestrator → Task Planning → Retrieve & Grade → Specialist → Answer
```

### 3. Self-Reflection Loop
```
Retrieve chunks → Grade relevance (1-5) → If mean < 3.0:
    Decompose question → Re-query with sub-questions → Merge results
```

### 4. Sub-Agent Delegation
```
Question type detection:
  • Tables/numbers → table-agent
  • Figures/charts → image-agent
  • Code/formulas → code-agent (Docker sandbox)
  • General text → orchestrator handles directly
```

## 📊 Performance Benchmarks

- **Parsing**: ~2-5 seconds per PDF page (with enrichment)
- **Embedding**: ~100 chunks/second (CPU, all-MiniLM-L6-v2)
- **Retrieval**: <100ms for top-6 results (in-memory Qdrant)
- **LLM Response**: 2-10 seconds (MiniMax-M2.7 via Ollama)
- **Code Execution**: <5 seconds (Docker sandbox startup + execution)

## 🛠️ Development

### Running Tests
```bash
pytest tests/ -v
```

### Code Quality
```bash
# Format
black docling_deep_agent/

# Type checking
mypy docling_deep_agent/

# Linting
ruff check docling_deep_agent/
```

### Building Docker Image
```bash
# The sandbox image is built automatically on first use
# To rebuild manually:
docker build -t docling-code-sandbox:latest -f docling_deep_agent/Dockerfile .
```

## 🔄 Upgrading to Production

### 1. Persistent Vector Store
```python
# Replace in-memory Qdrant with Docker
docker run -p 6333:6333 qdrant/qdrant

# Update store.py
client = QdrantClient(url="http://localhost:6333")
```

### 2. Persistent Memory
```python
# Replace InMemoryStore with PostgreSQL
from langgraph.store.postgres import PostgresStore

store = PostgresStore.from_conn_string(os.environ["DATABASE_URL"])
store.setup()
```

### 3. Production LLM
```python
# Switch from Ollama to cloud API
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4", temperature=0)
```

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **Docling v2** - IBM's document understanding framework
- **Deep Agents** - Agentic orchestration framework
- **Qdrant** - High-performance vector database
- **Ollama** - Local LLM runtime
- **MiniMax-M2.7** - 230B parameter reasoning model

## 📧 Support

For questions or issues, please open an issue on GitHub.

---

**Built for Enterprise Document Intelligence** 📄🤖