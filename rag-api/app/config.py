"""Configuration settings for the Paperless RAG API."""

import os
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Paperless-ngx Configuration
    PAPERLESS_BASE_URL: str
    PAPERLESS_API_TOKEN: str
    
    # OpenRouter Configuration
    OPENROUTER_API_KEY: str
    OPENROUTER_MODEL: str = "openai/gpt-oss-20b"
    
    # Vector Database Configuration
    QDRANT_URL: str = "http://qdrant:6333"
    
    # Embedding Configuration
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    
    # RAG Configuration
    RAG_TOP_K: int = 6
    CHUNK_TOKENS: int = 800
    CHUNK_OVERLAP: int = 120
    MAX_SNIPPETS_TOKENS: int = 2500
    
    # Server Configuration
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8088
    ALLOWED_ORIGINS: str = "http://localhost,http://localhost:3000,http://192.168.1.77,http://192.168.1.77:3000"
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    
    @field_validator('ALLOWED_ORIGINS')
    @classmethod
    def parse_allowed_origins(cls, v):
        """Parse comma-separated origins into a list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    @field_validator('PAPERLESS_BASE_URL')
    @classmethod
    def validate_paperless_url(cls, v):
        """Ensure paperless URL doesn't end with slash."""
        return v.rstrip('/')
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
