# 作者：langjunnan
# 开发时间：2025年7月23日

from datetime import datetime
from typing import Any

from app.admin.schema.category import CategoryDetail
from app.admin.schema.user import GetUserDetail
from app.mcp.schema.mcp import detect_needs_auth
from common.schema import SchemaBase
from pydantic import Field, model_validator


class AdminMcpBaseDetail(SchemaBase):
    id: int = Field(description='id')
    server_title: str = Field(description='名称')
    server_name: str = Field(description='mcp name')
    description: str | None = Field(None, description='描述')
    server_type: str = Field(description='类型')
    compile_type: str = Field(description='编译类型')
    git: str | None = Field(None, description='git地址')
    created_time: datetime = Field(description='创建时间')
    updated_time: datetime | None = Field(None, description='更新时间')


class AdminSearchMcpParam(SchemaBase):
    # category_id: int | None = Field(None, description='分类id')
    keyword: str | None = Field(None, description='搜索词')
    transport: str | None = Field(None, description='协议类型')
    server_type: str | None = Field(None, description='部署类型')
    is_public: int | None = Field(None, description='是否公开')


class GetAdminMcpDetail(SchemaBase):
    id: int = Field(description='id')
    server_name: str = Field(description='mcp name')
    server_title: str | None = Field(None, description='名称')
    description: str | None = Field(None, description='描述')
    server_type: str | None = Field(None, description='类型')
    compile_type: str = Field(description='编译类型')
    git: str | None = Field(None, description='git地址')
    user: GetUserDetail = Field(description='用户信息')
    category: CategoryDetail | None = Field(None, description='分类信息')
    is_public: int | None = Field(None, description='是否公开')
    is_recommend: int | None = Field(None, description='是否推荐')


class MyMcpDetail(SchemaBase):
    id: int = Field(description='id')
    server_title: str = Field(description='名称')
    server_name: str = Field(description='mcp name')
    description: str | None = Field(None, description='描述')
    server_type: str = Field(description='类型')
    avatar: str | None = Field(None, description='MCP 头像 URL')
    is_public: bool | None = Field(None, description='是否公开')
    needs_auth: bool = Field(False, description='是否需要用户自备 token')
    user: GetUserDetail = Field(description='用户信息')
    created_time: datetime = Field(description='创建时间')
    updated_time: datetime | None = Field(None, description='更新时间')

    @model_validator(mode='before')
    @classmethod
    def handle_needs_auth(cls, data: Any) -> Any:
        # 分页链路 items 为 dict，单对象链路为 ORM 对象，两种都要兼容
        if isinstance(data, dict):
            data['needs_auth'] = detect_needs_auth(data.get('server_config'), data.get('transport'))
        else:
            data.needs_auth = detect_needs_auth(data.server_config, data.transport)
        return data


class UpdateMcpServerParam(SchemaBase):
    server_title: str | None = Field(None, description='名称')
    description: str | None = Field(None, description='描述')
    category_id: int | None = Field(None, description='分类ID')
    is_public: int | None = Field(None, description='是否公开')
    is_recommend: int | None = Field(None, description='是否推荐')
