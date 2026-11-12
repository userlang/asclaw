# 作者：langjunnan
# 开发时间：2025年7月23日

from app.skills.model import AgentSkill
from sqlalchemy import Select, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload, selectinload
from sqlalchemy_crud_plus import CRUDPlus


class CRUDSkill(CRUDPlus[AgentSkill]):
    async def get_skill_by_user(self, db: AsyncSession, skill_name: str, user_id: int) -> AgentSkill | None:
        return await self.select_model_by_column(
            db,
            name=skill_name,
            user_id=user_id,
            load_strategies={'user': 'selectinload', 'category': 'selectinload'},
        )

    async def get_public_skill_by_user(self, db: AsyncSession, skill_name: str, user_id: int) -> AgentSkill | None:
        return await self.select_model_by_column(
            db,
            name=skill_name,
            user_id=user_id,
            is_public=1,
            load_strategies={'user': 'selectinload', 'category': 'selectinload'},
        )

    async def get_skill_visible_to(
        self,
        db: AsyncSession,
        skill_name: str,
        owner_user_id: int,
        viewer_user_id: int,
        viewer_enterprise_id: int | None,
    ) -> AgentSkill | None:
        """按可见性取 skill：公开 / 本人所有 / 同企业私有，其余视为不存在"""
        visible = or_(
            self.model.is_public.is_(True),
            self.model.user_id == viewer_user_id,
        )
        if viewer_enterprise_id is not None:
            visible |= self.model.enterprise_id == viewer_enterprise_id
        stmt = (
            select(self.model)
            .where(self.model.name == skill_name, self.model.user_id == owner_user_id, visible)
            .options(selectinload(self.model.user), selectinload(self.model.category))
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_by_name_and_user(self, db: AsyncSession, name: str, user_id: int) -> AgentSkill | None:
        """name 在同一用户下唯一（详情 URL 是 /skills/{owner}/{name}），发布前查重"""
        return await self.select_model_by_column(db, name=name, user_id=user_id)

    async def get_list(
        self,
        keyword: str | None = None,
        category_id: int | None = None,
        viewer_user_id: int | None = None,
        viewer_enterprise_id: int | None = None,
    ) -> Select:
        """广场列表：公开 + 本人 + 本企业私有（已发布 status=1）"""
        visible = self.model.is_public.is_(True)
        if viewer_user_id is not None:
            visible |= self.model.user_id == viewer_user_id
        if viewer_enterprise_id is not None:
            visible |= self.model.enterprise_id == viewer_enterprise_id
        whereclause = [visible, self.model.status == 1]
        if category_id:
            whereclause.append(self.model.category_id == category_id)
        if keyword:
            whereclause.append(self.model.name.like(f'%{keyword}%'))
        return await self.select_order(
            'updated_time',
            'desc',
            *whereclause,
            load_options=[
                noload(self.model.category),
                selectinload(self.model.user),
            ],
        )

    async def get_my_skills(self, user_id: int) -> Select:
        return await self.select_order(
            'updated_time',
            'desc',
            load_options=[
                noload(self.model.category),
                selectinload(self.model.user),
            ],
            user_id=user_id,
        )


skill_dao: CRUDSkill = CRUDSkill(AgentSkill)
