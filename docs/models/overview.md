# Model Layer Overview

> **Status: 🔲 Phase 2 — not yet implemented**
>
> This document describes the planned design. The interface contract is defined; implementations are pending.

The model layer is an abstraction that lets the rest of Axiom call any LLM through a single unified interface — switching providers is a one-line config change.

---

## The Problem It Solves

Without abstraction:

```python
# Tightly coupled — every caller knows about OpenAI
from openai import AsyncOpenAI
client = AsyncOpenAI()
response = await client.chat.completions.create(model="gpt-4o-mini", ...)
# Now switching to Anthropic requires rewriting every caller
```

With the `BaseLLM` abstraction:

```python
# Loosely coupled — callers only know about BaseLLM
llm = OpenAIModel("gpt-4o-mini")
# llm = AnthropicModel("claude-3-5-haiku-20241022")  ← one line change
# llm = OllamaModel("llama3.2")                       ← one line change
response = await llm.generate(prompt="...", context=[...])
```

The `QueryEngine` takes a `BaseLLM` — it doesn't know or care whether it's talking to OpenAI or a local Llama model.

---

## The `BaseLLM` Interface

**File:** `axiom-core/src/axiom/models/base.py` (planned)

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator

@dataclass
class ModelResponse:
    """Standardised response from any LLM."""
    answer: str
    model_name: str
    token_count: int
    latency_seconds: float
    cost_usd: float
    metadata: dict          # provider-specific: input_tokens, output_tokens, etc.

class BaseLLM(ABC):
    """Abstract base class for all LLM providers."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        context: list[str],
        temperature: float = 0.0,
        max_tokens: int = 1000,
        **kwargs,
    ) -> ModelResponse:
        """Generate a completion given a prompt and retrieved context."""

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        context: list[str],
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream completion tokens one at a time."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """The model identifier string."""

    @property
    @abstractmethod
    def context_window(self) -> int:
        """Maximum context length in tokens."""

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in USD. Override in each provider subclass."""
        return 0.0
```

---

## The `ModelResponse` Schema

Every provider returns the same `ModelResponse` dataclass:

| Field | Type | Description |
|-------|------|-------------|
| `answer` | `str` | The model's text response |
| `model_name` | `str` | e.g. `"gpt-4o-mini"` |
| `token_count` | `int` | Total tokens used (input + output) |
| `latency_seconds` | `float` | Wall-clock time for the LLM call |
| `cost_usd` | `float` | Estimated cost at current pricing |
| `metadata` | `dict` | Provider-specific details |

This is what gets returned in the `/query` API response, giving users full visibility into what each query actually cost.

---

## Planned Implementations

| Module | Provider | Models |
|--------|----------|--------|
| `openai_models.py` | OpenAI | `gpt-4o`, `gpt-4o-mini` |
| `anthropic_models.py` | Anthropic | `claude-3-5-sonnet`, `claude-3-5-haiku` |
| `ollama_models.py` | Ollama (local) | `llama3.2`, `qwen2.5` |

Each is implemented with LangChain's provider integrations (`langchain-openai`, `langchain-anthropic`, `langchain-community`) to avoid writing low-level HTTP clients.

---

## Model Router

**File:** `axiom-core/src/axiom/models/router.py` (planned)

A factory function that creates the right `BaseLLM` from configuration:

```python
def get_llm(
    provider: ModelProvider | None = None,
    model: str | None = None,
) -> BaseLLM:
    """Return the correct LLM instance based on config or explicit args."""
    provider = provider or settings.llm_provider
    model = model or settings.llm_model

    if provider == ModelProvider.OPENAI:
        return OpenAIModel(model)
    elif provider == ModelProvider.ANTHROPIC:
        return AnthropicModel(model)
    elif provider == ModelProvider.OLLAMA:
        return OllamaModel(model)
    else:
        raise ValueError(f"Unknown provider: {provider}")
```

The `/query` endpoint accepts an optional `model` override:

```json
{ "query": "...", "model": "claude-3-5-haiku-20241022" }
```

This lets you switch models per-request without restarting the server.

---

## Experiments First

Before implementing the model layer in `axiom-core`, run `axiom-experiments/notebooks/01_model_testing.ipynb` to:

- Verify your API keys work
- Compare response quality across providers
- Measure latency differences
- Understand token usage patterns

Only then build the production implementation. See [Notebooks Guide](../experiments/notebooks.md).

---

→ **Next:** [Providers](providers.md)

**Related:** [Cost Tracking](cost-tracking.md) · [RAG Pipeline](../rag/pipeline.md) · [Experiments Overview](../experiments/overview.md)
