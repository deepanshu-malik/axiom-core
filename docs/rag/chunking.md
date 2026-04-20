# Chunking Strategies

Chunking splits documents into pieces small enough to fit in a prompt, while preserving enough context to be useful. The strategy you choose directly affects retrieval quality.

---

## Why Not Just Use the Whole File?

A typical Python file is 5–500KB. An LLM context window is ~128K tokens (~100K words). You could fit many files — but:

1. **Cost** — more tokens = higher cost per query
2. **Noise** — LLMs perform worse when the relevant passage is buried in irrelevant text
3. **Precision** — a 200-token chunk about authentication retrieves better than a 2000-line file

The goal is chunks large enough to be self-contained, but small enough to be precise.

---

## Strategies

### 1. Fixed-size chunking

Split every N characters regardless of content structure.

```python
chunks = [text[i:i+1000] for i in range(0, len(text), 800)]
# 1000-char chunks with 200-char overlap
```

**Pros:** Simple, predictable, fast
**Cons:** Splits mid-sentence, mid-function, mid-paragraph — context breaks

---

### 2. Recursive character splitting (Axiom default)

Split on a priority list of separators: `\n\n` → `\n` → `. ` → ` ` → `""`. This tries to preserve natural text boundaries.

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", ". ", " ", ""]
)
chunks = splitter.split_text(text)
```

**Pros:** Respects paragraph/sentence boundaries better than fixed-size
**Cons:** Chunk sizes vary; doesn't understand code structure

---

### 3. Code-aware chunking

Split on code structure: class definitions, function definitions, imports.

```python
from langchain.text_splitter import PythonCodeTextSplitter

splitter = PythonCodeTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_text(python_source)
```

**Pros:** Each chunk is a complete function or class — semantically coherent
**Cons:** Only works for supported languages; some functions are very long

---

### 4. Semantic chunking (advanced)

Split at points where the topic changes, detected by embedding similarity between adjacent sentences.

```python
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings

splitter = SemanticChunker(OpenAIEmbeddings())
chunks = splitter.create_documents([text])
```

**Pros:** Chunks are thematically coherent — best retrieval quality
**Cons:** Requires an embedding model at indexing time; slower; more expensive

---

## Axiom's Default: Recursive + 1000/200

```python
# axiom-core/src/axiom/vectorstore/indexer.py (planned)
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", ". ", " ", ""]
)
```

**Why 1000/200?**
- 1000 characters ≈ 200–250 tokens — fits many chunks in a single prompt
- 200-char overlap ensures boundary content isn't lost between chunks
- Recursive splitting respects paragraph structure for most file types

These values are configurable via `.env`:

```bash
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

---

## Chunk Metadata

Every chunk carries metadata identifying its origin:

```python
Document(
    content="def authenticate(token: str) -> User:\n    ...",
    metadata={
        "source": "/home/user/axiom/axiom-core/src/axiom/api/auth.py",
        "file_name": "auth.py",
        "file_type": ".py",
        "chunk_id": 3,
        "total_chunks": 12,
    }
)
```

This metadata is returned in the `/query` response as `sources`, so the user knows exactly which file and chunk produced each piece of the answer.

---

## Experimenting with Chunking

Run `axiom-experiments/notebooks/03_chunking_experiments.ipynb` to compare strategies on your own files:

- Index the same document with each strategy
- Run 10 test queries
- Measure which strategy retrieves the most relevant chunks (by manual inspection + cosine similarity)

The notebook outputs a comparison table showing chunk count, average chunk size, and retrieval hit rate for each strategy.

---

→ **Next:** [Embeddings](embeddings.md)

**Related:** [RAG Overview](overview.md) · [Retrieval Strategies](retrieval.md) · [Experiments Notebooks](../experiments/notebooks.md)
