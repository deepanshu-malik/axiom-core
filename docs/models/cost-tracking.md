# Cost Tracking

Every query through Axiom reports the exact cost in USD. This lets you compare models on real workloads, not just benchmarks.

---

## How Cost is Calculated

Each LLM provider's implementation overrides `estimate_cost()`:

```python
def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
    """Return cost in USD based on current provider pricing."""
    in_rate, out_rate = self._get_rates()
    return (input_tokens * in_rate + output_tokens * out_rate) / 1_000_000
```

Token counts come from the provider's API response metadata — Axiom does not estimate them independently.

---

## Per-Model Rates

### OpenAI

| Model | Input per 1M | Output per 1M |
|-------|-------------|--------------|
| `gpt-4o` | $2.50 | $10.00 |
| `gpt-4o-mini` | $0.15 | $0.60 |

### Anthropic

| Model | Input per 1M | Output per 1M |
|-------|-------------|--------------|
| `claude-3-5-sonnet-20241022` | $3.00 | $15.00 |
| `claude-3-5-haiku-20241022` | $0.80 | $4.00 |

### Ollama

| Model | Input per 1M | Output per 1M |
|-------|-------------|--------------|
| Any | $0.00 | $0.00 |

> **Note:** Prices are hardcoded at implementation time. If provider pricing changes, update `estimate_cost()` in the relevant model module.

---

## What's Included in Token Count

`token_count` in `ModelResponse` is **input + output combined**.

`metadata` provides the breakdown:

```python
ModelResponse(
    answer="FastAPI is a modern Python web framework...",
    model_name="gpt-4o-mini",
    token_count=387,
    latency_seconds=0.84,
    cost_usd=0.000232,
    metadata={
        "input_tokens": 312,   # prompt + retrieved context
        "output_tokens": 75,   # the answer
    }
)
```

Input tokens include:
- The RAG prompt template text
- All retrieved chunks passed as context
- The user's query

Output tokens are the model's answer only.

---

## Cost in the API Response

The `/query` endpoint surfaces cost directly:

```json
{
  "answer": "FastAPI is a modern Python web framework...",
  "sources": [...],
  "model_used": "gpt-4o-mini",
  "total_time": 1.42,
  "cost_usd": 0.000232
}
```

This makes cost immediately visible to anyone using the API, without needing to check provider dashboards.

---

## Model Comparison in Experiments

The `axiom-experiments/scripts/compare_models.py` script (planned) runs the same query across all configured models and prints a comparison table:

```
┌──────────────────────────────────────────────────────────────────────┐
│ Model Comparison: 'How is auth implemented in this codebase?'        │
├─────────────────────────┬─────────┬────────┬──────────┬─────────────┤
│ Model                   │ Latency │ Tokens │ Cost     │ Answer      │
├─────────────────────────┼─────────┼────────┼──────────┼─────────────┤
│ gpt-4o-mini             │ 0.84s   │ 387    │ $0.00023 │ FastAPI ... │
│ gpt-4o                  │ 1.21s   │ 412    │ $0.00514 │ FastAPI ... │
│ claude-3-5-haiku        │ 1.05s   │ 398    │ $0.00092 │ FastAPI ... │
│ claude-3-5-sonnet       │ 1.83s   │ 445    │ $0.00802 │ FastAPI ... │
│ llama3.2 (local)        │ 4.2s    │ 371    │ $0.00000 │ FastAPI ... │
└─────────────────────────┴─────────┴────────┴──────────┴─────────────┘
```

Results are also saved to `axiom-experiments/results/comparison_{timestamp}.json`.

---

## Keeping Costs Low During Development

| Strategy | Savings |
|----------|---------|
| Use `gpt-4o-mini` or `claude-3-5-haiku` for testing | ~10× cheaper than top-tier models |
| Use Ollama for offline/private queries | 100% savings, at cost of latency |
| Reduce `TOP_K` during experiments | Fewer chunks = fewer input tokens |
| Reduce `MAX_TOKENS` for short answers | Limits output token cost |
| Run comparison scripts once, cache results | Don't re-run the same experiment repeatedly |

---

→ **Next:** [RAG Overview](../rag/overview.md)

**Related:** [Providers](providers.md) · [Model Layer Overview](overview.md) · [Experiments Overview](../experiments/overview.md)
