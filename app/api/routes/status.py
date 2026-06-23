"""Consulta de execuções, métricas do dashboard e disparo manual."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status as http_status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.execution import ExecutionLog, ExecutionStatus
from app.schemas.executions import (
    DashboardMetrics,
    ExecutionOut,
    ExecutionPage,
    ManualTriggerRequest,
    StatusCount,
)
from app.schemas.webhooks import TriggerResponse
from app.services.pipeline import DuplicateTrigger, start_pipeline

router = APIRouter(prefix="/executions", tags=["executions"])

_TERMINAL_OK = ExecutionStatus.SUCCEEDED
_TERMINAL_FAIL = ExecutionStatus.FAILED


@router.get("", response_model=ExecutionPage)
def list_executions(
    db: Session = Depends(get_db),
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
):
    """Lista execuções (mais recentes primeiro), com a última linha por correlation."""
    base = select(ExecutionLog)
    if status_filter:
        base = base.where(ExecutionLog.status == status_filter)

    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = db.scalars(
        base.order_by(ExecutionLog.id.desc()).limit(limit).offset(offset)
    ).all()
    return ExecutionPage(total=total, items=rows)


@router.get("/metrics", response_model=DashboardMetrics)
def metrics(db: Session = Depends(get_db)):
    """Agregações para o dashboard."""
    status_rows = db.execute(
        select(ExecutionLog.status, func.count())
        .group_by(ExecutionLog.status)
    ).all()
    by_status = {str(s.value if hasattr(s, "value") else s): c for s, c in status_rows}

    total = sum(by_status.values())
    succeeded = by_status.get(_TERMINAL_OK.value, 0)
    failed = by_status.get(_TERMINAL_FAIL.value, 0)
    in_progress = total - succeeded - failed
    terminal = succeeded + failed
    success_rate = round((succeeded / terminal) * 100, 1) if terminal else 0.0

    dir_rows = db.execute(
        select(ExecutionLog.diretoria, func.count())
        .where(ExecutionLog.diretoria.is_not(None))
        .group_by(ExecutionLog.diretoria)
    ).all()

    return DashboardMetrics(
        total=total,
        succeeded=succeeded,
        failed=failed,
        in_progress=in_progress,
        success_rate=success_rate,
        by_status=[StatusCount(status=k, count=v) for k, v in by_status.items()],
        by_diretoria=[{"diretoria": d, "count": c} for d, c in dir_rows],
    )


@router.post("/trigger", response_model=TriggerResponse, status_code=202)
def manual_trigger(payload: ManualTriggerRequest):
    """Dispara o pipeline manualmente (mesma cadeia do webhook do Dataflow)."""
    try:
        correlation_id, task_id = start_pipeline(
            payload.workspace_id, payload.dataset_id, source="manual"
        )
    except DuplicateTrigger as exc:
        raise HTTPException(status_code=http_status.HTTP_409_CONFLICT, detail=str(exc))
    return TriggerResponse(correlation_id=correlation_id, task_id=task_id)


@router.get("/{correlation_id}", response_model=list[ExecutionOut])
def get_execution(correlation_id: str, db: Session = Depends(get_db)):
    rows = db.scalars(
        select(ExecutionLog)
        .where(ExecutionLog.correlation_id == correlation_id)
        .order_by(ExecutionLog.id)
    ).all()
    if not rows:
        raise HTTPException(status_code=404, detail="correlation_id não encontrado.")
    return rows
