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
    favorite_count: int = Field(description='favorite count')

    @model_validator(mode='before')
    @classmethod
    def handle(cls, data: Any) -> Self:
        data['owner'] = data['user']['username']
        data['favorite_count'] = 900
        return data


class GetSkillDetail(SchemaBase):
    name: str = Field(description='skill name')
    title: str = Field(description='skill title')
    description: str | None = Field(None, description='skill描述')
    path: str | None = Field(None, description='skill path')
    repository: str | None = Field(None, description='仓库地址')
    owner: str = Field(description='owner')
    avatar: str = Field(description='avatar')
    category: str | None = Field(None, description='分类名称')
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
