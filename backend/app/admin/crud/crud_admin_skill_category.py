# 作者：langjunnan
# 开发时间：2025年7月23日

from app.admin.schema.category import AddCategoryParam
from app.skills.model import AgentSkill, SkillCategory
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_crud_plus import CRUDPlus


class CRUDSkillAdminCategory(CRUDPlus[SkillCategory]):
    async def get_skill_category(self, db: AsyncSession, pk: int) -> SkillCategory:
        return await self.select_model(db, pk)

    async def get_list(self, is_recommend: int | None = None) -> Select:
        filters = {}
        if is_recommend is not None and is_recommend >= 0:
            filters['is_recommend'] = bool(is_recommend)
        return await self.select_order('id', 'asc', **filters)

    async def add(self, db: AsyncSession, obj: AddCategoryParam) -> None:
        data = obj.model_dump()
        data['is_recommend'] = bool(data['is_recommend'])
        new_category = self.model(**data)
        db.add(new_category)

    async def get_category_by_name(self, db: AsyncSession, name: str) -> SkillCategory:
        return await self.select_model_by_column(db, name=name)

    async def count_skills(self, db: AsyncSession, category_id: int) -> int:
        """该分类下关联的 skill 数量（删除前校验用）"""
        result = await db.execute(
            select(func.count(AgentSkill.id)).where(AgentSkill.category_id == category_id)
        )
        return result.scalar_one()


skill_admin_category_dao: CRUDSkillAdminCategory = CRUDSkillAdminCategory(SkillCategory)
