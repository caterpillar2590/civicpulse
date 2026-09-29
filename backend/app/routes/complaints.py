from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.schemas import (
    Category,
    ComplaintCreate,
    ComplaintListOut,
    ComplaintOut,
    Priority,
    Status,
    StatusUpdate,
)
from app.providers.rate_limiter import check_rate_limit
from app.repositories.complaint_repository import ComplaintRepository
from app.services.complaint_service import InvalidTransitionError, create_complaint, transition_status
from app.config import get_settings

router = APIRouter(prefix="/api/complaints", tags=["complaints"])


@router.post("", response_model=ComplaintOut, status_code=201)
async def submit_complaint(request: Request, payload: ComplaintCreate, session: AsyncSession = Depends(get_db)):
    settings = get_settings()
    client_ip = request.client.host if request.client else "unknown"
    allowed, retry_after = await check_rate_limit(
        client_ip, settings.rate_limit_window_seconds, settings.rate_limit_max_requests
    )
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Too many complaints submitted from this address. Please slow down.",
            headers={"Retry-After": str(retry_after)},
        )

    complaint = await create_complaint(session, payload)
    return ComplaintOut.model_validate(complaint)


@router.get("/{complaint_id}", response_model=ComplaintOut)
async def get_complaint(complaint_id: uuid.UUID, session: AsyncSession = Depends(get_db)):
    repo = ComplaintRepository(session)
    complaint = await repo.get_by_id(complaint_id)
    if complaint is None:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return ComplaintOut.model_validate(complaint)


@router.get("", response_model=ComplaintListOut)
async def list_complaints(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    category: Category | None = None,
    priority: Priority | None = None,
    status: Status | None = None,
    session: AsyncSession = Depends(get_db),
):
    repo = ComplaintRepository(session)
    rows, total = await repo.list(page, page_size, category, priority, status)
    return ComplaintListOut(
        items=[ComplaintOut.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.patch("/{complaint_id}/status", response_model=ComplaintOut)
async def update_status(complaint_id: uuid.UUID, payload: StatusUpdate, session: AsyncSession = Depends(get_db)):
    repo = ComplaintRepository(session)
    complaint = await repo.get_by_id(complaint_id)
    if complaint is None:
        raise HTTPException(status_code=404, detail="Complaint not found")

    try:
        updated = await transition_status(session, complaint, payload.status)
    except InvalidTransitionError as exc:
        raise HTTPException(
            status_code=409,
            detail=f"Invalid transition: cannot move from '{exc.current.value}' to '{exc.attempted.value}'",
        ) from exc

    return ComplaintOut.model_validate(updated)
