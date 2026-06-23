"""Infra HTTP compartilhada: retry com backoff para erros transientes.

Separa duas classes de falha:
- **Transiente** (timeout, erro de conexão, 5xx): retry automático com backoff
  exponencial + jitter via tenacity. Resolvido aqui, sem poluir o chamador.
- **Rate limit (429)** e **erros de negócio (4xx)**: propagados para o chamador
  decidir (no nosso caso, o worker Celery respeita o `Retry-After`).
"""
from __future__ import annotations

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)


class TransientHTTPError(Exception):
    """Erro HTTP recuperável (5xx) — elegível para retry automático."""


# Decorator reutilizável para chamadas idempotentes de leitura/polling.
transient_retry = retry(
    retry=retry_if_exception_type((httpx.TransportError, TransientHTTPError)),
    wait=wait_exponential_jitter(initial=1, max=20),
    stop=stop_after_attempt(4),
    reraise=True,
)


def raise_for_transient(resp: httpx.Response) -> None:
    """Converte 5xx em TransientHTTPError (para acionar o retry)."""
    if resp.status_code >= 500:
        raise TransientHTTPError(
            f"{resp.request.method} {resp.request.url} -> {resp.status_code}"
        )
