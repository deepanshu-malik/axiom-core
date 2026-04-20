# RAG Pipeline

The `QueryEngine` is the orchestrator that ties retrieval, prompt building, and LLM generation into a single cohesive pipeline.

---

## The `QueryEngine` Class

**File:** `axiom-core/src/axiom/rag/engine.py` (planned)

```python
from dataclasses import dataclass
from axiom.models.base import BaseLLM, ModelResponse
from axiom.vectorstore.base import VectorStore
from axiom.rag.retrievers.hybrid import HybridRetriever

@dataclass
class QueryResponse:
    """Everything returned to the user from a single query."""
    answer: str
    sources: list[SearchResult]
    model_response: ModelResponse
    retrieval_time: float
    total_time: float

class QueryEngine:
    def __init__(
        self,
        llm: BaseLLM,
        vectorstore: VectorStore,
        retriever_type: str = "hybrid",   # "semantic" | "hybrid" | "keyword"
        top_k: int = 5,
        use_reranking: bool = False,
    ):
        self.llm = llm
        self.vectorstore = vectorstore
        self.top_k = top_k

        if retriever_type == "hybrid":
            self.retriever = HybridRetriever(vectorstore, alpha=0.7)
        elif retriever_type == "semantic":
            self.retriever = SemanticRetriever(vectorstore)
        else:
            self.retriever = KeywordRetriever(vectorstore)

    async def query(self, query: str) -> QueryResponse:
        import time
        start = time.time()

        # Step 1: Retrieve
        t0 = time.time()
        results = await self.retriever.retrieve(query, k=self.top_k)
        retrieval_time = time.time() - t0

        # Step 2: Build prompt
        context = [r.document.content for r in results]
        prompt = self._build_prompt(query, context)

        # Step 3: Generate
        model_response = await self.llm.generate(prompt, context)

        return QueryResponse(
            answer=model_response.answer,
            sources=results,
            model_response=model_response,
            retrieval_time=retrieval_time,
            total_time=time.time() - start,
        )
```

---

## Prompt Construction

The RAG prompt template wraps retrieved chunks with clear labels so the LLM knows what is evidence and what is the question:

```python
def _build_prompt(self, query: str, context: list[str]) -> str:
    context_str = "\n\n".join([
        f"Document {i+1}:\n{doc}"
        for i, doc in enumerate(context)
    ])

    return f"""You are a helpful assistant answering questions about a codebase and documents.
Use only the provided context to answer. If the answer is not in the context, say so.
Always cite which document(s) you used.

Context:
{context_str}

Question: {query}

Answer:"""
```

**Why this template works:**
- "Use only the provided context" — prevents hallucination from training data
- "If the answer is not in the context, say so" — honest non-answers beat wrong answers
- "Always cite which document(s)" — forces traceability

---

## Source Citations in the Response

The `QueryResponse.sources` field returns the retrieved chunks alongside the answer:

```json
{
  "answer": "Authentication uses JWT tokens validated in middleware.py...",
  "sources": [
    {
      "content": "def verify_token(token: str) -> User:\n    payload = jwt.decode...",
      "source": "/home/user/axiom/axiom-core/src/axiom/api/auth.py",
      "score": 0.94
    },
    {
      "content": "class AuthMiddleware:\n    async def __call__(self, request...",
      "source": "/home/user/axiom/axiom-core/src/axiom/api/middleware.py",
      "score": 0.87
    }
  ],
  "model_used": "gpt-4o-mini",
  "total_time": 1.42,
  "cost_usd": 0.000232
}
```

The `score` is the combined retrieval score (higher = more relevant).

---

## Context Window Management

With `TOP_K=5` and `CHUNK_SIZE=1000`:
- 5 chunks × ~1000 chars ≈ 5000 characters ≈ ~1250 tokens of context
- Plus prompt template: ~100 tokens
- Plus query: ~20 tokens
- **Total input: ~1370 tokens** — well within any model's context window

For large codebases, increase `TOP_K` carefully. At `TOP_K=20`, input tokens reach ~5000–6000, costing more and potentially diluting the most relevant content.

---

## Full End-to-End Example

```python
from axiom.models.router import get_llm
from axiom.vectorstore.chroma import ChromaVectorStore
from axiom.rag.engine import QueryEngine

async def main():
    llm = get_llm()                               # from settings.py
    store = ChromaVectorStore()                   # connects to chroma_db/
    engine = QueryEngine(llm=llm, vectorstore=store)

    response = await engine.query(
        "How is error handling implemented across the API?"
    )

    print(f"Answer: {response.answer}")
    print(f"\nSources ({len(response.sources)}):")
    for src in response.sources:
        print(f"  • {src.document.metadata['source']} (score: {src.score:.2f})")
    print(f"\nCost: ${response.model_response.cost_usd:.4f}")
    print(f"Time: {response.total_time:.2f}s")
```

---

## Running the Full Pipeline in Experiments

Before building the production `QueryEngine`, validate it in `axiom-experiments/notebooks/05_rag_pipeline.ipynb`:

- Index a small set of test documents
- Run 10–20 test queries
- Inspect retrieved chunks and answer quality
- Tune `TOP_K`, `CHUNK_SIZE`, and `alpha`
- Measure cost per query

Only then implement the production version in `axiom-core`.

---

→ **Next:** [API Overview](../api/overview.md)

**Related:** [Retrieval Strategies](retrieval.md) · [Chunking Strategies](chunking.md) · [Data Flow](../architecture/data-flow.md) · [axiom-core RAG Engine Docs](../rag-engine.md)
