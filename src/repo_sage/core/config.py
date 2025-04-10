"""Configuration management for RepoSage."""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # LLM Provider Configuration
    llm_provider: str = Field(default="openai", description="LLM provider name")
    llm_api_key: Optional[str] = Field(default=None, description="API key for LLM service")
    llm_base_url: Optional[str] = Field(default=None, description="Base URL for LLM API")
    llm_model: str = Field(default="gpt-4", description="Model name to use")
    llm_temperature: float = Field(default=0.2, description="Temperature for LLM generation")
    llm_max_tokens: int = Field(default=4096, description="Max tokens per request")
    
    # Analysis Configuration
    max_file_size_kb: int = Field(default=500, description="Skip files larger than this")
    max_workers: int = Field(default=4, description="Max concurrent workers")
    target_extensions: tuple = Field(
        default=(".py", ".js", ".ts", ".java", ".go"),
        description="File extensions to analyze"
    )
    
    # Refactoring Configuration
    auto_apply_refactor: bool = Field(default=False, description="Auto apply refactoring")
    output_dir: str = Field(default="./reports", description="Output directory for reports")
    
    class Config:
        env_prefix = "REPOSAGE_"
        env_file = ".env"


# Global settings instance
settings = Settings()
