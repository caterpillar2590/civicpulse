"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-01-01 00:00:00
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

category_enum = postgresql.ENUM(
    "water", "electricity", "sanitation", "roads", "streetlights", "other",
    name="category_enum",
    create_type=False,
)
priority_enum = postgresql.ENUM("high", "normal", "low", name="priority_enum", create_type=False)
status_enum = postgresql.ENUM(
    "open", "in_progress", "resolved", "rejected", name="status_enum", create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()
    category_enum.create(bind, checkfirst=True)
    priority_enum.create(bind, checkfirst=True)
    status_enum.create(bind, checkfirst=True)

    op.create_table(
        "complaints",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("location", sa.String(200), nullable=False),
        sa.Column("reporter_contact", sa.String(200), nullable=True),
        sa.Column("category", category_enum, nullable=False),
        sa.Column("priority", priority_enum, nullable=False),
        sa.Column("status", status_enum, nullable=False, server_default="open"),
        sa.Column("ai_summary", sa.String(140), nullable=True),
        sa.Column("triaged_by", sa.String(50), nullable=False),
        sa.Column("triage_latency_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(text) >= 10 AND length(text) <= 2000", name="ck_text_len"),
        sa.CheckConstraint(
            "length(location) >= 3 AND length(location) <= 200", name="ck_location_len"
        ),
    )
    # Serves the dashboard's default filtered view: WHERE status = ? AND priority = ?
    op.create_index("ix_complaints_status_priority", "complaints", ["status", "priority"])
    # Serves ORDER BY created_at DESC pagination and any date-range stats query
    op.create_index("ix_complaints_created_at", "complaints", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_complaints_created_at", table_name="complaints")
    op.drop_index("ix_complaints_status_priority", table_name="complaints")
    op.drop_table("complaints")
    bind = op.get_bind()
    status_enum.drop(bind, checkfirst=True)
    priority_enum.drop(bind, checkfirst=True)
    category_enum.drop(bind, checkfirst=True)
