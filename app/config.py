"""Application configuration with dependency injection support."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = PROJECT_ROOT / "dataset"
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"
RESULTS_DIR = PROJECT_ROOT / "results"
POLICIES_DIR = KNOWLEDGE_DIR / "policies"
TEMPLATES_DIR = KNOWLEDGE_DIR / "templates"
FAQ_DIR = KNOWLEDGE_DIR / "faq"
EMBEDDINGS_DIR = KNOWLEDGE_DIR / "embeddings"


class Settings(BaseSettings):
    """Central configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(
        default="claude-sonnet-4-6",
        alias="ANTHROPIC_MODEL",
    )
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_model: str = Field(
        default="gemini-2.5-flash",
        alias="GEMINI_MODEL",
    )
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        alias="EMBEDDING_MODEL",
    )
    chroma_persist_dir: Path = Field(
        default=EMBEDDINGS_DIR / "chroma",
        alias="CHROMA_PERSIST_DIR",
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        alias="LOG_LEVEL",
    )
    cache_ttl_seconds: int = Field(default=3600, alias="CACHE_TTL_SECONDS")
    max_retries: int = Field(default=3, alias="MAX_RETRIES")
    retrieval_top_k: int = Field(default=3, alias="RETRIEVAL_TOP_K")
    knowledge_graph_path: Path = Field(
        default=KNOWLEDGE_DIR / "knowledge_graph.json",
    )
    generated_results_path: Path = Field(default=RESULTS_DIR / "generated.json")
    evaluation_results_path: Path = Field(default=RESULTS_DIR / "evaluation.json")
    dashboard_path: Path = Field(default=RESULTS_DIR / "dashboard.json")
    cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        alias="CORS_ORIGINS",
    )
    cors_origin_regex: str = Field(
        default=r"https://.*\.vercel\.app",
        alias="CORS_ORIGIN_REGEX",
    )

    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def project_root(self) -> Path:
        return PROJECT_ROOT


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton for dependency injection."""
    return Settings()
