from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.services.stats_service import get_stats

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("")
async def stats(response: Response, session: AsyncSession = Depends(get_db)):
    data, hit = await get_stats(session)
    response.headers["X-Cache"] = "HIT" if hit else "MISS"
    return data
