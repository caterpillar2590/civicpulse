from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.complaint import Complaint
from app.models.schemas import Category, Priority, Status


class ComplaintRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, complaint: Complaint) -> Complaint:
        self.session.add(complaint)
        await self.session.commit()
        await self.session.refresh(complaint)
        return complaint

    async def get_by_id(self, complaint_id: uuid.UUID) -> Complaint | None:
        return await self.session.get(Complaint, complaint_id)

    async def list(
        self,
        page: int,
        page_size: int,
        category: Category | None = None,
        priority: Priority | None = None,
        status: Status | None = None,
    ) -> tuple[list[Complaint], int]:
        stmt = select(Complaint)
        count_stmt = select(func.count()).select_from(Complaint)

        if category is not None:
            stmt = stmt.where(Complaint.category == category)
            count_stmt = count_stmt.where(Complaint.category == category)
        if priority is not None:
            stmt = stmt.where(Complaint.priority == priority)
            count_stmt = count_stmt.where(Complaint.priority == priority)
        if status is not None:
            stmt = stmt.where(Complaint.status == status)
            count_stmt = count_stmt.where(Complaint.status == status)

        stmt = stmt.order_by(Complaint.created_at.desc()).offset((page - 1) * page_size).limit(page_size)

        total = (await self.session.execute(count_stmt)).scalar_one()
        rows = (await self.session.execute(stmt)).scalars().all()
        return list(rows), total

    async def update_status(self, complaint: Complaint, new_status: Status) -> Complaint:
        complaint.status = new_status
        await self.session.commit()
        await self.session.refresh(complaint)
        return complaint

    async def stats(self) -> dict:
        by_category_stmt = select(Complaint.category, func.count()).group_by(Complaint.category)
        by_priority_stmt = select(Complaint.priority, func.count()).group_by(Complaint.priority)
        total_stmt = select(func.count()).select_from(Complaint)

        by_category = dict((r[0].value, r[1]) for r in (await self.session.execute(by_category_stmt)).all())
        by_priority = dict((r[0].value, r[1]) for r in (await self.session.execute(by_priority_stmt)).all())
        total = (await self.session.execute(total_stmt)).scalar_one()

        return {"total": total, "by_category": by_category, "by_priority": by_priority}
