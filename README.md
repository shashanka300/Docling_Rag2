# Docling Deep Agent RAG System

An **Agentic RAG (Retrieval-Augmented Generation)** system built for BCBSKS customer service representatives, combining document intelligence with AI assistance to help answer policy questions, handle prior authorizations, and provide member support.

## 🎯 Overview

This system uses **Docling v2** for multi-format document parsing, **Qdrant** for vector storage, and **Deep Agents** orchestration to create an intelligent document Q&A assistant with specialized sub-agents for different content types.

### Key Features

- 🤖 **Self-Reflecting AI**: Automatically grades retrieved context and refines queries
- 📄 **Multi-Format Support**: PDF, DOCX, PPTX, XLSX, CSV, XML, Images
- 🔍 **Semantic Search**: Vector-based retrieval with metadata filtering
- 🎨 **Visual Understanding**: VLM-based figure captioning and chart analysis
- 🧮 **Code Execution**: Safe Docker sandbox for formulas and code blocks
- 📊 **Table Intelligence**: Specialized agent for structured data analysis
- 🔒 **Secure**: Isolated execution environment with resource limits

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator Agent                        │
│              (MiniMax-M2.7 via Ollama)                      │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Ingest Agent │    │ Table Agent  │    │ Image Agent  │
│              │    │              │    │              │
│ • Parse docs │    │ • Analyze    │    │ • VLM        │
│ • Chunk      │    │   tables     │    │   captions   │
│ • Embed      │    │ • Compare    │    │ • Chart      │
│ • Store      │    │   data       │    │   analysis   │
└──────────────┘    └──────────────┘    └──────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │  Code Agent  │
                    │              │
                    │ • Execute    │
                    │   formulas   │
                    │ • Run code   │
                    │ • Docker     │
                    │   sandbox    │
                    └──────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │    Qdrant    │
                    │ Vector Store │
                    └──────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker Desktop (for code execution sandbox)
- Ollama with MiniMax-M2.7 model

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/shashanka300/Docling_Rag2.git
cd Docling_Rag2
```

2. **Install dependencies using UV** (recommended)
```bash
# Install UV if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv sync
```

Or using pip:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. **Set up Ollama with MiniMax-M2.7**
```bash
# Install Ollama from https://ollama.ai
ollama pull minimax-m2.7:cloud
```

4. **Create `.env` file** (optional)
```bash
# Add any environment variables if needed
touch .env
```

5. **Add your documents**
```bash
# Create data directory and add your documents
mkdir -p data
# Copy your PDF, DOCX, or other supported files to data/
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

answer = run_agent("What are the prior authorization requirements for imaging?")
print(answer)
```

## 📚 Usage Examples

### 1. Ingest a Document
```
You: Ingest the file data/policy_document.pdf
Agent: Ingested 'data/policy_document.pdf' → 127 chunks stored (95 text, 18 table, 14 picture).
```

### 2. Ask Questions
```
You: What are the coverage requirements for outpatient MRI?
Agent: According to the Prior Authorization Policy (pages 12-13), outpatient MRI 
imaging requires prior authorization for Medicare Advantage members when ordered 
for non-emergency conditions...
```

### 3. Analyze Tables
```
You: Compare the revenue figures in Q3 vs Q2
Agent: [Delegates to table-agent]
Q3 revenue was $2.4M compared to Q2's $2.1M, representing a 14.3% increase...
```

### 4. Execute Code
```
You: Find the pricing formula and calculate it for x=42
Agent: [Delegates to code-agent]
Formula: price = base_rate * (1 + x/100)
Result: $56.84
```

## 🔧 Configuration

### Enrichment Levels

Control document processing depth in [`parser.py`](docling_deep_agent/parser.py):

```python
# Minimal - fast, basic extraction
EnrichmentConfig.minimal()

# Code - enables code language detection + LaTeX formulas
EnrichmentConfig.for_code_agent()

# Image - enables VLM captioning + picture classification
EnrichmentConfig.for_image_agent()

# Full - all enrichments enabled
EnrichmentConfig.full()
```

### Chunking Strategy

Configure in [`chunker.py`](docling_deep_agent/chunker.py):

```python
ChunkerConfig(
    tokenizer="sentence-transformers/all-MiniLM-L6-v2",
    max_tokens=512,
    min_confidence=0.5,  # Filter low-quality chunks
    merge_peers=True,
    use_hierarchical=False
)
```

### Vector Store

Switch from in-memory to persistent storage in [`store.py`](docling_deep_agent/store.py):

```python
# In-memory (default)
client = QdrantClient(":memory:")

# Docker
client = QdrantClient(url="http://localhost:6333")

# Cloud
client = QdrantClient(
    url="https://your-cluster.qdrant.io",
    api_key="your-api-key"
)
```

## 📁 Project Structure

```
docling_deep_agent/
├── agent.py          # Main orchestrator with self-reflection
├── parser.py         # Multi-format document parser (Docling v2)
├── chunker.py        # Chunking + confidence filtering
├── store.py          # Qdrant vector store + retrieval
├── subagents.py      # Specialist sub-agents (ingest, table, image, code)
└── sandbox.py        # Docker-based code execution environment

docs/
├── requirements.md              # Business requirements
├── PLAN_SUMMARY.md             # Implementation plan
├── technical_specifications.md  # Code examples & specs
├── component_hierarchy.md       # Component structure
└── implementation_plan.md       # Detailed implementation

data/                 # Your documents (not in git)
├── *.pdf
├── *.docx
└── ...

.env                  # Environment variables (not in git)
pyproject.toml        # Project dependencies
requirements.txt      # Pip requirements
```

## 🔐 Security

The Docker sandbox provides multiple security layers:

- ✅ **No host filesystem access** - Container is isolated
- ✅ **Network disabled** - `network_mode="none"` by default
- ✅ **Resource limits** - 512MB RAM, 50% CPU cap
- ✅ **Non-root execution** - Runs as `nobody` user
- ✅ **Capability dropping** - All Linux capabilities removed
- ✅ **Output truncation** - 32KB limit prevents context flooding

## 🎓 How It Works

### 1. Document Ingestion
```
PDF/DOCX → Docling Parser → Chunks → Embeddings → Qdrant
```

### 2. Query Processing
```
Question → Orchestrator → Retrieve & Grade → Specialist Sub-Agent → Answer
```

### 3. Self-Reflection Loop
```
If relevance_score < 3.0:
    Decompose question → Re-query → Merge results
```

## 🛠️ Development

### Running Tests
```bash
# Add your test files to tests/
pytest tests/
```

### Code Quality
```bash
# Format code
black docling_deep_agent/

# Type checking
mypy docling_deep_agent/

# Linting
ruff check docling_deep_agent/
```

## 📊 Performance

- **Parsing**: ~2-5 seconds per PDF page (with enrichment)
- **Embedding**: ~100 chunks/second (CPU)
- **Retrieval**: <100ms for top-6 results (in-memory)
- **LLM Response**: 2-10 seconds (depends on Ollama setup)

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Docling v2** - IBM's document understanding framework
- **Deep Agents** - Agentic orchestration framework
- **Qdrant** - Vector database
- **Ollama** - Local LLM runtime
- **MiniMax-M2.7** - 230B parameter reasoning model

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Built for BCBSKS Customer Service Excellence** 🏥