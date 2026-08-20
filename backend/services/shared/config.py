"""Configuration settings for PS-02 microservices."""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App & Environment
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    LOG_LEVEL: str = Field(default="INFO")

    # Database Configuration (Supabase PostgreSQL / SQLite fallback)
    DATABASE_URL: Optional[str] = Field(default=None)
    SUPABASE_URL: Optional[str] = Field(default=None)
    SUPABASE_KEY: Optional[str] = Field(default=None)
    SUPABASE_ANON_KEY: Optional[str] = Field(default=None)
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = Field(default=None)
    SUPABASE_DB_URL: Optional[str] = Field(default=None)

    # Server Ports
    CORE_SERVER_PORT: int = Field(default=8000)
    EVENT_INTELLIGENCE_SERVER_PORT: int = Field(default=8001)
    ACTION_COMMISSION_SERVER_PORT: int = Field(default=8002)
    AUDIT_BLOCKCHAIN_SERVER_PORT: int = Field(default=8003)

    # Service Intercommunication URLs
    CORE_SERVER_URL: str = Field(default="http://127.0.0.1:8000")
    EVENT_INTELLIGENCE_SERVER_URL: str = Field(default="http://127.0.0.1:8001")
    ACTION_COMMISSION_SERVER_URL: str = Field(default="http://127.0.0.1:8002")
    AUDIT_BLOCKCHAIN_SERVER_URL: str = Field(default="http://127.0.0.1:8003")

    # Security & Auth
    JWT_SECRET_KEY: str = Field(default="ps02-crm-secret-key-change-in-production-2026")
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440)
    INTERNAL_SERVICE_SECRET: str = Field(default="ps02-internal-service-hmac-token-2026")

    # Blockchain & Audit
    BLOCKCHAIN_MODE: str = Field(default="ledger")  # "ledger" or "web3"
    BLOCKCHAIN_PROVIDER_URL: Optional[str] = Field(default=None)
    BLOCKCHAIN_CONTRACT_ADDRESS: Optional[str] = Field(default=None)
    BLOCKCHAIN_MAX_RETRIES: int = Field(default=5)
    BLOCKCHAIN_TIMEOUT_SECONDS: float = Field(default=5.0)

    # Commission Defaults
    DEFAULT_COMMISSION_RATE: float = Field(default=0.02)  # 2% default conversion commission

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_effective_db_url(self) -> str:
        """Returns the PostgreSQL / Supabase connection URL or falls back to local SQLite."""
        if self.DATABASE_URL:
            # Handle postgres:// vs postgresql://
            url = self.DATABASE_URL
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
            return url
        if self.SUPABASE_DB_URL:
            url = self.SUPABASE_DB_URL
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
            return url
        # SQLite fallback for local test/dev
        return "sqlite:///./crm_operational.db"


settings = Settings()
