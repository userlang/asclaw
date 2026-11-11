# 作者：langjunnan
# 开发时间：2025年7月23日

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_crud_plus import CRUDPlus

from app.agent.model.llm_credential import LlmUserCredential


class CRUDLlmUserCredential(CRUDPlus[LlmUserCredential]):
    @staticmethod
    def _personal_filter(user_id: int):
        """个人密钥行：user_id 匹配且 enterprise_id 为空（避免误命中企业共享行）"""
        return (
            LlmUserCredential.user_id == user_id,
            LlmUserCredential.enterprise_id.is_(None),
        )

    async def get_credential(self, db: AsyncSession, user_id: int) -> LlmUserCredential | None:
        stmt = select(LlmUserCredential).where(*self._personal_filter(user_id))
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_enterprise_credential(self, db: AsyncSession, enterprise_id: int) -> LlmUserCredential | None:
        stmt = select(LlmUserCredential).where(LlmUserCredential.enterprise_id == enterprise_id)
        result = await db.execute(stmt)
        return result.scalars().first()

    async def upsert_credential(
        self,
        db: AsyncSession,
        user_id: int,
        api_key_encrypted: str | None,
        enterprise_id: int | None = None,
        base_url: str | None = None,
        chat_model: str | None = None,
        title_model: str | None = None,
    ) -> LlmUserCredential:
        # 个人密钥按 (user_id, enterprise_id IS NULL) 定位；
        # 企业密钥按 (enterprise_id) 定位（任意成员保存都覆盖同一条，user_id 记录最后操作人）
        # api_key_encrypted 为 None 表示沿用已保存的密钥（service 层保证此时行必存在）
        if enterprise_id is not None:
            row = await self.get_enterprise_credential(db, enterprise_id)
        else:
            row = await self.get_credential(db, user_id)
        if row:
            row.user_id = user_id
            if api_key_encrypted is not None:
                row.api_key = api_key_encrypted
            row.base_url = base_url
            row.chat_model = chat_model
            row.title_model = title_model
            return row
        row = LlmUserCredential(
            user_id=user_id,
            api_key=api_key_encrypted or '',
            enterprise_id=enterprise_id,
            base_url=base_url,
            chat_model=chat_model,
            title_model=title_model,
        )
        db.add(row)
        await db.flush()
        return row

    async def delete_credential(self, db: AsyncSession, user_id: int) -> bool:
        stmt = select(LlmUserCredential).where(*self._personal_filter(user_id))
        result = await db.execute(stmt)
        row = result.scalars().first()
        if not row:
            return False
        await db.delete(row)
        return True

    async def delete_enterprise_credential(self, db: AsyncSession, enterprise_id: int) -> bool:
        row = await self.get_enterprise_credential(db, enterprise_id)
        if not row:
            return False
        await db.delete(row)
        return True


llm_credential_dao: CRUDLlmUserCredential = CRUDLlmUserCredential(LlmUserCredential)
