from __future__ import annotations

from datetime import datetime
from typing import Literal

from common.schema import SchemaBase
from pydantic import Field, field_validator


class EnterpriseApplyParam(SchemaBase):
    """企业入驻申请参数"""

    name: str = Field(description='企业名称')
    credit_code: str = Field(description='统一社会信用代码（营业执照）')
    legal_person: str | None = Field(None, description='法定代表人')
    contact_name: str = Field(description='联系人')
    contact_phone: str = Field(description='联系电话')
    contact_email: str | None = Field(None, description='联系邮箱')
    license_url: str | None = Field(None, description='营业执照文件地址')
    address: str | None = Field(None, description='注册地址')
    description: str | None = Field(None, description='企业简介')
    username: str = Field(description='登录用户名')
    password: str = Field(min_length=6, description='登录密码')

    @field_validator('username')
    @classmethod
    def username_validator(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('用户名不能为空')
        return v


class EnterpriseLoginParam(SchemaBase):
    """商家登录参数"""

    username: str = Field(description='用户名')
    password: str = Field(description='密码')


class EnterpriseDetail(SchemaBase):
    """企业详情（管理端）"""

    id: int
    name: str
    credit_code: str
    legal_person: str | None = None
    contact_name: str
    contact_phone: str
    contact_email: str | None = None
    license_url: str | None = None
    address: str | None = None
    description: str | None = None
    username: str
    status: int
    reject_reason: str | None = None
    reviewed_time: datetime | None = None
    created_time: datetime


class UpdateEnterpriseParam(SchemaBase):
    """管理员修改企业信息"""

    name: str | None = Field(None, description='企业名称')
    credit_code: str | None = Field(None, description='统一社会信用代码')
    legal_person: str | None = Field(None, description='法定代表人')
    contact_name: str | None = Field(None, description='联系人')
    contact_phone: str | None = Field(None, description='联系电话')
    contact_email: str | None = Field(None, description='联系邮箱')
    license_url: str | None = Field(None, description='营业执照文件地址')
    address: str | None = Field(None, description='注册地址')
    description: str | None = Field(None, description='企业简介')
    username: str | None = Field(None, description='登录用户名')
    password: str | None = Field(None, min_length=6, description='重置登录密码（为空则不修改）')


class EnterpriseReviewParam(SchemaBase):
    """审核参数（批量）"""

    pks: list[int] = Field(description='企业 ID 列表')
    status: Literal[1, 2] = Field(description='目标状态（1通过 2拒绝）')
    reject_reason: str | None = Field(None, description='拒绝原因（拒绝时填写）')


class DeleteEnterpriseParam(SchemaBase):
    """批量删除参数"""

    pks: list[int] = Field(description='企业 ID 列表')
