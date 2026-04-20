# Retrieval Strategies

Retrieval is how Axiom finds relevant document chunks given a user query. The strategy you choose affects both recall (finding the right content) and precision (not returning irrelevant content).

---

## Three Strategies

### 1. Semantic Retrieval

Embeds the query and finds chunks with the most similar vectors using cosine similarity.

```python
# axiom-core/src/axiom/rag/retrievers/semantic.py (planned)
class SemanticRetriever:
    async def retrieve(self, query: str, k: int = 5) -> list[SearchResult]:
        return await self.vectorstore.search(query, k=k)
```

**Best for:** Natural language questions, paraphrased queries, conceptual searches
**Weakness:** Struggles with exact identifiers, error codes, function names

**Example where it works well:**
> "How does the app handle user sessions?" → finds session management code even if it uses words like `token`, `cache`, `persistence`

**Example where it fails:**
> "Find usages of `authenticate_jwt_rs256`" → may not find exact matches if the function name isn't represented well in the embedding space

---

### 2. Keyword Search (BM25)

Uses BM25 (Best Match 25), a classic information retrieval algorithm. Scores chunks based on term frequency and inverse document frequency.

```python
# axiom-core/src/axiom/rag/retrievers/keyword.py (planned)
from rank_bm25 import BM25Okapi

class KeywordRetriever:
    def build_index(self, documents: list[Document]):
        tokenized = [doc.content.split() for doc in documents]
        self.bm25 = BM25Okapi(tokenized)
        self.docs = documents

    async def retrieve(self, query: str, k: int = 5) -> list[SearchResult]:
        scores = self.bm25.get_scores(query.split())
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        return [SearchResult(self.docs[i], scores[i], rank) for rank, i in enumerate(top_indices)]
```

**Best for:** Exact term matching — function names, class names, error codes, identifiers
**Weakness:** Misses paraphrases and semantic equivalents

**Example where it works well:**
> "Find authenticate_jwt_rs256" → exact keyword match wins

**Example where it fails:**
> "How does the login flow work?" → doesn't know that `authenticate` relates to "login"

---

### 3. Hybrid Retrieval (Axiom default)

Combines semantic and keyword scores with a weighted sum:

```
final_score = α × semantic_score + (1 - α) × bm25_score
```

Where `α = 0.7` (70% semantic, 30% keyword) by default.

```python
# axiom-core/src/axiom/rag/retrievers/hybrid.py (planned)
class HybridRetriever:
    def __init__(self, vectorstore: VectorStore, alpha: float = 0.7):
        self.vectorstore = vectorstore
        self.alpha = alpha

    async def retrieve(self, query: str, k: int = 5) -> list[SearchResult]:
        # Get semantic candidates (2× to allow for re-scoring)
        semantic = await self.vectorstore.search(query, k=k * 2)

        # Get BM25 scores for all docs
        bm25_scores = self.bm25.get_scores(query.split())

        # Merge scores
        scores = {}
        for result in semantic:
            doc_id = result.document.metadata["id"]
            scores[doc_id] = self.alpha * result.score

        for idx, score in enumerate(bm25_scores):
            doc_id = self.docs[idx].metadata["id"]
            scores[doc_id] = scores.get(doc_id, 0) + (1 - self.alpha) * score

        # Return top-k
        top_ids = sorted(scores, key=scores.get, reverse=True)[:k]
        ...
```

**Best for:** General-purpose retrieval on mixed content (natural language + code)
**Why it wins:** Handles both "explain the login flow" (semantic) and "find jwt_secret usage" (keyword) in the same system

---

## Choosing Alpha

| Alpha | Effect |
|-------|--------|
| `1.0` | Pure semantic — equivalent to `SemanticRetriever` |
| `0.7` | Default — semantic-dominant, keyword augmented |
| `0.5` | Equal weight — good for balanced content |
| `0.0` | Pure keyword — equivalent to `KeywordRetriever` |

For a codebase-heavy knowledge base, `alpha = 0.6–0.7` tends to work best. For prose-heavy documents, `alpha = 0.8+` is better.

Configure via:
```bash
# No direct alpha setting in .env yet — set in QueryEngine construction
# Default is 0.7
```

---

## Optional: Reranking

After retrieval, a reranker re-scores the top-K chunks using a more powerful (but slower) model. Axiom supports Cohere Rerank as an optional step:

```python
# axiom-core/src/axiom/rag/rerankers/cohere.py (planned)
import cohere

class CohereReranker:
    async def rerank(
        self, query: str, results: list[SearchResult], top_n: int = 5
    ) -> list[SearchResult]:
        response = self.client.rerank(
            query=query,
            documents=[r.document.content for r in results],
            top_n=top_n,
            model="rerank-english-v3.0",
        )
        ...
```

Enable via:
```bash
RERANK=true
# Requires COHERE_API_KEY in .env
```

Reranking adds ~200–400ms latency but often improves the top-3 results meaningfully. Run `axiom-experiments/notebooks/04_retrieval_strategies.ipynb` to measure the impact on your content.

---

## Retrieval Configuration

```bash
RETRIEVER_STRATEGY=hybrid    # semantic | hybrid | keyword
TOP_K=5                      # Number of chunks to retrieve
RERANK=false                 # Enable Cohere reranking
```

---

→ **Next:** [RAG Pipeline](pipeline.md)

**Related:** [Chunking Strategies](chunking.md) · [Embeddings](embeddings.md) · [Experiments Notebooks](../experiments/notebooks.md)
