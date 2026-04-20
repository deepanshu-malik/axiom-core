# API Reference — Implementation Reference

> **Status: ✅ Working**

Operational guide for `axiom-core/src/axiom/api/`.

For endpoint design and request/response schemas, see [Endpoints Reference](api/endpoints.md).

---

## Module Layout

```
src/axiom/api/
├── __init__.py
├── main.py      ← FastAPI app, router registration
├── health.py    ← GET /health
├── config.py    ← GET /config
└── query.py     ← POST /query (Phase 4)
```

---

## `main.py` — Application Entry Point

```python
from fastapi import FastAPI
from axiom import __version__
from axiom.api import config, health, query

app = FastAPI(
    title="Axiom API",
    version=__version__,
    description="MCP-enabled personal knowledge assistant",
)

app.include_router(health.router)
app.include_router(config.router)
app.include_router(query.router)

@app.get("/")
async def root() -> dict:
    return {"message": "Axiom API", "version": __version__, "docs": "/docs"}
```

**How to start:**

```bash
cd axiom-core
source .venv/bin/activate
uvicorn axiom.api.main:app --reload
```

Interactive docs: `http://localhost:8000/docs`

---

## `health.py` — Health Check

**Route:** `GET /health`
**Auth:** None
**Status:** ✅ Implemented

```python
@router.get("/health")
async def health_check() -> dict:
    return {"status": "healthy", "service": "axiom-core"}
```

**Response:**

```json
{ "status": "healthy", "service": "axiom-core" }
```

Use this route to confirm the server is up before making other requests. Suitable as a liveness probe in Docker/k8s.

---

## `config.py` — Configuration View

**Route:** `GET /config`
**Auth:** None
**Status:** ✅ Implemented

Returns current runtime configuration — all fields sourced from `axiom.config.settings`. Sensitive values (API keys) are never included.

**Response:**

```json
{
  "llm_provider": "openai",
  "llm_model": "gpt-4o-mini",
  "embedding_model": "text-embedding-3-small",
  "retriever_strategy": "hybrid",
  "chunk_size": 1000,
  "chunk_overlap": 200,
  "top_k": 5,
  "rerank": false,
  "temperature": 0.0,
  "max_tokens": 1000,
  "collection_name": "axiom"
}
```

All these values can be changed via `.env` without touching code. See [Configuration](getting-started/installation.md#configuration-reference).

---

## `query.py` — RAG Query

**Route:** `POST /query/`
**Auth:** None
**Status:** 🔲 Stub — returns 501 until Phase 4

### Request

```json
{
  "query": "How does the hybrid retriever work?",
  "top_k": 5,
  "model": "gpt-4o"
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | `str` | required | Natural language question |
| `top_k` | `int` | `5` | Number of source documents to retrieve |
| `model` | `str \| null` | `null` | Override the default LLM for this request |

### Response (Phase 4)

```json
{
  "answer": "The hybrid retriever combines...",
  "sources": [
    {
      "content": "...",
      "metadata": { "source": "path/to/file.md", "chunk_id": 3 },
      "score": 0.91,
      "rank": 0
    }
  ],
  "model_used": "gpt-4o-mini",
  "total_time": 1.42,
  "cost_usd": 0.00031
}
```

### Current stub behaviour

```python
raise HTTPException(
    status_code=501,
    detail="Query endpoint not yet implemented. Coming in Phase 4.",
)
```

**Phase 4 wiring** is described in [RAG Engine — Wiring /query](rag-engine.md#wiring-query-in-phase-4).

---

## Adding a New Route

1. Create `src/axiom/api/my_route.py` with an `APIRouter`.
2. Define Pydantic request/response models in the same file.
3. Register in `main.py`:

```python
from axiom.api import my_route
app.include_router(my_route.router)
```

4. Add the endpoint to [Endpoints Reference](api/endpoints.md).

---

## Tests

```bash
cd axiom-core
pytest tests/ -v -k "api"
```

Integration tests hit the real FastAPI app using `httpx.AsyncClient`:

```python
from httpx import AsyncClient, ASGITransport
from axiom.api.main import app

@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"
```

---

## Related Docs

- [API Overview](api/overview.md)
- [Endpoints Reference](api/endpoints.md)
- [RAG Engine](rag-engine.md) — Phase 4 wiring of `/query`
- [axiom-core index](index.md)
