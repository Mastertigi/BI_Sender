"""Regras de Roteamento: Diretoria -> Report/Página -> Destinatários.

Cada linha define como uma página exportada de um relatório deve ser
distribuída: para quem mandar por e-mail e em qual canal do Teams notificar,
e qual identidade RLS aplicar na exportação.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class RoutingRule(Base):
    __tablename__ = "routing_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Negócio
    diretoria: Mapped[str] = mapped_column(String(120), index=True)

    # Power BI
    workspace_id: Mapped[str] = mapped_column(String(64), index=True)
    dataset_id: Mapped[str] = mapped_column(String(64), index=True)
    report_id: Mapped[str] = mapped_column(String(64), index=True)
    # Nome da página (objectId/pageName retornado por GetPages) a exportar.
    page_name: Mapped[str] = mapped_column(String(120))
    report_display_name: Mapped[str] = mapped_column(String(200))

    # RLS aplicado na exportação (effectiveIdentity). Opcional.
    rls_username: Mapped[str | None] = mapped_column(String(200), nullable=True)
    rls_roles: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    # Filtros por nível de relatório (sintaxe de URL filter) opcionais.
    report_level_filters: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Entrega
    email_to: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    email_cc: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    teams_team_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    teams_channel_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Anexar PDF (true) ou enviar apenas link (false).
    attach_pdf: Mapped[bool] = mapped_column(Boolean, default=True)

    # Metadados livres (ex.: locale, formatos extras).
    extra: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<RoutingRule {self.diretoria} report={self.report_id} page={self.page_name}>"
