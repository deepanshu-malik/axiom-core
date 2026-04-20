# API Overview

`axiom-core` exposes a FastAPI HTTP API that serves as the main entry point into the Axiom system.

---

## Application Structure

```
axiom-core/src/axiom/
├── api/
│   ├── main.py        ← FastAPI app, router registration
│   ├── health.py      ← GET /health
│   ├── config.py      ← GET /config
│   └── query.py       ← POST /query  (Phase 4)
└── config/
    └── settings.py    ← Pydantic Settings (env vars)
```

---

## Starting the Server

```bash
cd ~/axiom/axiom-core
source .venv/bin/activate

# Development (auto-reload on file changes)
uvicorn axiom.api.main:app --reload --port 8000

# Production
uvicorn axiom.api.main:app --host 0.0.0.0 --port 8000 --workers 1
```

---

## Interactive API Docs

FastAPI automatically generates two interactive UIs:

| UI | URL | Best for |
|----|-----|----------|
| Swagger UI | [http://localhost:8000/docs](http://localhost:8000/docs) | Testing endpoints interactively |
| ReDoc | [http://localhost:8000/redoc](http://localhost:8000/redoc) | Reading the full schema |

---

## Configuration

All runtime configuration is loaded from environment variables via Pydantic Settings:

**File:** `axiom-core/src/axiom/config/settings.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Keys
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    github_token: str | None = None

    # Model Selection
    llm_provider: ModelProvider = ModelProvider.OPENAI
    llm_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"

    # RAG Configuration
    retriever_strategy: RetrieverStrategy = RetrieverStrategy.HYBRID
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k: int = 5
    rerank: bool = False

    # Model Parameters
    temperature: float = 0.0
    max_tokens: int = 1000

    # Vector Store
    chroma_persist_dir: str = "./chroma_db"
    collection_name: str = "axiom_knowledge"

    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    class Config:
        env_file = ".env"

settings = Settings()   # global singleton
```

**Access from anywhere in the codebase:**
```python
from axiom.config import settings
print(settings.llm_model)
```

---

## Router Structure

`main.py` registers three routers:

```python
from fastapi import FastAPI
from axiom.api import health, config, query

app = FastAPI(
    title="Axiom API",
    version="0.1.0",
    description="MCP-enabled personal knowledge assistant",
)

app.include_router(health.router)           # GET /health
app.include_router(config.router)           # GET /config
app.include_router(query.router)            # POST /query
```

Each router is its own module. Adding new endpoints = adding a new module and registering its router in `main.py`.

---

## CORS and Middleware

For local development, no CORS configuration is needed. When adding a frontend (Phase 3+), add:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Streamlit/React dev server
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

---

## Dependency Injection

FastAPI's `Depends` system is used to inject shared resources (the `QueryEngine` instance, database connections) into route handlers without global state:

```python
# Planned pattern for Phase 4
from functools import lru_cache
from axiom.rag.engine import QueryEngine

@lru_cache
def get_query_engine() -> QueryEngine:
    llm = get_llm()
    store = ChromaVectorStore()
    return QueryEngine(llm=llm, vectorstore=store)

@router.post("/")
async def query_knowledge(
    request: QueryRequest,
    engine: QueryEngine = Depends(get_query_engine),
) -> QueryResponse:
    return await engine.query(request.query)
```

---

→ **Next:** [Endpoints](endpoints.md)

**Related:** [Data Flow](../architecture/data-flow.md) · [RAG Pipeline](../rag/pipeline.md) · [axiom-core API Reference](api-reference.md)
