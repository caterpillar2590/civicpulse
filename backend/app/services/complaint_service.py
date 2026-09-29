from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.complaint import Complaint
from app.models.schemas import VALID_TRANSITIONS, ComplaintCreate, Status
from app.providers.cache import invalidate_stats_cache
from app.repositories.complaint_repository import ComplaintRepository
from app.services.triage_service import triage_complaint


class InvalidTransitionError(Exception):
    def __init__(self, current: Status, attempted: Status):
        self.current = current
        self.attempted = attempted
        super().__init__(f"Cannot transition from {current.value} to {attempted.value}")


async def create_complaint(session: AsyncSession, payload: ComplaintCreate) -> Complaint:
    repo = ComplaintRepository(session)
    new_id = uuid.uuid4()

    outcome = await triage_complaint(payload.text, payload.location, str(new_id))

    complaint = Complaint(
        id=new_id,
        text=payload.text,
        location=payload.location,
        reporter_contact=payload.reporter_contact,
        category=outcome.result.category,
        priority=outcome.result.priority,
        status=Status.open,
        ai_summary=outcome.result.summary,
        triaged_by=outcome.triaged_by,
        triage_latency_ms=outcome.latency_ms,
    )
    saved = await repo.create(complaint)
    await invalidate_stats_cache()
    return saved


async def transition_status(session: AsyncSession, complaint: Complaint, new_status: Status) -> Complaint:
    allowed = VALID_TRANSITIONS.get(complaint.status, set())
    if new_status not in allowed:
        raise InvalidTransitionError(complaint.status, new_status)
    repo = ComplaintRepository(session)
    return await repo.update_status(complaint, new_status)
