"""Schemas de execução: listagem, métricas e disparo manual."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ExecutionOut(BaseModel):
    id: int
    correlation_id: str
    status: str
    diretoria: Optional[str] = None
    workspace_id: Optional[str] = None
    dataset_id: Optional[str] = None
    report_id: Optional[str] = None
    page_name: Optional[str] = None
    powerbi_export_id: Optional[str] = None
    error_detail: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExecutionPage(BaseModel):
    total: int
    items: list[ExecutionOut]


class StatusCount(BaseModel):
    status: str
    count: int


class DashboardMetrics(BaseModel):
    total: int
    succeeded: int
    failed: int
    in_progress: int
    success_rate: float = Field(..., description="0..100")
    by_status: list[StatusCount]
    by_diretoria: list[dict]


class ManualTriggerRequest(BaseModel):
    workspace_id: str
    dataset_id: str
