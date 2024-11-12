# 作者：langjunnan
# 开发时间：2025年7月23日

from __future__ import annotations

from typing import Any, Self

from common.schema import SchemaBase
from pydantic import Field, model_validator


class SearchAgentParam(SchemaBase):
    category_id: int | None = Field(None, description='分类id')
    keyword: str | None = Field(None, description='搜索词')


class AgentDetail(SchemaBase):
    title: str = Field(description='agent title')
    name: str = Field(description='agent name')
    avatar: str | None = Field(None, description='agent avatar')
    description: str | None = Field(None, description='agent描述')
    owner: str = Field(description='owner')
    is_public: bool = Field(False, description='是否公开')
    tools: int = Field(description='tools count')
    skills: int = Field(description='skills count')
    knowledge: int = Field(description='knowledge count')
    databases: int = Field(description='databases count')

    @model_validator(mode='before')
    @classmethod
    def handle(cls, data: Any) -> Self:
        data['tools'] = len(data['tools']) if data['tools'] else 0
        data['skills'] = len(data['skills']) if data['skills'] else 0
        data['knowledge'] = len(data['knowledge']) if data['knowledge'] else 0
        data['databases'] = len(data['databases']) if data['databases'] else 0
        data['owner'] = data['user']['username']
        return data


class GetAgentDetail(SchemaBase):
    """agent 公开详情（配置页/详情页共用）"""

    id: int = Field(0, description='id')
    name: str = Field(description='agent name')
    title: str = Field(description='agent title')
    avatar: str | None = Field(None, description='头像')
    description: str | None = Field(None, description='描述')
    system_prompt: str | None = Field(None, description='系统提示词')
    prologue: str | None = Field(None, description='开场白')
    mcps: list[str] = Field(default_factory=list, description='绑定的 MCP 列表 ["owner/name", ...]')
    skills: list[str] = Field(default_factory=list, description='绑定的 Skill 列表 ["owner/name", ...]')
    enable_search: bool = Field(False, description='联网搜索')
    enable_multimodal: bool = Field(False, description='多模态')
    enable_suggest: bool = Field(False, description='问题建议')
    is_public: bool = Field(False, description='是否公开')
    category: str | None = Field(None, description='分类名称')
    owner: str = Field(description='owner')

    @model_validator(mode='before')
    @classmethod
    def handle(cls, data: Any) -> Self:
        if hasattr(data, '__dict__'):
            data.owner = data.user.username if data.user else ''
            data.category = data.category.name if data.category else None
            data.mcps = data.mcps or []
            data.skills = data.skills or []
        else:
            owner = data.get('user')
            data['owner'] = owner['username'] if isinstance(owner, dict) else (owner.username if owner else '')
            category = data.get('category')
            data['category'] = category['name'] if isinstance(category, dict) else (category.name if category else None)
            data['mcps'] = data.get('mcps') or []
            data['skills'] = data.get('skills') or []
        return data


class PublishAgentParam(SchemaBase):
    """创建/配置 agent"""

    name: str = Field(
        ...,
        min_length=2,
        max_length=64,
        pattern=r'^[a-z0-9][a-z0-9-]*$',
        description='agent name，小写字母/数字/连字符',
    )
    title: str = Field(..., min_length=1, max_length=255, description='标题')
    avatar: str | None = Field(None, max_length=255, description='头像 URL')
    description: str | None = Field(None, max_length=1024, description='描述')
    system_prompt: str | None = Field(None, description='系统提示词')
    prologue: str | None = Field(None, description='开场白')
    mcps: list[str] = Field(default_factory=list, description='绑定的 MCP ["owner/name", ...]')
    skills: list[str] = Field(default_factory=list, description='绑定的 Skill ["owner/name", ...]')
    enable_search: bool = Field(False, description='联网搜索')
    enable_multimodal: bool = Field(False, description='多模态')
    enable_suggest: bool = Field(False, description='问题建议')
    is_public: bool = Field(False, description='是否公开：True 所有企业可见 / False 仅本企业与作者可见')
    category_id: int | None = Field(None, description='分类ID')


class UpdateAgentParam(SchemaBase):
    """更新 agent（全字段可选）"""

    title: str | None = Field(None, min_length=1, max_length=255, description='标题')
    avatar: str | None = Field(None, max_length=255, description='头像 URL')
    description: str | None = Field(None, max_length=1024, description='描述')
    system_prompt: str | None = Field(None, description='系统提示词')
    prologue: str | None = Field(None, description='开场白')
    mcps: list[str] | None = Field(None, description='绑定的 MCP')
    skills: list[str] | None = Field(None, description='绑定的 Skill')
    enable_search: bool | None = Field(None, description='联网搜索')
    enable_multimodal: bool | None = Field(None, description='多模态')
    enable_suggest: bool | None = Field(None, description='问题建议')
    is_public: bool | None = Field(None, description='是否公开')
    category_id: int | None = Field(None, description='分类ID')


class AgentCategoryDetail(SchemaBase):
    id: int = Field(description='id')
    name: str = Field(description='分类名称')
