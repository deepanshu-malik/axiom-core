# Endpoints

Full reference for all `axiom-core` HTTP endpoints.

Base URL: `http://localhost:8000`

---

## `GET /`

Root endpoint. Returns basic API information.

**Response:**
```json
{
  "message": "Axiom API",
  "version": "0.1.0",
  "docs": "/docs"
}
```

---

## `GET /health`

Health check. Returns immediately — no database or LLM calls.

**Response `200`:**
```json
{
  "status": "healthy",
  "service": "axiom-core"
}
```

Use this for:
- Load balancer health checks
- Docker/Kubernetes readiness probes
- Verifying the server started correctly

```bash
curl http://localhost:8000/health
```

---

## `GET /config`

Returns the current active configuration. API keys are **never** included.

**Response `200`:**
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
  "collection_name": "axiom_knowledge"
}
```

Use this to verify your `.env` settings were loaded correctly:

```bash
curl http://localhost:8000/config | jq .llm_model
```

---

## `POST /query`

> **Status: 🔲 Returns 501 — Implemented in Phase 4**

Query your personal knowledge base. Runs the full RAG pipeline and returns an answer with sources, model metadata, and cost.

**Request body:**
```json
{
  "query": "How is authentication implemented in my projects?",
  "top_k": 5,
  "model": "gpt-4o-mini"
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `query` | string | ✅ | — | The natural language question |
| `top_k` | integer | ❌ | `5` | Number of chunks to retrieve |
| `model` | string | ❌ | From `.env` | Override the LLM for this request |

**Response `200`:**
```json
{
  "answer": "Authentication in your codebase uses JWT tokens. The main logic is in auth.py, where verify_token() decodes the JWT using the RS256 algorithm...",
  "sources": [
    {
      "content": "def verify_token(token: str) -> User:\n    payload = jwt.decode(token, SECRET_KEY, algorithms=['RS256'])...",
      "source": "/home/user/axiom/axiom-core/src/axiom/api/auth.py",
      "score": 0.94
    },
    {
      "content": "class AuthMiddleware:\n    async def __call__(self, request: Request, call_next)...",
      "source": "/home/user/axiom/axiom-core/src/axiom/api/middleware.py",
      "score": 0.87
    }
  ],
  "model_used": "gpt-4o-mini",
  "total_time": 1.42,
  "cost_usd": 0.000232
}
```

| Field | Type | Description |
|-------|------|-------------|
| `answer` | string | The LLM's answer, grounded in retrieved sources |
| `sources` | array | Retrieved chunks with file path and similarity score |
| `sources[].content` | string | The chunk text (truncated to 200 chars in response) |
| `sources[].source` | string | Absolute path to the source file |
| `sources[].score` | float | Retrieval score (0–1, higher = more relevant) |
| `model_used` | string | The model that generated the answer |
| `total_time` | float | Wall-clock seconds for the full request |
| `cost_usd` | float | Estimated cost in USD |

**Response `501`** (current — Phase 4 not yet implemented):
```json
{
  "detail": "Query endpoint not yet implemented. Coming in Phase 4."
}
```

**Response `500`** (after Phase 4, on error):
```json
{
  "detail": "ChromaDB collection is empty. Run the indexing script first."
}
```

---

## Error Responses

All endpoints follow the FastAPI default error format:

```json
{
  "detail": "Human-readable error message"
}
```

| Status | When |
|--------|------|
| `422` | Request body fails validation (wrong types, missing required fields) |
| `500` | Internal error (LLM API failure, empty vector store, etc.) |
| `501` | Endpoint not yet implemented |

---

## Example: Full Query via curl

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What MCP tools does the filesystem server expose?",
    "top_k": 3,
    "model": "gpt-4o-mini"
  }' | jq .
```

---

## Example: Switch Model Per-Request

```bash
# Compare two models on the same query:

curl -s -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain the RAG pipeline", "model": "gpt-4o-mini"}' \
  | jq '{model: .model_used, cost: .cost_usd, time: .total_time}'

curl -s -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain the RAG pipeline", "model": "claude-3-5-haiku-20241022"}' \
  | jq '{model: .model_used, cost: .cost_usd, time: .total_time}'
```

---

→ **Next:** [Experiments Overview](../experiments/overview.md)

**Related:** [API Overview](overview.md) · [RAG Pipeline](../rag/pipeline.md) · [axiom-core API Reference](api-reference.md)
