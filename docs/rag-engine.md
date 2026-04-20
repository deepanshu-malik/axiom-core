# RAG Engine — Implementation Reference

> **Status: 🔲 Phase 4**

Implementation guide for `axiom-core/src/axiom/rag/` and `axiom-core/src/axiom/mcp/`.

For concepts, see [RAG Pipeline](rag/pipeline.md) and [Retrieval Strategies](rag/retrieval.md).

---

## Module Layout

```
src/axiom/
├── rag/
│   ├── __init__.py
│   ├── engine.py               ← QueryEngine
│   ├── retrievers/
│   │   ├── __init__.py
│   │   ├── base.py             ← BaseRetriever ABC
│   │   ├── semantic.py         ← SemanticRetriever
│   │   ├── hybrid.py           ← HybridRetriever
│   │   └── keyword.py          ← KeywordRetriever (BM25)
│   └── rerankers/
│       ├── __init__.py
│       ├── base.py             ← BaseReranker ABC
│       └── cohere.py           ← CohereReranker
└── mcp/
    ├── __init__.py
    ├── manager.py              ← MCPManager
    ├── client.py               ← MCPClient (protocol)
    └── registry.py             ← server config/discovery
```

---

## `rag/retrievers/base.py`

```python
from abc import ABC, abstractmethod
from axiom.vectorstore.base import SearchResult

class BaseRetriever(ABC):
    @abstractmethod
    async def retrieve(self, query: str, k: int = 5) -> list[SearchResult]: ...
```

---

## `rag/retrievers/semantic.py`

```python
from axiom.vectorstore.base import VectorStore, SearchResult
from .base import BaseRetriever

class SemanticRetriever(BaseRetriever):
    def __init__(self, vectorstore: VectorStore):
        self.vectorstore = vectorstore

    async def retrieve(self, query: str, k: int = 5) -> list[SearchResult]:
        return await self.vectorstore.search(query, k=k)
```

---

## `rag/retrievers/hybrid.py`

```python
from rank_bm25 import BM25Okapi
from axiom.vectorstore.base import VectorStore, SearchResult, Document
from .base import BaseRetriever

class HybridRetriever(BaseRetriever):
    def __init__(self, vectorstore: VectorStore, alpha: float = 0.7):
        self.vectorstore = vectorstore
        self.alpha = alpha
        self._bm25: BM25Okapi | None = None
        self._docs: list[Document] = []

    async def build_index(self) -> None:
        """Build BM25 index from all documents in the vector store."""
        self._docs = await self.vectorstore.get_all()
        tokenized = [doc.content.split() for doc in self._docs]
        self._bm25 = BM25Okapi(tokenized)

    async def retrieve(self, query: str, k: int = 5) -> list[SearchResult]:
        if self._bm25 is None:
            await self.build_index()

        # Semantic candidates (2x to allow re-scoring)
        semantic = await self.vectorstore.search(query, k=k * 2)

        # BM25 scores
        bm25_scores = self._bm25.get_scores(query.split())

        # Merge
        scores: dict[str, float] = {}
        doc_map: dict[str, Document] = {}

        for result in semantic:
            doc_id = result.document.metadata.get("source", "") + str(result.rank)
            scores[doc_id] = self.alpha * result.score
            doc_map[doc_id] = result.document

        for idx, score in enumerate(bm25_scores):
            doc = self._docs[idx]
            doc_id = doc.metadata.get("source", "") + str(idx)
            scores[doc_id] = scores.get(doc_id, 0) + (1 - self.alpha) * score
            doc_map[doc_id] = doc

        # Return top-k
        top_ids = sorted(scores, key=lambda x: scores[x], reverse=True)[:k]
        return [
            SearchResult(document=doc_map[doc_id], score=scores[doc_id], rank=i)
            for i, doc_id in enumerate(top_ids)
        ]
```

---

## `rag/engine.py`

