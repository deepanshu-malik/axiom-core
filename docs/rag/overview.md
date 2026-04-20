# RAG Overview

RAG (Retrieval-Augmented Generation) is the core technique that makes Axiom useful. Instead of asking an LLM to answer from its training data alone, RAG first retrieves relevant passages from your actual files, then asks the LLM to answer using that evidence.

---

## The Problem with Plain LLMs

```
You: "How is authentication implemented in my projects?"
GPT-4: "Authentication is typically implemented using JWT tokens..."
```

The LLM answers from its training data — generic, not specific to your codebase. It can't answer questions about private code it has never seen.

---

## How RAG Fixes This

```
You: "How is authentication implemented in my projects?"

Axiom:
  1. Searches your indexed files for "authentication"
  2. Retrieves: auth.py, middleware.py, jwt_utils.py (top 5 relevant chunks)
  3. Asks the LLM: "Given these files, how is authentication implemented?"

GPT-4: "In your codebase, authentication uses JWT tokens defined in
        jwt_utils.py. The middleware at middleware.py validates tokens
        on every request by calling verify_token()..."
```

The answer is grounded in your actual code — specific, accurate, and citable.

---

## RAG Architecture in Axiom

```
Documents (files)
       │
       ▼
  Chunking              Split long files into overlapping chunks
       │
       ▼
  Embeddings            Convert each chunk to a vector
       │
       ▼
  Vector Store          Store chunks + vectors in ChromaDB
       │
       │          ← at query time ─────────────────────
       ▼
  Retrieval             Find top-K chunks similar to the query
       │
       ▼
  Reranking (optional)  Reorder chunks by relevance
       │
       ▼
  Prompt Building       Format chunks + query into LLM prompt
       │
       ▼
  LLM Generation        LLM reads context and writes answer
       │
       ▼
  Response              Answer + source citations + cost
```

---

## Axiom's RAG Choices

| Component | Axiom's choice | Alternatives |
|-----------|---------------|--------------|
| Chunking | Recursive character splitter | Fixed-size, semantic |
| Embeddings | OpenAI text-embedding-3-small | Local sentence-transformers |
| Vector store | ChromaDB (local, embedded) | Pinecone, Weaviate, Qdrant |
| Retrieval | Hybrid (semantic + BM25) | Semantic only, keyword only |
| Reranking | None (optional Cohere) | Cross-encoders |
| LLM | Configurable (OpenAI default) | Any provider |

These defaults were chosen based on the experiments in `axiom-experiments`. The key tradeoffs are covered in the following docs.

---

## The Indexing Pipeline (One-time)

```bash
# Index your files before querying
python axiom-experiments/scripts/index_documents.py ~/axiom
```

This reads all supported files in `~/axiom`, chunks them, embeds them, and stores them in `chroma_db/`. You only need to re-run this when files change significantly.

---

## The Query Pipeline (Per-request)

Every call to `POST /query` runs this sequence:

1. **Retrieve** — top-5 chunks most relevant to the query
2. **Build prompt** — assemble retrieved chunks + query into a RAG prompt
3. **Generate** — send to LLM, get answer + token usage
4. **Return** — answer + source file paths + cost + latency

The full implementation lives in `axiom-core/src/axiom/rag/engine.py`.

---

## Key Concepts

### Why chunking matters
LLMs have context limits. A 10,000-line file doesn't fit in one prompt. Chunking breaks it into overlapping pieces so nothing is lost, and retrieval finds the most relevant piece rather than dumping the whole file.

### Why embeddings matter
Embeddings convert text to numbers that capture semantic meaning. "authenticate user" and "login validation" become similar vectors even without shared words — so retrieval finds conceptually relevant content, not just keyword matches.

### Why hybrid retrieval beats pure semantic
Semantic search misses exact terms (function names, error codes, identifiers). BM25 misses paraphrases. Hybrid search combines both at a 70/30 ratio and beats either alone on real codebases.

---

→ **Next:** [Chunking Strategies](chunking.md)

**Related:** [Retrieval Strategies](retrieval.md) · [RAG Pipeline](pipeline.md) · [Data Flow](../architecture/data-flow.md)
