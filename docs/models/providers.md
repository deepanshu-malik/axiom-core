# LLM Providers

Axiom supports three LLM providers. All implement `BaseLLM` and return `ModelResponse` — the caller never needs to know which is active.

---

## Comparison

| Provider | Models | Cost | Latency | Context | Best for |
|----------|--------|------|---------|---------|----------|
| OpenAI | gpt-4o, gpt-4o-mini | $$ | Fast | 128K | General purpose, fast iteration |
| Anthropic | claude-3-5-sonnet, claude-3-5-haiku | $$ | Medium | 200K | Long docs, analysis, reasoning |
| Ollama | llama3.2, qwen2.5 | Free | Slow (CPU) | 128K | Privacy, offline, zero cost |

---

## OpenAI

**Module:** `axiom-core/src/axiom/models/openai_models.py`
**Dependency:** `langchain-openai`

### Supported models

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Context |
|-------|-----------------------|------------------------|---------|
| `gpt-4o` | $2.50 | $10.00 | 128K |
| `gpt-4o-mini` | $0.15 | $0.60 | 128K |

`gpt-4o-mini` is recommended for development — it's fast and cheap enough to run hundreds of test queries without meaningful cost.

### Configuration

```bash
OPENAI_API_KEY=sk-...
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
```

### Planned implementation

```python
from langchain_openai import ChatOpenAI
from axiom.models.base import BaseLLM, ModelResponse

class OpenAIModel(BaseLLM):
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self._model_name = model_name
        self.llm = ChatOpenAI(model=model_name, temperature=0.0)

    async def generate(self, prompt, context, **kwargs) -> ModelResponse:
        # Build messages, call LLM, parse token usage, calculate cost
        ...

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        rates = {
            "gpt-4o": (2.50, 10.00),
            "gpt-4o-mini": (0.15, 0.60),
        }
        in_rate, out_rate = rates.get(self._model_name, (0, 0))
        return (input_tokens * in_rate + output_tokens * out_rate) / 1_000_000
```

---

## Anthropic

**Module:** `axiom-core/src/axiom/models/anthropic_models.py`
**Dependency:** `langchain-anthropic`

### Supported models

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Context |
|-------|-----------------------|------------------------|---------|
| `claude-3-5-sonnet-20241022` | $3.00 | $15.00 | 200K |
| `claude-3-5-haiku-20241022` | $0.80 | $4.00 | 200K |

Anthropic models have a 200K token context window — nearly double OpenAI. This matters when retrieving large files or many chunks simultaneously.

### Configuration

```bash
ANTHROPIC_API_KEY=sk-ant-...
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-haiku-20241022
```

### Planned implementation

```python
from langchain_anthropic import ChatAnthropic
from axiom.models.base import BaseLLM, ModelResponse

class AnthropicModel(BaseLLM):
    def __init__(self, model_name: str = "claude-3-5-haiku-20241022"):
        self._model_name = model_name
        self.llm = ChatAnthropic(model=model_name)

    async def generate(self, prompt, context, **kwargs) -> ModelResponse:
        ...

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        rates = {
            "claude-3-5-sonnet-20241022": (3.00, 15.00),
            "claude-3-5-haiku-20241022": (0.80, 4.00),
        }
        in_rate, out_rate = rates.get(self._model_name, (0, 0))
        return (input_tokens * in_rate + output_tokens * out_rate) / 1_000_000
```

---

## Ollama (Local Models)

**Module:** `axiom-core/src/axiom/models/ollama_models.py`
**Dependency:** `langchain-community` + Ollama running locally

Ollama lets you run open-source models entirely on your own hardware — no API key, no cost, no data leaving your machine.

### Supported models

| Model | Parameters | RAM required | Best for |
|-------|-----------|--------------|----------|
| `llama3.2` | 3B | ~4GB | Fast, general purpose |
| `llama3.2:1b` | 1B | ~2GB | Very fast, low quality |
| `qwen2.5` | 7B | ~8GB | Code understanding |
| `qwen2.5:14b` | 14B | ~16GB | High quality, slow |

### Setup

```bash
# Install Ollama: https://ollama.com
ollama serve                    # Start the Ollama daemon
ollama pull llama3.2            # Download the model (~2GB)
```

### Configuration

```bash
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
# No API key needed
# Assumes Ollama at http://localhost:11434
```

### Cost estimation

Ollama models are free to run — `estimate_cost()` always returns `0.0`. Latency is higher than cloud models, especially on CPU-only machines.

---

## Switching Between Providers

Change `.env` and restart the server:

```bash
# Switch to Anthropic haiku
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-haiku-20241022
```

Or override per-request via the API:

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is FastAPI?", "model": "claude-3-5-haiku-20241022"}'
```

---

## Testing All Providers

Use `axiom-experiments/notebooks/01_model_testing.ipynb` to test all configured providers before implementing the model layer. The notebook compares:

- Response quality on the same prompt
- Latency distribution over 10 calls
- Token usage and cost per query

See [Notebooks Guide](../experiments/notebooks.md) for details.

---

→ **Next:** [Cost Tracking](cost-tracking.md)

**Related:** [Model Layer Overview](overview.md) · [Experiments Notebooks](../experiments/notebooks.md)
