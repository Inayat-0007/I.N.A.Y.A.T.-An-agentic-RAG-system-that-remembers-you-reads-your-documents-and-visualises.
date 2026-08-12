"""Type-safe application settings loaded from environment variables.

This module only reads and validates configuration. It must not call
Gemini, Neo4j, Mem0, or any other external service.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class InayatSettings(BaseSettings):
    """Central configuration for I.N.A.Y.A.T. (env-backed, no hardcoded secrets)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: str = Field(validation_alias="GEMINI_API_KEY")
    mem0_api_key: str = Field(default="", validation_alias="MEM0_API_KEY")
    neo4j_uri: str = Field(default="", validation_alias="NEO4J_URI")
    neo4j_username: str = Field(default="neo4j", validation_alias="NEO4J_USERNAME")
    neo4j_password: str = Field(default="", validation_alias="NEO4J_PASSWORD")

    llm_model: str = Field(
        default="gemini-flash-lite-latest", validation_alias="INAYAT_LLM_MODEL"
    )
    embed_model: str = Field(
        default="gemini-embedding-001", validation_alias="INAYAT_EMBED_MODEL"
    )
    chunk_size: int = Field(default=512, validation_alias="INAYAT_CHUNK_SIZE", ge=64)
    chunk_overlap: int = Field(
        default=64, validation_alias="INAYAT_CHUNK_OVERLAP", ge=0
    )
    similarity_top_k: int = Field(default=5, validation_alias="INAYAT_TOP_K", ge=1)
    mmr_enabled: bool = Field(default=False, validation_alias="INAYAT_MMR_ENABLED")
    mmr_lambda: float = Field(
        default=0.7, validation_alias="INAYAT_MMR_LAMBDA", ge=0.0, le=1.0
    )
    max_upload_bytes: int = Field(
        default=10_485_760, validation_alias="INAYAT_MAX_UPLOAD_BYTES", ge=1
    )
    demo_mode: bool = Field(default=False, validation_alias="INAYAT_DEMO_MODE")
    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:8000",
        validation_alias="INAYAT_CORS_ORIGINS",
    )
    log_level: str = Field(default="INFO", validation_alias="INAYAT_LOG_LEVEL")
    allow_empty_from_existing: bool = Field(
        default=True, validation_alias="INAYAT_ALLOW_EMPTY_FROM_EXISTING"
    )

    @field_validator("gemini_api_key")
    @classmethod
    def gemini_key_not_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("GEMINI_API_KEY is required and cannot be blank.")
        return value.strip()

    @model_validator(mode="after")
    def validate_chunking(self) -> "InayatSettings":
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("INAYAT_CHUNK_OVERLAP must be less than INAYAT_CHUNK_SIZE.")
        return self

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def missing_recommended_vars(self) -> List[str]:
        missing: List[str] = []
        if not self.mem0_api_key:
            missing.append("MEM0_API_KEY")
        if not self.neo4j_uri:
            missing.append("NEO4J_URI")
        if not self.neo4j_password:
            missing.append("NEO4J_PASSWORD")
        return missing


@lru_cache
def get_settings() -> InayatSettings:
    """Return cached settings instance (reload via ``clear_settings_cache()`` in tests)."""
    return InayatSettings()


def clear_settings_cache() -> None:
    """Clear the settings cache (for tests and env reload)."""
    get_settings.cache_clear()
