"""Pydantic settings for Axiom configuration."""

from enum import Enum

from pydantic_settings import BaseSettings, SettingsConfigDict


class ModelProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


class RetrieverStrategy(str, Enum):
    """Supported retrieval strategies."""

    SEMANTIC = "semantic"
    HYBRID = "hybrid"
    KEYWORD = "keyword"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # API Keys
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    github_token: str | None = None

    # Model Selection
    llm_provider: ModelProvider = ModelProvider.OPENAI
    llm_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"

    # RAG Configuration
    retriever_strategy: RetrieverStrategy = RetrieverStrategy.HYBRID
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k: int = 5
    rerank: bool = False

    # Model Parameters
    temperature: float = 0.0
    max_tokens: int = 1000

    # Vector Store
    chroma_persist_dir: str = "./chroma_db"
    collection_name: str = "axiom_knowledge"

    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000


# Global settings instance
settings = Settings()
