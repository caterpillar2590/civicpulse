from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, Enum, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.models.schemas import Category, Priority, Status


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    reporter_contact: Mapped[str | None] = mapped_column(String(200), nullable=True)

    category: Mapped[Category] = mapped_column(
        Enum(Category, name="category_enum", native_enum=True), nullable=False
    )
    priority: Mapped[Priority] = mapped_column(
        Enum(Priority, name="priority_enum", native_enum=True), nullable=False
    )
    status: Mapped[Status] = mapped_column(
        Enum(Status, name="status_enum", native_enum=True),
        nullable=False,
        default=Status.open,
    )

    ai_summary: Mapped[str | None] = mapped_column(String(140), nullable=True)
    triaged_by: Mapped[str] = mapped_column(String(50), nullable=False)
    triage_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    __table_args__ = (
        CheckConstraint("length(text) >= 10 AND length(text) <= 2000", name="ck_text_len"),
        CheckConstraint("length(location) >= 3 AND length(location) <= 200", name="ck_location_len"),
        # Serves GET /api/complaints filtered by status+priority (dashboard default view)
        Index("ix_complaints_status_priority", "status", "priority"),
        # Serves GET /api/complaints ordered by recency / date-range stats queries
        Index("ix_complaints_created_at", "created_at"),
    )
