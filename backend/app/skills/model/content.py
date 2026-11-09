#!/usr/bin/env python3
# 作者：langjunnan
# 开发时间：2025年7月23日

# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from common.model import Base
from sqlalchemy import BigInteger, DateTime, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

if TYPE_CHECKING:
    from datetime import datetime


class SkillContent(Base):
    """skill 附加文件内容（导入时从来源抓取的 SKILL.md 之外的文件）

    时间列沿用 Base（DateTimeMixin）的 created_time/updated_time（init=False + 默认值），
    不要自行声明无默认的 DateTime 列——会触发 MappedAsDataclass 字段顺序错误。
    """

    __tablename__ = 'skill_content'
    __table_args__ = (
        UniqueConstraint('skill_id', 'file_path', name='uk_skill_content_skill_path'),
    )

    # 无默认值列必须声明在最前（MappedAsDataclass 字段顺序约束）
    skill_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True, comment='关联 agent_skill.id')
    file_path: Mapped[str] = mapped_column(String(255), nullable=False, comment='相对路径，如 scripts/run.py')

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, init=False)
    content: Mapped[str | None] = mapped_column(Text, default=None, comment='文件文本内容')
