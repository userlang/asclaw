#!/usr/bin/env python3
# 作者：langjunnan
# 开发时间：2025年7月23日

# -*- coding: utf-8 -*-
from __future__ import annotations

from common.model import Base, id_key
from sqlalchemy import BigInteger, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column


class McpUserCredential(Base):
    """用户为广场 MCP 配置的自己的凭证（加密存储）

    广场 MCP 属于模板：URL/工具清单共享，鉴权 token 各自配置。
    个人凭证（enterprise_id 为空）与企业共享凭证各自独立成行，
    credential 为 AES-CBC 加密后的 headers JSON hex 字符串。
    """

    __tablename__ = 'mcp_user_credential'
    id: Mapped[id_key] = mapped_column(init=False)

    # 保存人（企业凭证时为操作成员，便于审计）
    user_id: Mapped[int] = mapped_column(BigInteger, index=True, comment='配置凭证的用户ID')
    mcp_server_id: Mapped[int] = mapped_column(BigInteger, index=True, comment='MCP 服务器ID')
    # 企业维度共享凭证：为空表示个人凭证；有值表示该企业下所有用户可用
    enterprise_id: Mapped[int | None] = mapped_column(BigInteger, default=None, index=True, comment='企业ID（空=个人凭证）')

    # 加密后的 headers JSON（如 {"Authorization": "Bearer xxx"}）
    credential: Mapped[str | None] = mapped_column(Text, default=None, comment='加密的用户凭证')

    # 唯一性：同一用户对同一 MCP，个人（enterprise_id 为空）与企业两条互不覆盖
    __table_args__ = (
        UniqueConstraint('user_id', 'mcp_server_id', 'enterprise_id', name='uix_user_mcp_credential'),
    )
