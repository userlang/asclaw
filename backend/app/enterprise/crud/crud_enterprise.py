from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_crud_plus import CRUDPlus

from app.enterprise.model.enterprise import Enterprise


class CRUDEnterprise(CRUDPlus[Enterprise]):
    async def get_by_id(self, db: AsyncSession, pk: int) -> Enterprise | None:
        return await db.get(Enterprise, pk)

    async def get_by_username(self, db: AsyncSession, username: str) -> Enterprise | None:
        return await self.select_model_by_column(db, username=username)

    async def get_select(self, status: int | None = None, keyword: str | None = None) -> select:
        filters = {}
        if status is not None:
            filters['status'] = status
        if keyword:
            filters['name__like'] = f'%{keyword}%'
        return await self.select_order('created_time', 'desc', **filters)

    async def create(self, db: AsyncSession, enterprise: Enterprise) -> Enterprise:
        db.add(enterprise)
        await db.flush()
        return enterprise

    async def delete_batch(self, db: AsyncSession, pks: list[int]) -> int:
        result = await db.execute(delete(Enterprise).where(Enterprise.id.in_(pks)))
        return result.rowcount


enterprise_dao: CRUDEnterprise = CRUDEnterprise(Enterprise)
