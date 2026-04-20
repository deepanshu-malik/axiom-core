# Vector Store — Implementation Reference

> **Status: 🔲 Phase 3**

Implementation guide for `axiom-core/src/axiom/vectorstore/`.

For concepts, see [Embeddings](rag/embeddings.md) and [Chunking Strategies](rag/chunking.md).

---

## Module Layout

```
src/axiom/vectorstore/
├── __init__.py        ← exports: VectorStore, Document, SearchResult, ChromaVectorStore
├── base.py            ← abstract interfaces
├── chroma.py          ← ChromaDB implementation
└── indexer.py         ← DocumentIndexer (chunking + metadata)
```

---

## `base.py` — Interfaces

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

@dataclass
class Document:
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None

@dataclass
class SearchResult:
    document: Document
    score: float
    rank: int

class VectorStore(ABC):
    @abstractmethod
    async def add_documents(self, documents: list[Document]) -> None: ...

    @abstractmethod
    async def search(
        self,
        query: str,
        k: int = 5,
        filter: dict[str, Any] | None = None,
    ) -> list[SearchResult]: ...

    @abstractmethod
    async def get_all(self) -> list[Document]: ...

    @abstractmethod
    async def delete(self, filter: dict[str, Any]) -> int: ...

    @abstractmethod
    async def count(self) -> int: ...
```

---

## `chroma.py` — ChromaDB Implementation

```python
import chromadb
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings
from axiom.config import settings
from .base import VectorStore, Document, SearchResult

class ChromaVectorStore(VectorStore):
    def __init__(
        self,
        collection_name: str | None = None,
        persist_directory: str | None = None,
    ):
        collection_name = collection_name or settings.collection_name
        persist_directory = persist_directory or settings.chroma_persist_dir

        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        self.embeddings = OpenAIEmbeddings(model=settings.embedding_model)

    async def add_documents(self, documents: list[Document]) -> None:
        if not documents:
            return

        texts = [doc.content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        ids = [f"{doc.metadata.get('source', 'doc')}_{i}" for i, doc in enumerate(documents)]

        # Generate embeddings via OpenAI
        vectors = await self.embeddings.aembed_documents(texts)

        self.collection.add(
            documents=texts,
            embeddings=vectors,
            metadatas=metadatas,
            ids=ids,
        )

    async def search(
        self,
        query: str,
        k: int = 5,
        filter: dict | None = None,
    ) -> list[SearchResult]:
        query_vector = await self.embeddings.aembed_query(query)

        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=k,
            where=filter,
        )

        return [
            SearchResult(
                document=Document(
                    content=doc,
                    metadata=meta,
                ),
                score=1.0 - dist,   # ChromaDB returns distances, convert to similarity
                rank=i,
            )
            for i, (doc, meta, dist) in enumerate(zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ))
        ]

    async def count(self) -> int:
        return self.collection.count()

    async def get_all(self) -> list[Document]:
        result = self.collection.get()
        return [
            Document(content=doc, metadata=meta)
            for doc, meta in zip(result["documents"], result["metadatas"])
        ]

    async def delete(self, filter: dict) -> int:
        ids = self.collection.get(where=filter)["ids"]
        if ids:
            self.collection.delete(ids=ids)
        return len(ids)
```

---

## `indexer.py` — DocumentIndexer

```python
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from axiom.config import settings
from .base import Document

class DocumentIndexer:
    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size or settings.chunk_size,
            chunk_overlap=chunk_overlap or settings.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def chunk_text(self, text: str, metadata: dict) -> list[Document]:
        chunks = self.splitter.split_text(text)
        return [
            Document(
                content=chunk,
                metadata={
                    **metadata,
                    "chunk_id": i,
                    "total_chunks": len(chunks),
                },
            )
            for i, chunk in enumerate(chunks)
        ]

    def chunk_file(self, file_path: Path) -> list[Document]:
        content = file_path.read_text(encoding="utf-8", errors="replace")
        return self.chunk_text(content, {
            "source": str(file_path),
            "file_name": file_path.name,
            "file_type": file_path.suffix,
        })
```

---

## Indexing Script

`axiom-experiments/scripts/index_documents.py` (planned):

```bash
# Index your axiom workspace
python axiom-experiments/scripts/index_documents.py ~/axiom

# Re-index after changes
python axiom-experiments/scripts/index_documents.py ~/axiom --clear
```

---

## Resetting the Database

If you change embedding models or chunking settings, delete and re-index:

```bash
rm -rf axiom-core/chroma_db/
python axiom-experiments/scripts/index_documents.py ~/axiom
```

---

## Unit Tests

`tests/unit/test_vectorstore.py`:

```python
import pytest
import tempfile
from axiom.vectorstore.chroma import ChromaVectorStore
from axiom.vectorstore.base import Document

@pytest.fixture
async def store(tmp_path):
    return ChromaVectorStore(
        collection_name="test",
        persist_directory=str(tmp_path),
    )

@pytest.mark.asyncio
async def test_add_and_search(store):
    docs = [
        Document("FastAPI is a Python web framework", {"source": "docs.md"}),
        Document("ChromaDB stores vector embeddings", {"source": "db.md"}),
    ]
    await store.add_documents(docs)

    results = await store.search("Python web framework", k=1)
    assert len(results) == 1
    assert "FastAPI" in results[0].document.content

@pytest.mark.asyncio
async def test_count(store):
    assert await store.count() == 0
    docs = [Document("text", {"source": "a.md"})]
    await store.add_documents(docs)
    assert await store.count() == 1
```

---

## Related Docs

- [Embeddings](rag/embeddings.md)
- [Chunking Strategies](rag/chunking.md)
- [RAG Pipeline](rag/pipeline.md)
- [axiom-core index](index.md)
