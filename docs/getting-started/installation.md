# Installation

This guide sets up all three Axiom repositories on your local machine.

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.11+ | Required by all repos |
| Git | Any | For cloning |
| Node.js | 18+ | For MCP inspector (optional) |
| Ollama | Latest | Only if using local models |

---

## Repository Layout

Axiom uses a monorepo-style workspace. Clone everything into one parent directory:

```
axiom/                       ← workspace root
├── axiom-core/
├── axiom-mcp-servers/
└── axiom-experiments/
```

The repositories are already inside `~/axiom` if you followed the project setup.

---

## 1. axiom-mcp-servers

The MCP servers run independently. Set them up first.

```bash
cd ~/axiom/axiom-mcp-servers

# Create virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Verify
python -c "import fastmcp; print('fastmcp OK')"
```

### Configure allowed directories

Edit `servers/filesystem/config.yaml` to point to your actual directories:

```yaml
allowed_directories:
  - ~/axiom          # The Axiom workspace
  - ~/Documents      # Personal notes
  - ~/projects       # Other codebases
```

Only paths listed here will be accessible through the filesystem server.

---

## 2. axiom-core

The FastAPI backend. This is the main application.

```bash
cd ~/axiom/axiom-core

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env
```

Edit `.env` with your API keys:

```bash
# Required for OpenAI models
OPENAI_API_KEY=sk-...

# Required for Anthropic models
ANTHROPIC_API_KEY=sk-ant-...

# Optional: GitHub MCP server
GITHUB_TOKEN=ghp_...

# Model selection (defaults shown)
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small

# RAG configuration
RETRIEVER_STRATEGY=hybrid
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K=5
```

### Verify the install

```bash
uvicorn axiom.api.main:app --reload
# Open http://localhost:8000/health → should return {"status": "healthy"}
```

---

## 3. axiom-experiments

The Jupyter notebook environment for testing models and RAG strategies before building them into `axiom-core`.

```bash
cd ~/axiom/axiom-experiments

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install all experiment dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Add the same API keys as axiom-core
```

### Start Jupyter

```bash
jupyter lab
# Opens at http://localhost:8888
```

---

## 4. Ollama (optional — local models)

If you want to run Llama or Qwen locally without API costs:

```bash
# Install Ollama from https://ollama.com
# Then pull the models you want to test:

ollama pull llama3.2
ollama pull qwen2.5

# Verify Ollama is running
curl http://localhost:11434/api/tags
```

---

## 5. MCP Inspector (optional — debug MCP servers)

```bash
npm install -g @modelcontextprotocol/inspector

# Test the filesystem server
cd ~/axiom/axiom-mcp-servers
mcp-inspector python servers/filesystem/server.py
```

---

## Environment Variable Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | OpenAI API key |
| `ANTHROPIC_API_KEY` | — | Anthropic API key |
| `GITHUB_TOKEN` | — | GitHub personal access token |
| `LLM_PROVIDER` | `openai` | `openai` \| `anthropic` \| `ollama` |
| `LLM_MODEL` | `gpt-4o-mini` | Model name for the selected provider |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | OpenAI embedding model |
| `RETRIEVER_STRATEGY` | `hybrid` | `semantic` \| `hybrid` \| `keyword` |
| `CHUNK_SIZE` | `1000` | Characters per document chunk |
| `CHUNK_OVERLAP` | `200` | Overlap between consecutive chunks |
| `TOP_K` | `5` | Number of documents to retrieve per query |
| `RERANK` | `false` | Enable Cohere reranking |
| `CHROMA_PERSIST_DIR` | `./chroma_db` | Where ChromaDB stores its data |
| `COLLECTION_NAME` | `axiom_knowledge` | ChromaDB collection name |
| `API_HOST` | `0.0.0.0` | FastAPI host |
| `API_PORT` | `8000` | FastAPI port |

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'fastmcp'`**
Make sure you activated the correct virtual environment for the repo you're working in. Each repo has its own `.venv`.

**`Access denied` from the filesystem server**
The path is not in `allowed_directories` in `servers/filesystem/config.yaml`. Add it and restart the server.

**ChromaDB errors on startup**
Delete `axiom-core/chroma_db/` and reindex. The database schema can change between ChromaDB versions.

**Ollama connection refused**
Run `ollama serve` in a separate terminal. Ollama must be running before the server starts.

---

→ **Next:** [Quick Start](quick-start.md)

**Related:** [Architecture Overview](../architecture/overview.md) · [API Overview](../api/overview.md)
