"""
AION Core Configuration
Pydantic Settings v2 - enterprise configuration management
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any, List, Optional

from pydantic import AnyUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "AION"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production-must-be-at-least-32-characters"
    API_V1_PREFIX: str = "/api/v1"
    ALLOWED_HOSTS: List[str] = ["*"]
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    # Regex fallback for origins that can't be pinned to one exact URL, e.g.
    # Vercel preview deployments (a fresh subdomain per branch/PR). Checked
    # in addition to ALLOWED_ORIGINS by CORSMiddleware. None disables it.
    ALLOWED_ORIGIN_REGEX: Optional[str] = None

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4

    # Database (SQLite for local/dev — zero-install, file-based)
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/aion.db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Graph Store (embedded NetworkX graph, replaces Neo4j for local/dev)
    GRAPH_STORE_PATH: str = "./data/graph_store.json"

    # JWT
    JWT_SECRET_KEY: str = "jwt-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # LLM
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-opus-4-6"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    LLM_PROVIDER: str = "openai"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 4096

    # Embedding
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    # Knowledge Decay
    KNOWLEDGE_DECAY_THRESHOLD_DAYS: int = 90
    KNOWLEDGE_CONFLICT_SIMILARITY_THRESHOLD: float = 0.85
    KNOWLEDGE_DUPLICATE_SIMILARITY_THRESHOLD: float = 0.95

    # OII Computation
    OII_COMPUTATION_INTERVAL_HOURS: int = 24
    BOARD_REPORT_DAY: str = "monday"
    BOARD_REPORT_HOUR: int = 8

    # Integrations
    SLACK_BOT_TOKEN: str = ""
    GITHUB_TOKEN: str = ""
    JIRA_URL: str = ""
    JIRA_EMAIL: str = ""
    JIRA_API_TOKEN: str = ""
    CONFLUENCE_URL: str = ""
    GOOGLE_CREDENTIALS_FILE: str = "google_credentials.json"
    SHAREPOINT_TENANT_ID: str = ""
    SHAREPOINT_CLIENT_ID: str = ""
    SHAREPOINT_CLIENT_SECRET: str = ""

    # Monitoring
    PROMETHEUS_ENABLED: bool = True
    SENTRY_DSN: str = ""
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def kafka_servers(self) -> List[str]:
        return self.KAFKA_BOOTSTRAP_SERVERS.split(",")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
