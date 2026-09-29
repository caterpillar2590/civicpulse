from __future__ import annotations

from fastapi import APIRouter

from app.config import get_settings
from app.models.schemas import ProvidersMeta
from app.services.triage_service import get_recent_outcomes

router = APIRouter(prefix="/api/meta", tags=["meta"])


@router.get("/providers", response_model=ProvidersMeta)
async def providers_meta():
    settings = get_settings()
    return ProvidersMeta(
        active_provider=settings.triage_provider,
        recent_outcomes=get_recent_outcomes(),
    )
