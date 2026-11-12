# 作者：langjunnan
# 开发时间：2025年7月23日

from __future__ import annotations

from typing import Any, Self

from common.schema import SchemaBase
from pydantic import Field, model_validator


class SearchSkillParam(SchemaBase):
    category_id: int | None = Field(None, description='分类id')
    keyword: str | None = Field(None, description='搜索词')


class SkillDetail(SchemaBase):
    name: str = Field(description='skill name')
    title: str = Field(description='skill title')
    description: str | None = Field(None, description='skill描述')
    path: str | None = Field(None, description='skill path')
    owner: str = Field(description='owner')
    avatar: str = Field(description='avatar')
    is_public: bool = Field(False, description='是否公开')
    favorite_count: int = Field(description='favorite count')

    @model_validator(mode='before')
    @classmethod
    def handle(cls, data: Any) -> Self:
        data['owner'] = data['user']['username']
        data['favorite_count'] = 900
        return data


class GetSkillDetail(SchemaBase):
    id: int = Field(0, description='skill id')
    name: str = Field(description='skill name')
    title: str = Field(description='skill title')
    description: str | None = Field(None, description='skill描述')
    body: str | None = Field(None, description='SKILL.md 正文（Markdown）')
    path: str | None = Field(None, description='skill path')
    repository: str | None = Field(None, description='仓库地址')
    source_url: str | None = Field(None, description='导入来源')
    install_count: int = Field(0, description='安装/使用次数')
    owner: str = Field(description='owner')
    avatar: str = Field(description='avatar')
    category: str | None = Field(None, description='分类名称')
    is_public: bool = Field(False, description='是否公开')
    favorite_count: int = Field(description='favorite count')

    @model_validator(mode='before')
    @classmethod
    def handle(cls, data: Any) -> Self:
        if hasattr(data, '__dict__'):
            # ORM 对象：直接取关联属性
            data.owner = data.user.username if data.user else ''
            data.favorite_count = 900
            data.category = data.category.name if data.category else None
        else:
            # 已序列化的 dict（分页查询路径）
            owner = data.get('user')
            data['owner'] = owner['username'] if isinstance(owner, dict) else (owner.username if owner else '')
            data['favorite_count'] = 900
            category = data.get('category')
            data['category'] = category['name'] if isinstance(category, dict) else (category.name if category else None)
        return data


class SkillCategoryDetail(SchemaBase):
    id: int = Field(description='id')
    name: str = Field(description='分类名称')


class PublishSkillParam(SchemaBase):
    """发布（导入）skill：来源支持 GitHub 目录 URL（含 SKILL.md）或手填元信息"""

    name: str = Field(
        ...,
        min_length=2,
        max_length=64,
        pattern=r'^[a-z0-9][a-z0-9-]*$',
        description='skill name，小写字母/数字/连字符',
    )
    title: str = Field(..., min_length=1, max_length=255, description='标题')
    description: str = Field(..., min_length=1, max_length=1024, description='描述（注入 sys_prompt 的触发说明）')
    category_id: int | None = Field(None, description='分类ID')
    source_url: str | None = Field(None, max_length=500, description='SKILL.md 所在目录 URL（GitHub），提供时抓取正文')
    body: str | None = Field(None, description='SKILL.md 正文（Markdown），未提供 source_url 时可直接填写')
    is_public: bool = Field(False, description='是否公开：True 所有企业可见 / False 仅本企业与作者可见')
