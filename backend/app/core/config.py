"""Application Configuration and Environment Settings."""

from typing import Any

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration class loading environment variables."""

    # Project Information
    PROJECT_NAME: str = "MyAgent — Personal AI Coding Agent"
    VERSION: str = "0.7.0"
    ENVIRONMENT: str = "development"  # Options: "development", "testing", "production"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Server Binding
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Security & CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # JWT Authentication & Security
    JWT_SECRET_KEY: str = Field(
        default="dev_secret_key_change_in_production_32bytes_min_length_secret",
        description="Secret key for signing JWT tokens",
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    JWT_ISSUER: str = Field(default="agentai-api", description="JWT token issuer claim")
    JWT_AUDIENCE: str = Field(default="agentai-ui", description="JWT token audience claim")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60, ge=1, description="JWT access token validity in minutes"
    )

    # Database Settings
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "agentai"
    MONGODB_DB_NAME: str = "agentai"
    MONGODB_CONNECT_TIMEOUT_MS: int = 5000

    # LLM Settings
    DEFAULT_LLM_PROVIDER: str = "mock"
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # RAG Settings
    RAG_ENABLED: bool = True
    EMBEDDING_PROVIDER: str = "local"  # Options: "local", "ngram", "openai", "gemini"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    RAG_TOP_K: int = 8
    RAG_MIN_SCORE: float = 0.15
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 120
    RAG_MAX_CONTEXT_TOKENS: int = 6000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Enforce standard environment name."""
        allowed = ("development", "testing", "production")
        val = v.lower().strip()
        if val not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}, got '{v}'")
        return val

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        """Parse comma-separated string or list into list of origins."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return v
        return ["http://localhost:3000"]

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        """Strict production mode security configuration checks."""
        if self.ENVIRONMENT == "production":
            # 1. Require strong non-default secret
            if (
                len(self.JWT_SECRET_KEY) < 32
                or self.JWT_SECRET_KEY.startswith("dev_secret_key")
                or "change_in_production" in self.JWT_SECRET_KEY
            ):
                raise ValueError(
                    "Production Mode Error: JWT_SECRET_KEY must be a secure random secret "
                    "with at least 32 characters."
                )

            # 2. Require strict non-wildcard CORS origins
            if not self.CORS_ORIGINS or "*" in self.CORS_ORIGINS:
                raise ValueError(
                    "Production Mode Error: CORS_ORIGINS must not contain '*' wildcard. "
                    "Specify explicit trusted origins."
                )

        return self


settings = Settings()
