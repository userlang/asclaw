# 作者：langjunnan
# 开发时间：2025年7月23日

from app.admin.crud.crud_admin_skill_category import skill_admin_category_dao
from app.admin.schema.category import AddCategoryParam
from app.skills.service.skill_service import SkillError
from common.exception import errors
from database.db import async_db_session
from fastapi import Request
from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession


class SkillAdminCategoryService:
    @staticmethod
    async def get_list(is_recommend: int) -> Select:
        return await skill_admin_category_dao.get_list(is_recommend)

    @staticmethod
    async def create(*, request: Request, obj: AddCategoryParam) -> None:
        async with async_db_session.begin() as db:
            if await skill_admin_category_dao.get_category_by_name(db, obj.name):
                raise errors.ConflictError(msg='分类名称已存在')
            await skill_admin_category_dao.add(db, obj)

    @staticmethod
    async def delete(db: AsyncSession, category_id: int) -> int:
        """删除分类：分类下仍有 skill 时拒绝删除（先移走或清空引用）"""
        category = await skill_admin_category_dao.get_skill_category(db, category_id)
        if not category:
            # NotFoundError 不在全局异常处理器树里，会变成无信息的 500；用业务异常
            raise SkillError(code=404, msg='分类不存在')
        if await skill_admin_category_dao.count_skills(db, category_id) > 0:
            raise SkillError(code=400, msg='该分类下仍有 skill，请先移出后再删除')
        return await skill_admin_category_dao.delete_model(db, category_id)


skill_admin_category_service: SkillAdminCategoryService = SkillAdminCategoryService()
