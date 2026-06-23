"""Schemas Pydantic de entrada/saída da API."""
from __future__ import annotations

from pydantic import BaseModel, Field


class DataflowCompletedPayload(BaseModel):
    """Disparado quando a atualização de um Dataflow conclui.

    O gatilho (Power Automate mínimo, Fabric pipeline ou monitor próprio)
    chama o webhook informando qual dataset deve ser atualizado em seguida.
    """

    workspace_id: str = Field(..., description="ID do workspace (group) do Power BI")
    dataset_id: str = Field(..., description="ID do modelo semântico a atualizar")
    dataflow_id: str | None = Field(None, description="ID do dataflow concluído")


class TriggerResponse(BaseModel):
    correlation_id: str
    task_id: str
    status: str = "accepted"


class ExecutionLogOut(BaseModel):
    correlation_id: str
    status: str
    diretoria: str | None = None
    report_id: str | None = None
    page_name: str | None = None
    powerbi_export_id: str | None = None
    error_detail: str | None = None

    model_config = {"from_attributes": True}
