"""
Configuration management for the Wing Aerodynamic Analyzer application.
Follows 12-factor app principles with environment variable validation.
"""
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and .env file.
    
    Uses Pydantic V2 for validation and type safety.
    All sensitive values should be provided via environment variables.
    """

    # Application
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = False
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_title: str = "Wing Aerodynamic Analyzer"
    app_version: str = "0.1.0"

    # Embeddings Configuration
    embedding_provider: Literal["openai", "local"] = "openai"
    openai_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536
    
    # Note: text-embedding-3-small produces 1536 dimensions
    # If switching models, update this value accordingly
    # text-embedding-3-large = 3072, ada = 1536

    # Database / Vector Store
    chroma_path: Path = Path("./data/chroma_db")
    airfoil_data_path: Path = Path("./data/uiuc_airfoils.csv")

    # RAG Configuration
    rag_collection_name: str = "wing_aerodynamic_data"
    rag_similarity_threshold: float = 0.3
    rag_top_k_results: int = 5

    # MCP Tools
    mcp_tools_enabled: bool = True

    # Logging
    log_level: str = "INFO"
    log_file: Path = Path("./logs/app.log")

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def __init__(self, **kwargs):
        """Initialize settings and create required directories."""
        super().__init__(**kwargs)
        # Ensure data directory exists
        self.chroma_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses LRU cache to avoid reloading settings on every request.
    In testing, clear cache with: get_settings.cache_clear()
    
    Returns:
        Settings: Application settings validated and loaded from environment
    """
    return Settings()
