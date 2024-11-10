#!/usr/bin/env python3
# 作者：langjunnan
# 开发时间：2025年7月23日

# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Any, Dict, List, Optional, Self

from common.schema import SchemaBase
from fastmcp.mcp_config import RemoteMCPServer, StdioMCPServer
from pydantic import BaseModel, Field, field_validator, model_validator

# 鉴权相关 header 键名特征，用于判断 MCP 是否需要用户自备 token
_AUTH_HEADER_PATTERN = ('authorization', 'token', 'api-key', 'apikey', 'api_key', 'secret', 'x-api-key', 'key')
# URL query 中的敏感参数名（如 amap 的 ?key=xxx），全小写精确匹配
_URL_SENSITIVE_PARAMS = ('key', 'apikey', 'api_key', 'api-key', 'token', 'access_token', 'secret', 'ak', 'appkey', 'app_key')

# URL 参数键在凭证体系里的前缀：凭证存 {"url:key": "..."} 表示替换 URL query 中的 key 参数
URL_PARAM_PREFIX = 'url:'


def _url_sensitive_param_names(server_config: dict | None) -> list[str]:
    """从 server_config.mcpServers 的 url query 中找出敏感参数名（按出现顺序去重）"""
    from urllib.parse import parse_qsl, urlsplit

    names: list[str] = []
    if not server_config:
        return names
    for cfg in (server_config.get('mcpServers') or {}).values():
        url = cfg.get('url') if isinstance(cfg, dict) else None
        if not isinstance(url, str) or not url:
            continue
        try:
            query = urlsplit(url).query
        except ValueError:
            continue
        for name, _ in parse_qsl(query, keep_blank_values=True):
            if name.lower() in _URL_SENSITIVE_PARAMS and name not in names:
                names.append(name)
    return names


def detect_auth_header_keys(server_config: dict | None) -> list[str]:
    """从 server_config.mcpServers 中提取需要用户配置的鉴权键名（不含值）

    header 键原样返回（如 'Authorization'）；URL 敏感参数返回 'url:key' 形式。
    """
    keys: list[str] = []
    if not server_config:
        return keys
    for cfg in (server_config.get('mcpServers') or {}).values():
        headers = cfg.get('headers') if isinstance(cfg, dict) else None
        if isinstance(headers, dict):
            keys.extend(k for k, v in headers.items() if v and k not in keys)
    keys.extend(f'{URL_PARAM_PREFIX}{name}' for name in _url_sensitive_param_names(server_config) if f'{URL_PARAM_PREFIX}{name}' not in keys)
    return keys


def detect_needs_auth(server_config: dict | None, transport: str | None = None) -> bool:
    """remote 型 MCP 的 headers 或 URL query 含鉴权特征即视为需要用户自备 token；
    stdio/local 型走 owner 部署的实例，对广场用户无凭证概念"""
    if transport == 'stdio':
        return False
    if _url_sensitive_param_names(server_config):
        return True
    for key in detect_auth_header_keys(server_config):
        if not key.startswith(URL_PARAM_PREFIX) and any(p in key.lower() for p in _AUTH_HEADER_PATTERN):
            return True
    return False


class GetMcpDetail(SchemaBase):
    id: int = Field(description='id')
    server_title: str | None = Field(None, description='名称')
    description: str | None = Field(None, description='描述')
    server_type: str | None = Field(None, description='类型')
    avatar: str | None = Field(None, description='头像 URL（未配置时前端回落默认机器人头像）')
    cover: str | None = Field(None, description='封面图 URL（首页样式用）')
    needs_auth: bool = Field(False, description='是否需要用户自备 token')
    server_metadata: Dict[str, Any] | None = Field(None, description='能力')
    tools: List[Dict[str, Any]] | None = Field(None, description='工具')
    prompts: List[Dict[str, Any]] | None = Field(None, description='提示词')
    resources: List[Dict[str, Any]] | None = Field(None, description='资源')
    envs: Dict[str, Any] | None = Field(None, description='环境变量')

    @model_validator(mode='before')
    @classmethod
    def handle_envs(cls, data: Any) -> Any:
        envs = data.envs
        if envs:
            data.envs = {k: '******' for k in envs}
        data.needs_auth = detect_needs_auth(data.server_config, data.transport)
        return data


class McpBaseDetail(SchemaBase):
    # id: int = Field(description='id')
    # server_title: str = Field(description='名称')
    server_name: str = Field(description='mcp name')
    description: str | None = Field(None, description='描述')
    server_type: str = Field(description='类型')
    avatar: str | None = Field(description='avatar')
    # user: GetUserInfo = Field(description='用户信息')


class McpSearchDetail(McpBaseDetail):
    # tools: List[Dict[str, Any]] | None = Field(None, description='工具')
    # prompts: List[Dict[str, Any]] | None = Field(None, description='提示词')
    # resources: List[Dict[str, Any]] | None = Field(None, description='资源')

    # @model_validator(mode="after")
    # def handle(self):
    #     self.tools = len(self.tools) if self.tools else 0
    #     self.prompts = len(self.prompts) if self.prompts else 0
    #     self.resources = len(self.resources) if self.resources else 0
    #     return self
    id: int = Field(description='id')
    tools: int = Field(description='工具数量')
    prompts: int = Field(description='提示词数量')
    resources: int = Field(description='资源数量')
    call_count: int = Field(description='调用量')
    owner: str = Field(description='owner')
    needs_auth: bool = Field(False, description='是否需要用户自备 token')

    @model_validator(mode='before')
    @classmethod
    def handel(cls, data: Any) -> Self:
        data['tools'] = len(data['tools']) if data['tools'] else 0
        data['prompts'] = len(data['prompts']) if data['prompts'] else 0
        data['resources'] = len(data['resources']) if data['resources'] else 0
        data['call_count'] = 1889
        data['owner'] = data['user']['username']
        data['needs_auth'] = detect_needs_auth(data['server_config'], data.get('transport'))
        return data


