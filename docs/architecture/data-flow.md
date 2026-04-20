# Data Flow

How a user query travels through Axiom from input to final answer.

---

## The Full Request Lifecycle

```
User Query: "How is authentication implemented in my projects?"

Step 1 — API receives query
    POST /query  {"query": "...", "model": "gpt-4o-mini", "top_k": 5}

Step 2 — QueryEngine.query()
    ├── Route to retriever (hybrid by default)
    └── Start timer

Step 3 — Retrieval
    ├── Semantic search: embed query → cosine similarity in ChromaDB
    ├── Keyword search:  tokenize query → BM25 score over all docs
    ├── Merge scores:    0.7 × semantic + 0.3 × BM25
    └── Return top-5 chunks with metadata

Step 4 — Prompt building
    ├── Format retrieved chunks as "Document 1: ...", "Document 2: ..."
    └── Wrap with RAG prompt template

Step 5 — LLM call
    ├── Send prompt + context to selected model
    ├── Track: tokens_in, tokens_out, latency
    └── Calculate cost_usd

Step 6 — Response assembly
    ├── answer: model output
    ├── sources: chunk content + file path + similarity score
    ├── model_used: "gpt-4o-mini"
    ├── total_time: 1.42s
    └── cost_usd: $0.0003

Step 7 — Return to user
    HTTP 200 with QueryResponse JSON
```

---

## Sequence Diagram

```
Client          FastAPI         QueryEngine      Retriever       ChromaDB        LLM
  │                │                 │               │               │             │
  │─── POST /query ─►               │               │               │             │
  │                │─── query() ────►               │               │             │
  │                │                │─── retrieve() ►               │             │
  │                │                │               │─── embed() ──►│             │
  │                │                │               │◄── vectors ───│             │
  │                │                │               │─── search() ─►│             │
  │                │                │               │◄── chunks ────│             │
  │                │                │               │─── bm25() ────(in memory)   │
  │                │                │◄── results ───│               │             │
  │                │                │─── build_prompt()             │             │
  │                │                │─── generate() ─────────────────────────────►│
  │                │                │◄── ModelResponse ──────────────────────────│
  │                │◄── QueryResponse               │               │             │
  │◄── JSON 200 ───│                │               │               │             │
```

---

## Document Indexing Flow

Before queries can work, documents must be indexed. This is a separate one-time (or periodic) operation:

```
Source Files (via MCP or direct)
        │
        ▼
DocumentIndexer.chunk_file()
  ├── Read file content
  ├── Split into overlapping chunks (RecursiveCharacterTextSplitter)
  │     chunk_size=1000, chunk_overlap=200
  └── Attach metadata: source path, file name, chunk_id, total_chunks
        │
        ▼
Embedding model (OpenAI text-embedding-3-small or local)
  └── Convert each chunk text → float vector (1536 dims for OpenAI small)
        │
        ▼
ChromaDB.add_documents()
  └── Store: [vector, text, metadata] for each chunk
```

**Indexing is decoupled from querying.** You can re-index anytime without restarting the API.

---

## Retrieval Strategies — How Scores Are Combined

### Semantic only
```
score = cosine_similarity(query_vector, chunk_vector)
```

### Hybrid (default)
```
final_score = 0.7 × semantic_score + 0.3 × bm25_score
```
The `alpha` parameter (default 0.7) controls the balance. Higher alpha = more weight on semantic similarity, lower alpha = more weight on keyword matching.

### Keyword only (BM25)
```
score = BM25Okapi(tokenized_query, tokenized_corpus)
```
Best for exact term matching (function names, error codes, specific identifiers).

---

## MCP Integration in the Data Flow

When `axiom-core` uses MCP servers to fetch fresh content at query time (Phase 4+):

```
QueryEngine.query()
        │
        ├── (standard) retrieve from ChromaDB (pre-indexed)
        │
        └── (optional) fetch live content via MCP
                │
                ├── MCPManager.call_tool("read_file", {path})
                │       → FilesystemMCPServer (stdio)
                │       ← file contents
                │
                └── Inject into context alongside indexed chunks
```

This lets Axiom answer questions about files that haven't been indexed yet, or get fresh content for recently modified files.

---

## Cost Tracking

Every query produces a cost breakdown:

```python
ModelResponse(
    answer="...",
    model_name="gpt-4o-mini",
    token_count=387,          # input + output tokens
    latency_seconds=0.84,
    cost_usd=0.000232,        # calculated from token count × per-token price
    metadata={"input_tokens": 312, "output_tokens": 75}
)
```

Cost rates are hardcoded per model in each provider's `estimate_cost()` implementation and surfaced in the `/query` response.

---

## Error Handling

| Failure Point | Behaviour |
|---------------|-----------|
| Query with empty ChromaDB | Returns 0 results, LLM answers from training data only |
| LLM API timeout | `tenacity` retries with exponential backoff (3 attempts) |
| MCP server down | MCPManager logs error, continues with indexed data |
| File outside allowed dirs | Filesystem server raises `ValueError("Access denied")` |
| Unsupported file extension | `read_file` raises `ValueError("Unsupported file type")` |

---

→ **Next:** [MCP Overview](../mcp/overview.md)

**Related:** [Architecture Overview](overview.md) · [RAG Pipeline](../rag/pipeline.md) · [Retrieval Strategies](../rag/retrieval.md)
