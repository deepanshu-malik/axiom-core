# Models — Implementation Reference

> **Status: 🔲 Phase 2**

Implementation guide for `axiom-core/src/axiom/models/`.

For concepts and provider comparison, see [Model Layer Overview](models/overview.md) and [Providers](models/providers.md).

---

## Module Layout

```
src/axiom/models/
├── __init__.py          ← exports: BaseLLM, ModelResponse, get_llm
├── base.py              ← BaseLLM ABC, ModelResponse dataclass
├── openai_models.py     ← OpenAIModel
├── anthropic_models.py  ← AnthropicModel
├── ollama_models.py     ← OllamaModel
├── router.py            ← get_llm() factory
└── types.py             ← ModelProvider enum (already in settings.py)
```

---

## Implementation Order

1. `base.py` — define the interface
2. `openai_models.py` — first concrete implementation
3. `router.py` — factory function
4. `anthropic_models.py` and `ollama_models.py`
5. Unit tests in `tests/unit/test_models.py`

---

## `base.py`

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator

@dataclass
class ModelResponse:
    answer: str
    model_name: str
    token_count: int
    latency_seconds: float
    cost_usd: float
    metadata: dict = field(default_factory=dict)

class BaseLLM(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        context: list[str],
        temperature: float = 0.0,
        max_tokens: int = 1000,
        **kwargs,
    ) -> ModelResponse: ...

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        context: list[str],
        **kwargs,
    ) -> AsyncIterator[str]: ...

    @property
    @abstractmethod
    def model_name(self) -> str: ...

    @property
    @abstractmethod
    def context_window(self) -> int: ...

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        return 0.0
```

---

## `openai_models.py`

```python
import time
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from axiom.models.base import BaseLLM, ModelResponse

OPENAI_PRICING = {
    "gpt-4o":      (2.50, 10.00),   # (input, output) per 1M tokens
    "gpt-4o-mini": (0.15,  0.60),
}

class OpenAIModel(BaseLLM):
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self._model_name = model_name
        self.llm = ChatOpenAI(model=model_name)

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def context_window(self) -> int:
        return 128_000

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        in_rate, out_rate = OPENAI_PRICING.get(self._model_name, (0, 0))
        return (input_tokens * in_rate + output_tokens * out_rate) / 1_000_000

    async def generate(
        self,
        prompt: str,
        context: list[str],
        temperature: float = 0.0,
        max_tokens: int = 1000,
        **kwargs,
    ) -> ModelResponse:
        messages = [HumanMessage(content=prompt)]

        t0 = time.time()
        response = await self.llm.ainvoke(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        latency = time.time() - t0

        usage = response.usage_metadata or {}
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)

        return ModelResponse(
            answer=response.content,
            model_name=self._model_name,
            token_count=input_tokens + output_tokens,
            latency_seconds=latency,
            cost_usd=self.estimate_cost(input_tokens, output_tokens),
            metadata={"input_tokens": input_tokens, "output_tokens": output_tokens},
        )

    async def generate_stream(self, prompt, context, **kwargs):
        async for chunk in self.llm.astream(prompt):
            yield chunk.content
```

---

## `router.py`

```python
from axiom.config import settings
from axiom.config.settings import ModelProvider
from axiom.models.base import BaseLLM
from axiom.models.openai_models import OpenAIModel
from axiom.models.anthropic_models import AnthropicModel
from axiom.models.ollama_models import OllamaModel

def get_llm(provider: str | None = None, model: str | None = None) -> BaseLLM:
    """Return the correct LLM based on config or explicit overrides."""
    _provider = ModelProvider(provider) if provider else settings.llm_provider
    _model = model or settings.llm_model

    match _provider:
        case ModelProvider.OPENAI:
            return OpenAIModel(_model)
        case ModelProvider.ANTHROPIC:
            return AnthropicModel(_model)
        case ModelProvider.OLLAMA:
            return OllamaModel(_model)
        case _:
            raise ValueError(f"Unknown provider: {_provider}")
```

---

## Unit Tests

`tests/unit/test_models.py` — test each provider with a simple prompt:

```python
import pytest
from unittest.mock import AsyncMock, patch
from axiom.models.openai_models import OpenAIModel
from axiom.models.base import ModelResponse

@pytest.mark.asyncio
async def test_openai_model_returns_model_response():
    model = OpenAIModel("gpt-4o-mini")
    # Mock the LangChain call to avoid real API usage in unit tests
    with patch.object(model.llm, "ainvoke", new_callable=AsyncMock) as mock:
        mock.return_value.content = "Test answer"
        mock.return_value.usage_metadata = {"input_tokens": 10, "output_tokens": 5}
        response = await model.generate("What is 2+2?", [])

    assert isinstance(response, ModelResponse)
    assert response.model_name == "gpt-4o-mini"
    assert response.token_count == 15
    assert response.cost_usd > 0

@pytest.mark.asyncio
async def test_cost_calculation():
    model = OpenAIModel("gpt-4o-mini")
    cost = model.estimate_cost(input_tokens=1000, output_tokens=200)
    # 1000 * 0.15 / 1M + 200 * 0.60 / 1M = 0.00015 + 0.00012 = 0.00027
    assert abs(cost - 0.00027) < 0.000001
```

---

## Related Docs

- [Model Layer Overview](models/overview.md)
- [Providers](models/providers.md)
- [Cost Tracking](models/cost-tracking.md)
- [axiom-core index](index.md)
