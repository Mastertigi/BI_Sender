"""initial schema: routing_rules + execution_logs

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-23
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "routing_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("diretoria", sa.String(length=120), nullable=False, index=True),
        sa.Column("workspace_id", sa.String(length=64), nullable=False, index=True),
        sa.Column("dataset_id", sa.String(length=64), nullable=False, index=True),
        sa.Column("report_id", sa.String(length=64), nullable=False, index=True),
        sa.Column("page_name", sa.String(length=120), nullable=False),
        sa.Column("report_display_name", sa.String(length=200), nullable=False),
        sa.Column("rls_username", sa.String(length=200), nullable=True),
        sa.Column("rls_roles", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("report_level_filters", sa.String(length=500), nullable=True),
        sa.Column("email_to", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("email_cc", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("teams_team_id", sa.String(length=64), nullable=True),
        sa.Column("teams_channel_id", sa.String(length=64), nullable=True),
        sa.Column("attach_pdf", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("extra", postgresql.JSONB(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true(), index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "execution_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("correlation_id", sa.String(length=64), nullable=False, index=True),
        sa.Column("diretoria", sa.String(length=120), nullable=True),
        sa.Column("workspace_id", sa.String(length=64), nullable=True),
        sa.Column("dataset_id", sa.String(length=64), nullable=True),
        sa.Column("report_id", sa.String(length=64), nullable=True),
        sa.Column("page_name", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, index=True, server_default="PENDING"),
        sa.Column("powerbi_export_id", sa.String(length=64), nullable=True),
        sa.Column("error_detail", sa.Text(), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("execution_logs")
    op.drop_table("routing_rules")
