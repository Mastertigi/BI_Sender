"""Serviço de orquestração: ponto único para iniciar o pipeline.

Centraliza a lógica usada tanto pelo webhook do Dataflow quanto pelo disparo
manual: idempotência (lock no Redis), criação do log de auditoria e enfileiramento
da primeira task Celery.
"""
from __future__ import annotations

import logging
import uuid

from app.core.idempotency import acquire_trigger_lock
from app.db.session import SessionLocal
from app.models.execution import ExecutionLog, ExecutionStatus
from app.workers.tasks import refresh_dataset_task

logger = logging.getLogger("bi_notify")


class DuplicateTrigger(Exception):
    """Já existe um disparo em andamento para o mesmo dataset."""


def start_pipeline(
    workspace_id: str, dataset_id: str, *, source: str
) -> tuple[str, str]:
    """Inicia o pipeline. Retorna (correlation_id, task_id).

    Lança DuplicateTrigger se houver disparo recente para o mesmo dataset
    (proteção contra eventos duplicados do Dataflow).
    """
    if not acquire_trigger_lock(workspace_id, dataset_id):
        raise DuplicateTrigger(
            f"Disparo já em andamento para dataset {dataset_id}."
        )

    correlation_id = uuid.uuid4().hex
    with SessionLocal() as db:
        db.add(
            ExecutionLog(
                correlation_id=correlation_id,
                status=ExecutionStatus.PENDING,
                workspace_id=workspace_id,
                dataset_id=dataset_id,
                payload={"source": source},
            )
        )
        db.commit()

    async_result = refresh_dataset_task.delay(
        correlation_id, workspace_id, dataset_id
    )
    logger.info(
        "Pipeline iniciado",
        extra={"correlation_id": correlation_id},
    )
    return correlation_id, async_result.id
