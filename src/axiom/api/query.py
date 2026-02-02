"""Query endpoint for RAG queries."""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/query", tags=["query"])


class QueryRequest(BaseModel):
    """Request model for query endpoint."""

    query: str
    top_k: int = 5
    model: str | None = None  # Allow model override


class QueryResponse(BaseModel):
    """Response model for query endpoint."""

    answer: str
    sources: list[dict[str, Any]]
    model_used: str
    total_time: float
    cost_usd: float


@router.post("/", response_model=QueryResponse)
async def query_knowledge(request: QueryRequest) -> QueryResponse:
    """Query your personal knowledge base.

    This endpoint will be fully implemented in Phase 4.
    """
    # TODO: Implement full RAG pipeline in Phase 4
    raise HTTPException(
        status_code=501,
        detail="Query endpoint not yet implemented. Coming in Phase 4.",
    )
