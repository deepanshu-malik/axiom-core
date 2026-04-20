# Embeddings

Embeddings convert text into numerical vectors that capture semantic meaning. Similar text gets similar vectors — making semantic search possible.

---

## How Embeddings Enable Search

```
Query:  "user authentication logic"
         → embed → [0.23, -0.14, 0.87, ...]  (1536 dimensions)

Chunk A: "def verify_token(jwt: str) -> User:"
         → embed → [0.21, -0.12, 0.89, ...]  (similar!)

Chunk B: "def calculate_tax(amount: float) -> float:"
         → embed → [-0.31, 0.44, -0.12, ...]  (different)
```

Cosine similarity between query and chunk vectors tells ChromaDB which chunks are relevant — without any keyword matching.

---

## Embedding Models

### OpenAI `text-embedding-3-small` (Axiom default)

| Property | Value |
|----------|-------|
| Dimensions | 1536 |
| Cost | $0.02 per 1M tokens |
| Speed | Fast (API call) |
| Quality | High — strong on code and prose |

```bash
EMBEDDING_MODEL=text-embedding-3-small
```

Requires an OpenAI API key. Embeddings are computed once at indexing time and stored in ChromaDB — no ongoing cost at query time.

### OpenAI `text-embedding-3-large`

| Property | Value |
|----------|-------|
| Dimensions | 3072 |
| Cost | $0.13 per 1M tokens |
| Quality | Higher than small, diminishing returns for most use cases |

Use only if `text-embedding-3-small` isn't achieving sufficient retrieval quality.

### Sentence Transformers (local)

| Property | Value |
|----------|-------|
| Dimensions | 384–768 (model-dependent) |
| Cost | Free |
| Speed | Slower on CPU, fast on GPU |
| Quality | Lower than OpenAI, acceptable for most tasks |

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(chunks)
```

Available in `axiom-experiments` without an API key. Good for offline development.

---

## Comparison

| Model | Dimensions | Cost (index 1000 docs) | Retrieval quality |
|-------|-----------|------------------------|------------------|
| `text-embedding-3-small` | 1536 | ~$0.02 | ★★★★☆ |
| `text-embedding-3-large` | 3072 | ~$0.13 | ★★★★★ |
| `all-MiniLM-L6-v2` (local) | 384 | Free | ★★★☆☆ |
| `all-mpnet-base-v2` (local) | 768 | Free | ★★★★☆ |

For a typical Axiom workspace (~500 files, ~5000 chunks), `text-embedding-3-small` costs under $0.10 to index and provides strong retrieval quality.

---

## Important: Consistency

**The embedding model used at indexing time must match the one used at query time.**

ChromaDB stores vectors from one model. If you switch embedding models, you must delete the database and re-index:

```bash
rm -rf axiom-core/chroma_db/
python axiom-experiments/scripts/index_documents.py ~/axiom
```

This is why the embedding model is a first-class configuration setting:

```bash
EMBEDDING_MODEL=text-embedding-3-small   # in .env
```

---

## Experimenting with Embeddings

Run `axiom-experiments/notebooks/02_embedding_comparison.ipynb` to:

- Index the same documents with OpenAI and local models
- Run test queries and compare retrieved chunk relevance
- Measure embedding speed and cost per document
- Choose the best model for your use case before building the production system

---

→ **Next:** [Retrieval Strategies](retrieval.md)

**Related:** [Chunking Strategies](chunking.md) · [RAG Pipeline](pipeline.md) · [Experiments Notebooks](../experiments/notebooks.md)
