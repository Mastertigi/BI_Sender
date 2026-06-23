"""Log de execução: trilha de auditoria de cada disparo do pipeline."""
from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ExecutionStatus(str, enum.Enum):
    PENDING = "PENDING"
    REFRESHING_DATASET = "REFRESHING_DATASET"
    EXPORTING = "EXPORTING"
    DELIVERING = "DELIVERING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Correlaciona toda a cadeia de tasks de um mesmo disparo.
    correlation_id: Mapped[str] = mapped_column(String(64), index=True)

    diretoria: Mapped[str | None] = mapped_column(String(120), nullable=True)
    workspace_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    dataset_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    report_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    page_name: Mapped[str | None] = mapped_column(String(120), nullable=True)

    status: Mapped[ExecutionStatus] = mapped_column(
        Enum(ExecutionStatus, native_enum=False, length=32),
        default=ExecutionStatus.PENDING,
        index=True,
    )
    # ID do job de exportação retornado pelo Power BI (para auditoria/retry).
    powerbi_export_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ExecutionLog {self.correlation_id} {self.status}>"
