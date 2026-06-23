"""Endpoint que recebe a conclusão do Dataflow e inicia o pipeline."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import verify_webhook_token
from app.schemas.webhooks import DataflowCompletedPayload, TriggerResponse
from app.services.pipeline import DuplicateTrigger, start_pipeline

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post(
    "/dataflow-completed",
    response_model=TriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(verify_webhook_token)],
)
async def dataflow_completed(payload: DataflowCompletedPayload) -> TriggerResponse:
    """Recebe o gatilho, valida idempotência e enfileira o refresh do dataset.

    Responde 202 imediatamente: todo o trabalho pesado roda no Celery,
    evitando timeout HTTP durante a exportação dos PDFs.
    """
    try:
        correlation_id, task_id = start_pipeline(
            payload.workspace_id, payload.dataset_id, source="dataflow_webhook"
        )
    except DuplicateTrigger as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return TriggerResponse(correlation_id=correlation_id, task_id=task_id)
