"""Main FastAPI application entry point."""

from fastapi import FastAPI

from axiom import __version__
from axiom.api import config, health, query

app = FastAPI(
    title="Axiom API",
    version=__version__,
    description="MCP-enabled personal knowledge assistant",
)

# Include routers
app.include_router(health.router)
app.include_router(config.router)
app.include_router(query.router)


@app.get("/")
async def root() -> dict:
    """Root endpoint with API information."""
    return {
        "message": "Axiom API",
        "version": __version__,
        "docs": "/docs",
    }
