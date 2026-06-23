"""Configuração central tipada (Pydantic Settings).

Lê variáveis de ambiente / .env. Falha cedo se algo essencial faltar,
evitando que o worker suba sem credenciais válidas.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # ── Entra ID / Service Principal ──
    azure_tenant_id: str = Field(..., alias="AZURE_TENANT_ID")
    azure_client_id: str = Field(..., alias="AZURE_CLIENT_ID")
    azure_client_secret: Optional[str] = Field(None, alias="AZURE_CLIENT_SECRET")
    azure_client_cert_thumbprint: Optional[str] = Field(
        None, alias="AZURE_CLIENT_CERT_THUMBPRINT"
    )
    azure_client_cert_path: Optional[str] = Field(None, alias="AZURE_CLIENT_CERT_PATH")

    # ── Scopes ──
    powerbi_scope: str = Field(
        "https://analysis.windows.net/powerbi/api/.default", alias="POWERBI_SCOPE"
    )
    graph_scope: str = Field(
        "https://graph.microsoft.com/.default", alias="GRAPH_SCOPE"
    )

    # ── Endpoints ──
    powerbi_api_base: str = Field(
        "https://api.powerbi.com/v1.0/myorg", alias="POWERBI_API_BASE"
    )
    graph_api_base: str = Field(
        "https://graph.microsoft.com/v1.0", alias="GRAPH_API_BASE"
    )
    graph_sender_user_id: str = Field(..., alias="GRAPH_SENDER_USER_ID")

    # ── Infra ──
    database_url: str = Field(..., alias="DATABASE_URL")
    celery_broker_url: str = Field(..., alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(..., alias="CELERY_RESULT_BACKEND")

    # ── Segurança ──
    webhook_shared_secret: str = Field(..., alias="WEBHOOK_SHARED_SECRET")
    # Origens permitidas no CORS (frontend). CSV no .env.
    cors_origins_raw: str = Field(
        "http://localhost:5173,http://localhost:3000", alias="CORS_ORIGINS"
    )

    # ── Tuning de polling de exportação ──
    export_poll_initial_delay: int = Field(5, alias="EXPORT_POLL_INITIAL_DELAY")
    export_poll_max_delay: int = Field(60, alias="EXPORT_POLL_MAX_DELAY")
    export_poll_timeout: int = Field(1800, alias="EXPORT_POLL_TIMEOUT")

    @property
    def authority(self) -> str:
        return f"https://login.microsoftonline.com/{self.azure_tenant_id}"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins_raw.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
