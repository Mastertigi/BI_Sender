"""Idempotência e health usando Redis.

O disparo do pipeline é protegido contra duplicatas: dois eventos do mesmo
dataset numa janela curta não geram dois refreshes concorrentes. Usa SET NX EX
(atômico). Degrada com segurança: se o Redis estiver indisponível, libera o
disparo (prefere processar a bloquear).
"""
from __future__ import annotations

import logging

import redis

from app.core.config import settings

logger = logging.getLogger(__name__)

# Conexão preguiçosa, reutilizada (pool interno do cliente redis-py).
_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis.from_url(
            settings.celery_broker_url, decode_responses=True
        )
    return _client


def acquire_trigger_lock(
    workspace_id: str, dataset_id: str, ttl_seconds: int = 300
) -> bool:
    """Tenta adquirir lock do disparo. True = pode prosseguir.

    Em falha de Redis, retorna True (fail-open) e loga o aviso.
    """
    key = f"bi_notify:trigger:{workspace_id}:{dataset_id}"
    try:
        return bool(get_redis().set(key, "1", nx=True, ex=ttl_seconds))
    except redis.RedisError as exc:  # pragma: no cover - depende de infra
        logger.warning("Redis indisponível para idempotência: %s", exc)
        return True


def ping_redis() -> bool:
    try:
        return bool(get_redis().ping())
    except redis.RedisError:
        return False
