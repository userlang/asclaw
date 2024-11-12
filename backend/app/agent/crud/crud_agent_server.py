# 作者：langjunnan
# 开发时间：2025年7月23日

from app.agent.model import AgentServer
from sqlalchemy import Select, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload, selectinload
from sqlalchemy_crud_plus import CRUDPlus


class CRUDAgentServer(CRUDPlus[AgentServer]):
    async def get_by_user_and_name(
        self, db: AsyncSession, name: str, user_id: int, is_public: bool | None = None
    ) -> AgentServer | None:
        filters: dict = {'name': name, 'user_id': user_id}
        if is_public is not None:
            filters['is_public'] = 1 if is_public else 0
        return await self.select_model_by_column(
            db,
            load_strategies={'user': 'selectinload', 'category': 'selectinload'},
            **filters,
        )

    async def get_by_user_and_name_visible(
        self,
        db: AsyncSession,
        name: str,
        owner_user_id: int,
        viewer_user_id: int,
        viewer_enterprise_id: int | None,
    ) -> AgentServer | None:
        """按可见性取 agent：公开 / 本人所有 / 同企业私有，其余视为不存在"""
        visible = or_(
            self.model.is_public.is_(True),
            self.model.user_id == viewer_user_id,
        )
        if viewer_enterprise_id is not None:
            visible |= self.model.enterprise_id == viewer_enterprise_id
        stmt = (
            select(self.model)
            .where(self.model.name == name, self.model.user_id == owner_user_id, visible)
            .options(selectinload(self.model.user), selectinload(self.model.category))
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_list(
        self,
        keyword: str | None = None,
        category_id: int | None = None,
        viewer_user_id: int | None = None,
        viewer_enterprise_id: int | None = None,
    ) -> Select:
        """广场列表：公开 + 本人 + 本企业私有"""
        visible = self.model.is_public.is_(True)
        if viewer_user_id is not None:
            visible |= self.model.user_id == viewer_user_id
        if viewer_enterprise_id is not None:
            visible |= self.model.enterprise_id == viewer_enterprise_id
        whereclause = [visible]
        if category_id:
            whereclause.append(self.model.category_id == category_id)
        if keyword:
            whereclause.append(self.model.title.like(f'%{keyword}%'))
        return await self.select_order(
            'updated_time',
            'desc',
            *whereclause,
            load_options=[
                noload(self.model.category),
                selectinload(self.model.user),
            ],
        )


agent_server_dao: CRUDAgentServer = CRUDAgentServer(AgentServer)
