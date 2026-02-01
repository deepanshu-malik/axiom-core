# Axiom Core

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Axiom** is a personal knowledge assistant that uses RAG (Retrieval-Augmented Generation) to query your local files, GitHub repos, and documents through natural language. Built with FastAPI and the Model Context Protocol (MCP).

## ✨ Features

- 🔌 **MCP Integration** - Connect to multiple data sources via Model Context Protocol
- 🤖 **Multi-LLM Support** - Unified interface for OpenAI, Anthropic, and Ollama models
- 🔍 **Advanced RAG** - Semantic, hybrid, and keyword retrieval strategies
- 💾 **ChromaDB Vector Store** - Efficient document indexing and search
- ⚡ **FastAPI Backend** - Modern, async REST API
- 📊 **Cost Tracking** - Monitor token usage and API costs

## 🏗️ Architecture
```
User Query → FastAPI → Query Engine → [Retriever + LLM] → Response
                           ↓
                    Vector Store (ChromaDB)
                           ↓
                    MCP Servers (data sources)
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key (or Anthropic)
- Git

### Installation
```bash
git clone https://github.com/yourusername/axiom-core.git
cd axiom-core

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install dependencies
pip install -e ".[dev]"
```

### Configuration
```bash
cp .env.example .env
# Edit .env and add your API keys
```

Required environment variables:
```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...  # Optional
```

### Run the API
```bash
uvicorn axiom.api.main:app --reload
```

Visit http://localhost:8000/docs for interactive API documentation.

## 📖 Usage

### Query Your Knowledge Base
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I implement authentication in FastAPI?",
    "top_k": 5,
    "model": "gpt-4o-mini"
  }'
```

### Using Different Models
```python
from axiom.models import OpenAIModel, AnthropicModel
from axiom.rag import QueryEngine

# OpenAI
llm = OpenAIModel("gpt-4o-mini")

# Or Anthropic
llm = AnthropicModel("claude-3-5-haiku-20241022")

engine = QueryEngine(llm=llm)
response = await engine.query("Your question here")
```

## 🧪 Testing
```bash
pytest tests/
```

## 📁 Project Structure
```
axiom-core/
├── src/axiom/
│   ├── api/          # FastAPI routes
│   ├── rag/          # RAG orchestration
│   ├── models/       # LLM abstraction layer
│   ├── vectorstore/  # ChromaDB integration
│   ├── mcp/          # MCP client
│   └── config/       # Settings
└── tests/
```

## 🗺️ Roadmap

- [x] Model abstraction layer
- [x] ChromaDB vector store
- [x] Basic semantic retrieval
- [x] FastAPI endpoints
- [ ] Hybrid retrieval (vector + keyword)
- [ ] Reranking support
- [ ] GraphRAG integration
- [ ] Conversation memory

## 🤝 Related Projects

- [axiom-mcp-servers](https://github.com/yourusername/axiom-mcp-servers) - MCP server implementations
- [axiom-experiments](https://github.com/yourusername/axiom-experiments) - Model comparison & research

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [LangChain](https://python.langchain.com/)
- [ChromaDB](https://www.trychroma.com/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
