# Architecture Overview

Axiom is split into three independent repositories that communicate through well-defined interfaces. This separation makes each layer independently testable and replaceable.

---

## High-Level Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User / MCP Client                           │
│                   (Claude, Claude Code, curl)                       │
└────────────────────────────┬────────────────────────────────────────┘
                             │ HTTP / MCP protocol
┌────────────────────────────▼────────────────────────────────────────┐
│                       axiom-core  (FastAPI)                         │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    Query Engine (RAG)                        │    │
│  │  1. Receive query                                            │    │
│  │  2. Retrieve relevant chunks from vector store              │    │
│  │  3. Build prompt with retrieved context                     │    │
│  │  4. Call LLM, return answer + sources + cost                │    │
│  └───────────────┬───────────────────────┬──────────────────────┘   │
│                  │                       │                          │
│  ┌───────────────▼──────┐   ┌────────────▼─────────────┐           │
│  │    Model Layer       │   │     Vector Store          │           │
│  │  BaseLLM interface   │   │  ChromaDB + embeddings    │           │
│  │  OpenAI / Anthropic  │   │  Semantic search          │           │
│  │  Ollama (local)      │   │  BM25 keyword index       │           │
│  └──────────────────────┘   └────────────┬──────────────┘           │
│                                          │                          │
│  ┌───────────────────────────────────────▼──────────────────────┐   │
│  │                    MCP Client Manager                         │   │
│  │  Connects to MCP servers, routes resource/tool requests      │   │
│  └─────────────────────────┬─────────────────────────────────────┘  │
└────────────────────────────┼────────────────────────────────────────┘
                             │ MCP protocol (stdio)
┌────────────────────────────▼────────────────────────────────────────┐
│                    axiom-mcp-servers                                 │
│                                                                     │
│  ┌─────────────────────┐      ┌─────────────────────┐              │
│  │  Filesystem Server  │      │   GitHub Server      │              │
│  │  ✅ Implemented     │      │   🔲 Planned          │              │
│  │                     │      │                     │              │
│  │  Tools:             │      │  Tools:             │              │
│  │  • list_directory   │      │  • search_code      │              │
│  │  • read_file        │      │  • get_repo_tree    │              │
│  │  • search_files     │      │  • read_file        │              │
│  │  • get_file_info    │      │                     │              │
│  │  • list_allowed_dirs│      │                     │              │
│  └─────────────────────┘      └─────────────────────┘              │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    axiom-experiments                                 │
│              (Jupyter — runs independently of core)                 │
│                                                                     │
│   Notebooks → validate models, embeddings, chunking, retrieval      │
│   Results inform what gets built into axiom-core                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Repositories and Responsibilities

### `axiom-core`
The main application. Exposes a FastAPI HTTP API that orchestrates the full RAG pipeline.

**Key modules:**
| Module | Purpose |
|--------|---------|
| `api/` | FastAPI routes — `/health`, `/config`, `/query` |
| `config/settings.py` | Pydantic settings loaded from `.env` |
| `models/` | `BaseLLM` interface + OpenAI, Anthropic, Ollama implementations |
| `vectorstore/` | `VectorStore` interface + ChromaDB implementation |
| `rag/` | `QueryEngine`, retrieval strategies, rerankers |
| `mcp/` | MCP client manager for connecting to servers |

### `axiom-mcp-servers`
Standalone MCP servers that expose data sources. Each server runs as a separate process, communicating via stdio transport.

**Key servers:**
| Server | Status | Exposes |
|--------|--------|---------|
| `servers/filesystem/` | ✅ Complete | Local files via 5 tools + 3 prompts |
| `servers/github/` | 🔲 Planned | GitHub repos via code search |
| `servers/gdrive/` | 🔲 Phase 2+ | Google Drive files |

### `axiom-experiments`
A self-contained Jupyter environment for testing components before they are built into `axiom-core`. **Nothing in experiments depends on axiom-core.** This is intentional — it lets you validate approaches cheaply before committing to an implementation.

---

## Technology Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Web framework | FastAPI + Uvicorn | Async, auto docs, Pydantic validation |
| LLM providers | LangChain (OpenAI, Anthropic, Ollama) | Unified interface, easy switching |
| Vector store | ChromaDB | Embedded, no separate server needed |
| MCP servers | FastMCP | Minimal boilerplate for MCP protocol |
| Settings | Pydantic Settings | Type-safe env var loading |
| Testing | pytest + pytest-asyncio | Async-compatible test runner |
| Code quality | Ruff | Fast linting + formatting |

---

## Design Principles

### 1. Abstraction over implementation
Every provider implements the same interface (`BaseLLM`, `VectorStore`, `BaseRetriever`). Swapping from OpenAI to Anthropic or from ChromaDB to Pinecone requires changing one line, not rewriting business logic.

### 2. Experiments before implementation
New components — models, chunking strategies, retrieval approaches — are validated in `axiom-experiments` notebooks first. Only proven approaches get built into `axiom-core`.

### 3. MCP servers as independent services
Each MCP server runs in its own process with its own config. They can be developed, tested, and deployed without touching `axiom-core`. The MCP protocol defines the boundary.

### 4. Configuration as code
All runtime behavior is controlled by environment variables, loaded as typed Pydantic settings. No magic constants in business logic.

---

## Repo Boundaries

```
What crosses the boundary between repos:
  axiom-core ↔ axiom-mcp-servers:   MCP protocol over stdio
  axiom-core ↔ user:                HTTP REST API
  axiom-experiments → axiom-core:   insights only (no code dependency)
```

`axiom-experiments` deliberately has **no import dependency** on `axiom-core`. The notebooks reimport provider libraries (LangChain, OpenAI SDK) directly. This keeps experiments fast and independent.

---

→ **Next:** [Data Flow](data-flow.md)

**Related:** [MCP Overview](../mcp/overview.md) · [API Overview](../api/overview.md) · [Installation](../getting-started/installation.md)
