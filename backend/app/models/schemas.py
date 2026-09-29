"""Shared enums and Pydantic schemas.

These are used BOTH to validate HTTP input/output (routes/) AND to validate
LLM triage output (providers/triage/). One mental model, two uses.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class Category(str, enum.Enum):
    water = "water"
    electricity = "electricity"
    sanitation = "sanitation"
    roads = "roads"
    streetlights = "streetlights"
    other = "other"


class Priority(str, enum.Enum):
    high = "high"
    normal = "normal"
    low = "low"


class Status(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    rejected = "rejected"


# --- Explicit state machine (Backend §2.2) -------------------------------
# open -> in_progress | rejected
# in_progress -> resolved | rejected
# resolved, rejected are terminal.
VALID_TRANSITIONS: dict[Status, set[Status]] = {
    Status.open: {Status.in_progress, Status.rejected},
    Status.in_progress: {Status.resolved, Status.rejected},
    Status.resolved: set(),
    Status.rejected: set(),
}


class TriageResult(BaseModel):
    """The contract every TriageProvider must satisfy (validated, not trusted)."""

    category: Category
    priority: Priority
    summary: str = Field(max_length=140)
    confidence: float = Field(ge=0.0, le=1.0)

    @field_validator("summary")
    @classmethod
    def strip_summary(cls, v: str) -> str:
        v = v.strip()
        if len(v) > 140:
            v = v[:140].rstrip()
        return v


class ComplaintCreate(BaseModel):
    text: str = Field(min_length=10, max_length=2000)
    location: str = Field(min_length=3, max_length=200)
    reporter_contact: str | None = Field(default=None, max_length=200)


class ComplaintOut(BaseModel):
    id: uuid.UUID
    text: str
    location: str
    reporter_contact: str | None
    category: Category
    priority: Priority
    status: Status
    ai_summary: str | None
    triaged_by: str
    triage_latency_ms: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ComplaintListOut(BaseModel):
    items: list[ComplaintOut]
    total: int
    page: int
    page_size: int


class StatusUpdate(BaseModel):
    status: Status


class FieldError(BaseModel):
    field: str
    message: str


class ValidationErrorBody(BaseModel):
    detail: str
    errors: list[FieldError] = []


class ProviderOutcome(BaseModel):
    provider: str
    latency_ms: int
    fallback: bool
    timestamp: datetime


class ProvidersMeta(BaseModel):
    active_provider: str
    recent_outcomes: list[ProviderOutcome]
