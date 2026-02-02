# Axiom Core

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Axiom Core** is the FastAPI backend for Axiom, a personal knowledge assistant that uses RAG (Retrieval-Augmented Generation) to query your local files, GitHub repos, and documents through natural language.

## Project Status

| Component | Status |
|-----------|--------|
| FastAPI App Structure | ✅ Complete |
| Health/Config Endpoints | ✅ Complete |
| Pydantic Settings | ✅ Complete |
| Model Abstraction Layer | 🔲 Phase 2 (Next) |
| Vector Store (ChromaDB) | 🔲 Phase 3 |
| RAG Query Engine | 🔲 Phase 4 |
| Query Endpoint | 🔲 Phase 4 |

## Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key (or Anthropic) - needed for Phase 2+

### Installation

```bash
cd axiom-core

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -e ".[dev]"
```

### Configuration

```bash
cp .env.example .env
# Edit .env and add your API keys (needed for Phase 2+)
```

### Run the API

```bash
uvicorn axiom.api.main:app --reload
```

Visit http://localhost:8000/docs for interactive API documentation.

### Available Endpoints (Current)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info |
| `/health` | GET | Health check |
| `/config/` | GET | Current configuration |
| `/query/` | POST | Query endpoint (not yet implemented) |

### Run Tests

```bash
pytest tests/ -v
```

## Project Structure

```
axiom-core/
├── src/axiom/
│   ├── api/              # FastAPI routes
│   │   ├── main.py       # App entry point
│   │   ├── health.py     # GET /health ✅
│   │   ├── config.py     # GET /config ✅
│   │   └── query.py      # POST /query (placeholder)
│   │
│   ├── config/           # Configuration
│   │   └── settings.py   # Pydantic settings ✅
│   │
│   ├── models/           # LLM abstraction (Phase 2)
│   │   ├── base.py       # Abstract BaseLLM
│   │   ├── types.py      # ModelResponse, etc.
│   │   ├── openai_models.py
│   │   └── anthropic_models.py
│   │
│   ├── vectorstore/      # Vector DB (Phase 3)
│   │   ├── base.py       # Abstract VectorStore
│   │   ├── chroma.py     # ChromaDB implementation
│   │   └── indexer.py    # Document chunking
│   │
│   ├── rag/              # RAG orchestration (Phase 4)
│   │   ├── engine.py     # QueryEngine
│   │   └── retrievers/   # Retrieval strategies
│   │
│   └── mcp/              # MCP client (Phase 4+)
│       └── manager.py    # MCPManager
│
└── tests/
    ├── unit/
    │   └── test_health.py ✅
    └── integration/
```

## Next Steps: Phase 2

Implement the Model Abstraction Layer:

1. **`models/types.py`** - Define `ModelResponse` dataclass
2. **`models/base.py`** - Abstract `BaseLLM` interface
3. **`models/openai_models.py`** - OpenAI integration with LangChain
4. **`models/anthropic_models.py`** - Anthropic integration
5. **Unit tests** for model implementations

Example target API:
```python
from axiom.models import OpenAIModel, AnthropicModel

# Easy model swapping
llm = OpenAIModel("gpt-4o-mini")
# llm = AnthropicModel("claude-3-5-haiku-20241022")

response = await llm.generate(
    prompt="Summarize this code:",
    context=["def hello(): print('world')"],
    temperature=0.0
)

print(f"Answer: {response.answer}")
print(f"Cost: ${response.cost_usd:.4f}")
print(f"Tokens: {response.token_count}")
```

## Related Projects

- [axiom-mcp-servers](https://github.com/deepanshu-malik/axiom-mcp-servers) - MCP server implementations (Filesystem server complete)
- [axiom-experiments](https://github.com/deepanshu-malik/axiom-experiments) - Model comparison & research notebooks

## License

MIT License - see [LICENSE](LICENSE) for details.
