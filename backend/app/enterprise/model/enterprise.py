# 作者：langjunnan
# 开发时间：2025年7月23日

from __future__ import annotations

from datetime import datetime

from common.model import Base, id_key
from sqlalchemy import BigInteger, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column


class Enterprise(Base):
    """企业入驻申请"""

    __tablename__ = 'enterprise'

    id: Mapped[id_key] = mapped_column(init=False)
    # 必填字段（MappedAsDataclass 要求：无默认值字段必须在有默认值字段之前）
    name: Mapped[str] = mapped_column(String(100), comment='企业名称')
    credit_code: Mapped[str] = mapped_column(String(64), comment='统一社会信用代码（营业执照）')
    contact_name: Mapped[str] = mapped_column(String(50), comment='联系人')
    contact_phone: Mapped[str] = mapped_column(String(20), comment='联系电话')
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, comment='登录用户名')
    password: Mapped[str] = mapped_column(String(255), comment='密码哈希（bcrypt）')
    user_id: Mapped[int | None] = mapped_column(BigInteger, default=None, index=True, comment='关联用户ID（sys_user）')

    # 可选字段
    legal_person: Mapped[str | None] = mapped_column(String(50), default=None, comment='法定代表人')
    contact_email: Mapped[str | None] = mapped_column(String(100), default=None, comment='联系邮箱')
    license_url: Mapped[str | None] = mapped_column(String(255), default=None, comment='营业执照文件地址')
    address: Mapped[str | None] = mapped_column(String(255), default=None, comment='注册地址')
    description: Mapped[str | None] = mapped_column(Text, default=None, comment='企业简介')

    # 审核信息
    status: Mapped[int] = mapped_column(default=0, index=True, comment='审核状态（0待审核 1已通过 2已拒绝）')
    reject_reason: Mapped[str | None] = mapped_column(String(255), default=None, comment='拒绝原因')
    reviewed_by: Mapped[int | None] = mapped_column(BigInteger, default=None, comment='审核人用户ID')
    reviewed_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None, comment='审核时间')
