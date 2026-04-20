# axiom-core

The FastAPI backend for Axiom. Orchestrates the RAG pipeline, manages LLM providers, and connects to MCP servers.

---

## Module Reference

| Module | Status | Docs |
|--------|--------|------|
| `api/` — FastAPI routes | ✅ Working | [API Reference](api-reference.md) |
| `config/` — Pydantic settings | ✅ Working | [API Reference](api-reference.md#configuration) |
| `models/` — LLM abstraction | 🔲 Phase 2 | [Models](models.md) |
| `vectorstore/` — ChromaDB | 🔲 Phase 3 | [Vector Store](vectorstore.md) |
| `rag/` — Query engine | 🔲 Phase 4 | [RAG Engine](rag-engine.md) |
| `mcp/` — MCP client | 🔲 Phase 4 | [RAG Engine](rag-engine.md#mcp-client) |

---

## Repository Structure

```
axiom-core/
├── src/axiom/
│   ├── __init__.py          ← version: "0.1.0"
│   ├── api/
│   │   ├── main.py          ← FastAPI app, router registration
│   │   ├── health.py        ← GET /health
│   │   ├── config.py        ← GET /config
│   │   └── query.py         ← POST /query (Phase 4)
│   ├── config/
│   │   └── settings.py      ← Pydantic Settings
│   ├── models/              ← Phase 2
│   ├── vectorstore/         ← Phase 3
│   ├── rag/
│   │   ├── retrievers/      ← Phase 4
│   │   └── rerankers/       ← Phase 4
│   └── mcp/                 ← Phase 4
├── tests/
│   ├── unit/
│   └── integration/
├── docs/                    ← You are here
└── pyproject.toml
```

---

## Quick Start

```bash
cd axiom-core
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env
# Edit .env with your API keys

uvicorn axiom.api.main:app --reload
# → http://localhost:8000
# → http://localhost:8000/docs
# → http://localhost:8000/health
```

---

## Running Tests

```bash
cd axiom-core
source .venv/bin/activate

pytest tests/ -v
```

---

## Development Phases

| Phase | What gets built | Target |
|-------|----------------|--------|
| Phase 2 | `models/` — BaseLLM, OpenAI, Anthropic, Ollama | After `01_model_testing.ipynb` |
| Phase 3 | `vectorstore/` — ChromaDB, DocumentIndexer | After `02_embedding_comparison.ipynb` + `03_chunking_experiments.ipynb` |
| Phase 4 | `rag/` — QueryEngine, retrievers; `mcp/` — MCPManager; wire `/query` | After all experiment notebooks |

---

## Related Project Docs

- [API Overview](../../docs/api/overview.md)
- [Endpoints Reference](../../docs/api/endpoints.md)
- [Architecture Overview](../../docs/architecture/overview.md)
- [Data Flow](../../docs/architecture/data-flow.md)
- [RAG Pipeline](../../docs/rag/pipeline.md)
- [Model Layer Overview](../../docs/models/overview.md)
