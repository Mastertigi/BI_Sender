"""Instância Celery + configuração.

acks_late + reject_on_worker_lost garantem que tasks longas (exportação de PDF)
não sejam perdidas em caso de crash do worker. Limitamos prefetch a 1 para que
um worker ocupado num polling longo não segure outras tasks na fila.
"""
from __future__ import annotations

from celery import Celery
from celery.signals import setup_logging as celery_setup_logging

from app.core.config import settings
from app.core.logging import setup_logging

celery = Celery(
    "bi_notify",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks"],
)

celery.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="America/Sao_Paulo",
    enable_utc=True,
    # Limite de segurança: nenhuma task deve passar de 1h.
    task_time_limit=3600,
    task_soft_time_limit=3300,
)


@celery_setup_logging.connect
def _configure_logging(**_: object) -> None:
    """Impede o Celery de sobrescrever nosso logger JSON."""
    setup_logging()
