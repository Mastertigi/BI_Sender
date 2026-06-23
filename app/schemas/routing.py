"""Schemas Pydantic para CRUD de Regras de Roteamento."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class RoutingRuleBase(BaseModel):
    diretoria: str = Field(..., max_length=120)
    workspace_id: str = Field(..., max_length=64)
    dataset_id: str = Field(..., max_length=64)
    report_id: str = Field(..., max_length=64)
    page_name: str = Field(..., max_length=120)
    report_display_name: str = Field(..., max_length=200)

    rls_username: Optional[str] = None
    rls_roles: Optional[list[str]] = None
    report_level_filters: Optional[str] = Field(None, max_length=500)

    email_to: list[EmailStr] = Field(default_factory=list)
    email_cc: Optional[list[EmailStr]] = None
    teams_team_id: Optional[str] = None
    teams_channel_id: Optional[str] = None
    attach_pdf: bool = True

    active: bool = True


class RoutingRuleCreate(RoutingRuleBase):
    pass


class RoutingRuleUpdate(BaseModel):
    """Atualização parcial — todos os campos opcionais."""

    diretoria: Optional[str] = None
    workspace_id: Optional[str] = None
    dataset_id: Optional[str] = None
    report_id: Optional[str] = None
    page_name: Optional[str] = None
    report_display_name: Optional[str] = None
    rls_username: Optional[str] = None
    rls_roles: Optional[list[str]] = None
    report_level_filters: Optional[str] = None
    email_to: Optional[list[EmailStr]] = None
    email_cc: Optional[list[EmailStr]] = None
    teams_team_id: Optional[str] = None
    teams_channel_id: Optional[str] = None
    attach_pdf: Optional[bool] = None
    active: Optional[bool] = None


class RoutingRuleOut(RoutingRuleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
