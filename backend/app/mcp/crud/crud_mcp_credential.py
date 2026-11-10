# 作者：langjunnan
# 开发时间：2025年7月23日

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_crud_plus import CRUDPlus

from app.mcp.model.credential import McpUserCredential


class CRUDMcpUserCredential(CRUDPlus[McpUserCredential]):
    @staticmethod
    def _personal_filter(user_id: int, mcp_server_id: int):
        """个人凭证行：user_id 匹配且 enterprise_id 为空（避免误命中企业共享行）"""
        return (
            McpUserCredential.user_id == user_id,
            McpUserCredential.mcp_server_id == mcp_server_id,
            McpUserCredential.enterprise_id.is_(None),
        )

    async def get_credential(self, db: AsyncSession, user_id: int, mcp_server_id: int) -> McpUserCredential | None:
        stmt = select(McpUserCredential).where(*self._personal_filter(user_id, mcp_server_id))
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_enterprise_credential(
        self, db: AsyncSession, enterprise_id: int, mcp_server_id: int
    ) -> McpUserCredential | None:
        return await self.select_model_by_column(db, enterprise_id=enterprise_id, mcp_server_id=mcp_server_id)

    async def upsert_credential(
        self,
        db: AsyncSession,
        user_id: int,
        mcp_server_id: int,
        credential_encrypted: str,
        enterprise_id: int | None = None,
    ) -> McpUserCredential:
        # 个人凭证按 (user_id, mcp_server_id, enterprise_id IS NULL) 定位；
        # 企业凭证按 (enterprise_id, mcp_server_id) 定位（任意成员保存都覆盖同一条，user_id 记录最后操作人）
        if enterprise_id is not None:
            row = await self.get_enterprise_credential(db, enterprise_id, mcp_server_id)
        else:
            row = await self.get_credential(db, user_id, mcp_server_id)
        if row:
            row.user_id = user_id
            row.credential = credential_encrypted
            return row
        row = McpUserCredential(
            user_id=user_id,
            mcp_server_id=mcp_server_id,
            enterprise_id=enterprise_id,
            credential=credential_encrypted,
        )
        db.add(row)
        await db.flush()
        return row

    async def delete_credential(self, db: AsyncSession, user_id: int, mcp_server_id: int) -> bool:
        stmt = select(McpUserCredential).where(*self._personal_filter(user_id, mcp_server_id))
        result = await db.execute(stmt)
        row = result.scalars().first()
        if not row:
            return False
        await db.delete(row)
        return True

    async def delete_enterprise_credential(self, db: AsyncSession, enterprise_id: int, mcp_server_id: int) -> bool:
        row = await self.get_enterprise_credential(db, enterprise_id, mcp_server_id)
        if not row:
            return False
        await db.delete(row)
        return True

    async def get_user_credential_server_ids(
        self, db: AsyncSession, user_id: int, enterprise_id: int | None = None
    ) -> list[int]:
        """用户已配置凭证的 MCP server id 列表（个人 + 其企业共享的）"""
        conds = [McpUserCredential.user_id == user_id]
        if enterprise_id is not None:
            conds.append(McpUserCredential.enterprise_id == enterprise_id)
        stmt = select(McpUserCredential.mcp_server_id).where(or_(*conds))
        result = await db.execute(stmt)
        return list(result.scalars().all())
