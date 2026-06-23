"""Autenticação Service Principal (App-Only) via MSAL.

Fluxo client_credentials (server-to-server) para Power BI e Microsoft Graph.

Pontos-chave de arquitetura:
- `ConfidentialClientApplication` mantém um cache de tokens em memória e
  renova automaticamente; chamamos `acquire_token_for_client` a cada request,
  que retorna o token cacheado enquanto válido e só vai à rede quando expira.
- Um único app MSAL serve a múltiplos recursos: o recurso é definido pelo
  `scope` (`.../.default`), não por uma nova instância.
- Thread-safe: um lock protege a primeira inicialização preguiçosa, já que o
  worker Celery roda com concorrência > 1.

Gargalo previsto: em alta concorrência, o cache em memória é por processo.
Para frota de workers, considere um TokenCache serializado em Redis para
evitar N pedidos de token simultâneos ao Entra ID.
"""
from __future__ import annotations

import threading
from typing import Optional

import msal

from app.core.config import settings


class AuthError(RuntimeError):
    """Falha ao obter token do Entra ID."""


class TokenProvider:
    """Encapsula um ConfidentialClientApplication MSAL App-Only."""

    def __init__(self) -> None:
        self._app: Optional[msal.ConfidentialClientApplication] = None
        self._lock = threading.Lock()

    def _build_credential(self) -> object:
        """Prefere certificado (produção); cai para secret (dev)."""
        if settings.azure_client_cert_path and settings.azure_client_cert_thumbprint:
            with open(settings.azure_client_cert_path, "r", encoding="utf-8") as fh:
                private_key = fh.read()
            return {
                "thumbprint": settings.azure_client_cert_thumbprint,
                "private_key": private_key,
            }
        if settings.azure_client_secret:
            return settings.azure_client_secret
        raise AuthError(
            "Nenhuma credencial configurada: defina AZURE_CLIENT_SECRET ou "
            "AZURE_CLIENT_CERT_PATH + AZURE_CLIENT_CERT_THUMBPRINT."
        )

    @property
    def app(self) -> msal.ConfidentialClientApplication:
        # Inicialização preguiçosa e thread-safe (double-checked locking).
        if self._app is None:
            with self._lock:
                if self._app is None:
                    self._app = msal.ConfidentialClientApplication(
                        client_id=settings.azure_client_id,
                        authority=settings.authority,
                        client_credential=self._build_credential(),
                    )
        return self._app

    def get_token(self, scope: str) -> str:
        """Retorna um access token válido para o scope (recurso) informado.

        MSAL devolve o token do cache enquanto não expira; só busca na rede
        quando necessário. Lança AuthError em qualquer falha.
        """
        result = self.app.acquire_token_for_client(scopes=[scope])
        if not result or "access_token" not in result:
            err = (result or {}).get("error_description", "resposta vazia do MSAL")
            raise AuthError(f"Falha ao adquirir token para '{scope}': {err}")
        return result["access_token"]

    # Atalhos semânticos para os dois recursos do projeto.
    def powerbi_token(self) -> str:
        return self.get_token(settings.powerbi_scope)

    def graph_token(self) -> str:
        return self.get_token(settings.graph_scope)


# Instância única reutilizada por todo o processo (API e worker).
token_provider = TokenProvider()