```python
import time
from dataclasses import dataclass
from axiom.models.base import BaseLLM, ModelResponse
from axiom.vectorstore.base import VectorStore, SearchResult
from axiom.rag.retrievers.hybrid import HybridRetriever
from axiom.rag.retrievers.semantic import SemanticRetriever
from axiom.rag.retrievers.keyword import KeywordRetriever

@dataclass
class QueryResponse:
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
        retriever_type: str = "hybrid",
        top_k: int = 5,
        use_reranking: bool = False,
    ):
        self.llm = llm
        self.top_k = top_k

        match retriever_type:
            case "hybrid":
                self.retriever = HybridRetriever(vectorstore, alpha=0.7)
            case "semantic":
                self.retriever = SemanticRetriever(vectorstore)
            case "keyword":
                self.retriever = KeywordRetriever(vectorstore)
            case _:
                raise ValueError(f"Unknown retriever: {retriever_type}")

    async def query(self, query: str) -> QueryResponse:
        start = time.time()

        t0 = time.time()
        results = await self.retriever.retrieve(query, k=self.top_k)
        retrieval_time = time.time() - t0

        context = [r.document.content for r in results]
        prompt = self._build_prompt(query, context)
        model_response = await self.llm.generate(prompt, context)

        return QueryResponse(
            answer=model_response.answer,
            sources=results,
            model_response=model_response,
            retrieval_time=retrieval_time,
            total_time=time.time() - start,
        )

    def _build_prompt(self, query: str, context: list[str]) -> str:
        context_str = "\n\n".join(
            f"Document {i+1}:\n{doc}" for i, doc in enumerate(context)
        )
        return (
            "You are a helpful assistant answering questions about a codebase and documents.\n"
            "Use only the provided context to answer. If the answer is not in the context, say so.\n"
            "Always cite which document(s) you used.\n\n"
            f"Context:\n{context_str}\n\n"
            f"Question: {query}\n\n"
            "Answer:"
        )
```

---

## MCP Client Manager

```
src/axiom/mcp/
├── manager.py     ← MCPManager: connects to servers, routes requests
├── client.py      ← MCPClient: wraps fastmcp.Client per server
└── registry.py    ← reads server configs from env or config file
```

```python
# manager.py — planned design
from fastmcp import Client as MCPClient

class MCPManager:
    def __init__(self):
        self._clients: dict[str, MCPClient] = {}

    async def connect(self, name: str, command: list[str]) -> None:
        """Launch server subprocess and connect."""
        self._clients[name] = MCPClient({"command": command[0], "args": command[1:]})

    async def call_tool(self, server: str, tool: str, args: dict):
        async with self._clients[server] as client:
            return await client.call_tool(tool, args)

    async def read_resource(self, server: str, uri: str) -> str:
        async with self._clients[server] as client:
            result = await client.read_resource(uri)
            return result[0].text
```

---

## Wiring `/query` in Phase 4

`api/query.py` — replace the 501 stub:

```python
from functools import lru_cache
from fastapi import APIRouter, Depends, HTTPException
from axiom.models.router import get_llm
from axiom.vectorstore.chroma import ChromaVectorStore
from axiom.rag.engine import QueryEngine
from axiom.config import settings

router = APIRouter(prefix="/query", tags=["query"])

@lru_cache
def _get_engine() -> QueryEngine:
    return QueryEngine(
        llm=get_llm(),
        vectorstore=ChromaVectorStore(),
        retriever_type=settings.retriever_strategy.value,
        top_k=settings.top_k,
        use_reranking=settings.rerank,
    )

@router.post("/", response_model=QueryResponseModel)
async def query_knowledge(
    request: QueryRequest,
    engine: QueryEngine = Depends(_get_engine),
) -> QueryResponseModel:
    try:
        llm = get_llm(model=request.model) if request.model else None
        if llm:
            engine = QueryEngine(llm=llm, vectorstore=engine.vectorstore)
        response = await engine.query(request.query)
        return QueryResponseModel(
            answer=response.answer,
            sources=[...],
            model_used=response.model_response.model_name,
            total_time=response.total_time,
            cost_usd=response.model_response.cost_usd,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Related Docs

- [RAG Pipeline](rag/pipeline.md)
- [Retrieval Strategies](rag/retrieval.md)
- [Data Flow](architecture/data-flow.md)
- [axiom-core index](index.md)