class McpRecommendDetail(SchemaBase):
    server_name: str = Field(description='mcp name')
    description: str | None = Field(None, description='描述')
    server_type: str = Field(description='类型')
    owner: str = Field(description='owner')
    cover: str | None = Field(None, description='封面图，仅用于首页样式展示')
    needs_auth: bool = Field(False, description='是否需要用户自备 token')
    call_count: int = Field(description='调用量')

    @model_validator(mode='before')
    @classmethod
    def handel(cls, data: Any) -> Self:
        data.owner = data.user.username
        data.call_count = 1889
        data.needs_auth = detect_needs_auth(data.server_config, data.transport)
        return data


class GetMcpRecommendDetail(SchemaBase):
    """ """

    id: int = Field(description='id')
    name: str | None = Field(None, description='分类名称')
    mcp_servers: List[McpRecommendDetail] | None = Field(None, description='servers', serialization_alias='servers')


class GetMcpFeedDetail(SchemaBase):
    """ """

    id: int = Field(description='id')
    server_title: str | None = Field(None, description='名称')
    description: str | None = Field(None, description='描述')
    server_config: Dict[str, Any] | None = Field(None, description='元信息')
    created_time: datetime = Field(description='创建时间')
    updated_time: datetime | None = Field(None, description='更新时间')


class SearchMcpParam(SchemaBase):
    category_id: int | None = Field(None, description='分类id')
    keyword: str | None = Field(None, description='搜索词')


class UpdateMcpServerParam(SchemaBase):
    mcp_endpoint: str = Field(None, description='mcp server endpoint')
    capabilities: Optional[Dict[str, Any]] | None = Field(None, description='能力')
    tools: Optional[Dict[str, Any]] | None = Field(None, description='工具')
    prompts: Optional[Dict[str, Any]] | None = Field(None, description='提示词')
    resources: Optional[Dict[str, Any]] | None = Field(None, description='资源')
    is_public: bool = Field(None, description='是否公开')


class UpdateMcpCoverParam(SchemaBase):
    cover: str | None = Field(None, max_length=255, description='封面图 URL，置空清除封面')


class UpdateMcpAvatarParam(SchemaBase):
    avatar: str | None = Field(None, max_length=512, description='头像 URL，置空恢复默认机器人头像')


class McpCredentialHeadersParam(SchemaBase):
    """用户为广场 MCP 配置的自己的鉴权 headers，整体加密存储"""

    headers: Dict[str, str] = Field(description='待配置的 headers，如 {"Authorization": "Bearer xxx"}')


class McpServersWrapper(BaseModel):
    mcpServers: Dict[str, StdioMCPServer | RemoteMCPServer]


class AddMcpServerParam(BaseModel):
    server_title: str = Field(description='server_title')
    description: str | None = Field(None, description='描述')
    mcpServers: McpServersWrapper = Field(description='mcp server config')

    @field_validator('server_title')
    @classmethod
    def validate_server_title(cls, v: str) -> str:
        import re

        v = v.strip()
        if not v:
            raise ValueError('server_title cannot be empty')
        if not re.match(r'^[a-zA-Z0-9_\-. \u4e00-\u9fff\u3400-\u4dbf\uff00-\uffef]+$', v):
            raise ValueError(
                'server_title only allows Chinese/English letters, numbers, spaces, hyphens, underscores and dots'
            )
        return v

    @field_validator('mcpServers')
    def validate_mcpservers(cls, v):
        if not v:
            raise ValueError('mcpServers cannot be empty')
        return v


class AddMcpPackageParam(SchemaBase):
    language: str | None = Field(None, description='语言')
    package: str | None = Field(None, description='包名')
    env: Optional[Dict[str, str]] | None = Field({}, description='Environment variables')


class CallToolParam(SchemaBase):
    username: str = Field(description='用户名')
    server_name: str = Field(description='MCP server name')
    tool_name: str = Field(description='工具名称')
    arguments: Optional[Dict[str, Any]] = Field(description='工具参数')


class AddMcpParam(SchemaBase):
    """
    部署mcp参数  主要有的只能在本地运行
    1. 直接提供包名部署  uvx npx  暂时支持 （填写包名接口）    mcpproxy转发
        1. 如果部署过 则不允许部署
    2. 解析api  restful_api  直接转发
        1. oauth2.0 授权后可以
        2. key校验的
    3. 服务托管 基于代码托管平台  需要 Dockerfile   mcpproxy转发
        1. 直接配置构建命令
        2. 直接配置启动命令
    4. 解析 mcpServer配置进行部署
        1. command: 目前支持  uvx npx
        2. 支持定时更新
        3. 支持参数更新


    {
      "mcpServers": {
        "brave-search": {
          "command": "npx",
          "args": [
            "-y",
            "@modelcontextprotocol/server-brave-search"
          ],
          "env": {
            "BRAVE_API_KEY": "YOUR_API_KEY_HERE"
          }
        }
      }
    }

    构建镜像
        1. uvx python3.10    uv add xxx 安装    uvx xxx 运行
        2. npx node20        pnpm install xxx 安装   npx xxx 运行
    """

    # python3.13  java golang 等
    language: str | None = Field(None, description='语言')
    # 语言版本
    language_version: str | None = Field(None, description='语言版本')
    # pip、node、maven、bun
    deploy_method: str | None = Field(None, description='部署方式')
    # uvx pkg、npx pkg
    run_env: str | None = Field(None, description='运行环境')
    # 构建命令
