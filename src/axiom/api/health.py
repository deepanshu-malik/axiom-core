"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    """Check if the API is running."""
    return {"status": "healthy", "service": "axiom-core"}
