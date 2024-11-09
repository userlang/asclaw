# 作者：langjunnan
# 开发时间：2025年7月23日

from app.skills.model import SkillContent
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_crud_plus import CRUDPlus


class CRUDSkillContent(CRUDPlus[SkillContent]):
    async def get_by_skill(self, db: AsyncSession, skill_id: int) -> list[SkillContent]:
        result = await db.execute(
            select(self.model).where(self.model.skill_id == skill_id).order_by(self.model.file_path)
        )
        return list(result.scalars().all())

    async def delete_by_skill(self, db: AsyncSession, skill_id: int) -> None:
        await db.execute(delete(self.model).where(self.model.skill_id == skill_id))


skill_content_dao: CRUDSkillContent = CRUDSkillContent(SkillContent)
