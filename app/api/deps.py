"""Dependências de segurança da API interna."""
from __future__ import annotations

import hmac

from fastapi import Header, HTTPException, status

from app.core.config import settings


async def verify_webhook_token(
    x_webhook_token: str = Header(..., alias="X-Webhook-Token"),
) -> None:
    """Valida o segredo compartilhado em tempo constante (anti timing-attack)."""
    if not hmac.compare_digest(x_webhook_token, settings.webhook_shared_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido."
        )
