"""Configuration endpoint to view current settings."""

from fastapi import APIRouter

from axiom.config import settings

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/")
async def get_config() -> dict:
    """Get current configuration (excluding sensitive keys)."""
    return {
        "llm_provider": settings.llm_provider.value,
        "llm_model": settings.llm_model,
        "embedding_model": settings.embedding_model,
        "retriever_strategy": settings.retriever_strategy.value,
        "chunk_size": settings.chunk_size,
        "chunk_overlap": settings.chunk_overlap,
        "top_k": settings.top_k,
        "rerank": settings.rerank,
        "temperature": settings.temperature,
        "max_tokens": settings.max_tokens,
        "collection_name": settings.collection_name,
    }
