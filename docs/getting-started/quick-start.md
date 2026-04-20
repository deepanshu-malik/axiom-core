# Quick Start

Get Axiom running end-to-end in five minutes. This assumes you have completed [Installation](installation.md).

---

## Step 1 — Start the Filesystem MCP Server

The MCP server exposes your local files. Start it in a dedicated terminal:

```bash
cd ~/axiom/axiom-mcp-servers
source .venv/bin/activate

python servers/filesystem/server.py
```

You should see:

```
Starting MCP server 'filesystem' with transport 'stdio'
```

The server is running and waiting for an MCP client to connect. Leave this terminal open.

---

## Step 2 — Start axiom-core

In a second terminal:

```bash
cd ~/axiom/axiom-core
source .venv/bin/activate

uvicorn axiom.api.main:app --reload --port 8000
```

Verify it's up:

```bash
curl http://localhost:8000/health
# → {"status": "healthy", "service": "axiom-core"}
```

Check your current configuration:

```bash
curl http://localhost:8000/config
# → shows active model, chunk size, retriever strategy, etc.
```

---

## Step 3 — Browse the API docs

Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser.

Swagger UI shows all available endpoints with interactive testing. Use it to:
- Inspect the request/response schemas
- Test the `/query` endpoint once it's implemented (Phase 4)
- Check the current config

---

## Step 4 — Inspect the MCP server

In a third terminal, use the MCP inspector to verify your filesystem server is correctly exposing your files:

```bash
cd ~/axiom/axiom-mcp-servers
source .venv/bin/activate

mcp-inspector python servers/filesystem/server.py
```

Open the inspector UI and try:

**Tools tab:**
- Call `list_allowed_directories` — should show your configured paths
- Call `list_directory` with `{"directory": "~/axiom"}` — should list the project files
- Call `search_files` with `{"pattern": "*.py", "directory": "~/axiom"}` — finds all Python files

**Prompts tab:**
- `summarize_file` — enter a file path, it generates a summarization prompt
- `project_overview` — enter a directory, it generates an overview prompt

---

## Step 5 — Run the Experiments

Before the full RAG pipeline is implemented in `axiom-core`, use the Jupyter notebooks to test models and retrieval strategies directly.

```bash
cd ~/axiom/axiom-experiments
source .venv/bin/activate

jupyter lab
```

Run notebooks in order:

| Notebook | What it tests |
|----------|---------------|
| `00_ollama_local_models.ipynb` | Ollama local models (no API key needed) |
| `01_model_testing.ipynb` | OpenAI and Anthropic models |
| `02_embedding_comparison.ipynb` | Embedding model quality and speed |
| `03_chunking_experiments.ipynb` | Chunking strategy impact on retrieval |
| `04_retrieval_strategies.ipynb` | Semantic vs hybrid vs keyword |
| `05_rag_pipeline.ipynb` | End-to-end RAG with best settings |
| `06_mcp_integration.ipynb` | Connecting MCP + RAG |

Start with `00` or `01` depending on whether you have Ollama installed.

---

## What Works Right Now

| Feature | Status |
|---------|--------|
| Filesystem MCP server — all 5 tools | ✅ Working |
| Filesystem MCP server — 3 prompts | ✅ Working |
| FastAPI `/health` and `/config` | ✅ Working |
| FastAPI `/query` | 🔲 Returns 501 (Phase 4) |
| Model abstraction layer | 🔲 Phase 2 |
| ChromaDB vector store | 🔲 Phase 3 |
| RAG query engine | 🔲 Phase 4 |

The experiments notebooks work independently and do not require Phase 2–4 to be complete.

---

## Connect to Claude Code or Claude Desktop

To use the filesystem server directly from Claude, add it to your MCP client config.

**Claude Code** — add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "axiom-filesystem": {
      "command": "python",
      "args": ["/home/deepanshumalik/axiom/axiom-mcp-servers/servers/filesystem/server.py"]
    }
  }
}
```

After restarting Claude Code, the tools (`list_directory`, `read_file`, `search_files`, etc.) will be available in every conversation.

---

→ **Next:** [Architecture Overview](../architecture/overview.md)

**Related:** [Filesystem Server](../mcp/filesystem-server.md) · [Experiments Guide](../experiments/notebooks.md)
