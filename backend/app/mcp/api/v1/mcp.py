# 作者：langjunnan
# 开发时间：2025年7月23日

import copy

from loguru import logger
from typing import Annotated, List

from app.admin.schema.mcp import MyMcpDetail
from app.admin.service.admin_mcp_service import mcp_admin_server_service
from app.mcp.schema.category import GetCategoryBase
from app.mcp.schema.mcp import (
    CallToolParam,
    GetMcpDetail,
    GetMcpFeedDetail,
    GetMcpRecommendDetail,
    McpRecommendDetail,
    McpSearchDetail,
    McpCredentialHeadersParam,
    UpdateMcpAvatarParam,
    UpdateMcpCoverParam,
    UpdateMcpPublicParam,
    detect_needs_auth,
)
from app.mcp.service.mcp_category_service import mcp_category_service
from app.mcp.service.mcp_server_service import McpError, mcp_server_service
from common.exception import errors
from common.pagination import DependsPagination, PageData, paging_data
from common.response.response_schema import ResponseModel, ResponseSchemaModel, response_base
from common.security.jwt import DependsJwtAuth
from database.db import CurrentSession, async_db_session
from fastapi import APIRouter, Path, Query, Request
from fastmcp import Client
from fastmcp.mcp_config import MCPConfig

router = APIRouter()


@router.get(
    '/',
    summary='搜索mcp',
    dependencies=[DependsPagination],
)
async def search_mcp(
    db: CurrentSession,
    keyword: str | None = Query(None, description='搜索词'),
    category_id: int | None = Query(None, description='分类id'),
) -> ResponseSchemaModel[PageData[McpSearchDetail]]:
    mcp_select = await mcp_server_service.get_select(keyword=keyword, category_id=category_id)
    page_data = await paging_data(db, mcp_select)
    return response_base.success(data=page_data)


@router.get('/recommend', summary='推荐mcp列表')
async def get_recommend_mcp() -> ResponseSchemaModel[List[McpRecommendDetail]]:
    result = await mcp_server_service.get_recommend_mcp()
    return response_base.success(data=result)


@router.get('/categories', summary='mcp categories')
async def get_mcp_categories() -> ResponseSchemaModel[List[GetCategoryBase]]:
    result = await mcp_server_service.get_categories()
    return response_base.success(data=result)


@router.get('/categories/recommend', summary='按分类推荐mcp')
async def get_recommend_category_mcp() -> ResponseSchemaModel[List[GetMcpRecommendDetail] | None]:
    result = await mcp_category_service.get_recommend_category()
    return response_base.success(data=result)


@router.get(
    '/mine',
    summary='获取我的 MCP 列表',
    dependencies=[DependsJwtAuth, DependsPagination],
)
async def get_my_mcps(
    request: Request,
    db: CurrentSession,
) -> ResponseSchemaModel[PageData[MyMcpDetail]]:
    mcp_select = await mcp_admin_server_service.get_my_mcps(user_id=request.user.id)
    page_data = await paging_data(db, mcp_select)
    return response_base.success(data=page_data)


@router.get('/feed', summary='feed', dependencies=[DependsJwtAuth])
async def get_feed() -> ResponseSchemaModel[List[GetMcpFeedDetail] | None]:
    """仅显示最近一周的"""
    result = await mcp_server_service.get_mcp_last_7_day()
    return response_base.success(data=result)


@router.get('/credential-server-ids', summary='我已配置凭证的 MCP id 列表', dependencies=[DependsJwtAuth])
async def get_credential_server_ids(request: Request) -> ResponseSchemaModel[List[int]]:
    """个人凭证 + 所属企业共享凭证覆盖的 MCP id 并集，供前端过滤需鉴权 MCP"""
    result = await mcp_server_service.get_configured_credential_server_ids(request.user.username)
    return response_base.success(data=result)


@router.get('/{mcp_id}/credential', summary='查询 MCP 凭证配置状态', dependencies=[DependsJwtAuth])
async def get_mcp_credential_status(
    request: Request,
    mcp_id: Annotated[int, Path(description='MCP id')],
) -> ResponseSchemaModel[dict]:
    """返回是否需要 token、需要的 header 键名（不含值）、当前用户是否已配置"""
    result = await mcp_server_service.get_credential_status(request.user.username, mcp_id)
    return response_base.success(data=result)


@router.put('/{mcp_id}/credential', summary='配置我的 MCP 凭证', dependencies=[DependsJwtAuth])
async def update_mcp_credential(
    request: Request,
    mcp_id: Annotated[int, Path(description='MCP id')],
    obj: McpCredentialHeadersParam,
    scope: str = Query('personal', description='凭证范围：personal=个人 / enterprise=企业共享'),
) -> ResponseModel:
    """整体加密落库，仅本人（或企业全体成员）可用；重复提交覆盖"""
    await mcp_server_service.save_credential(request.user.username, mcp_id, obj.headers, scope=scope)
    return response_base.success()


@router.delete('/{mcp_id}/credential', summary='清除我的 MCP 凭证', dependencies=[DependsJwtAuth])
async def delete_mcp_credential(
    request: Request,
    mcp_id: Annotated[int, Path(description='MCP id')],
    scope: str = Query('personal', description='凭证范围：personal=个人 / enterprise=企业共享'),
) -> ResponseModel:
    await mcp_server_service.delete_credential(request.user.username, mcp_id, scope=scope)
    return response_base.success()


@router.get('/{mcp_id}', summary='mcp 详情')
async def get_mcp_detail(
    mcp_id: Annotated[int, Path(description='MCP id')],
) -> ResponseSchemaModel[GetMcpDetail | None]:
    result = await mcp_server_service.get_mcp_by_id(mcp_id)
    return response_base.success(data=result)


@router.put('/{mcp_id}/cover', summary='修改 MCP 封面', dependencies=[DependsJwtAuth])
async def update_mcp_cover(
    request: Request,
    mcp_id: Annotated[int, Path(description='MCP id')],
    obj: UpdateMcpCoverParam,
) -> ResponseModel:
    await mcp_server_service.update_cover(request.user.username, mcp_id, obj.cover)
    return response_base.success()


@router.put('/{mcp_id}/avatar', summary='修改 MCP 头像', dependencies=[DependsJwtAuth])
async def update_mcp_avatar(
    request: Request,
    mcp_id: Annotated[int, Path(description='MCP id')],
    obj: UpdateMcpAvatarParam,
) -> ResponseModel:
    """仅创建者可改；置空恢复默认机器人头像"""
    await mcp_server_service.update_avatar(request.user.username, mcp_id, obj.avatar)
    return response_base.success()


@router.put('/{mcp_id}/public', summary='切换 MCP 公开/私有', dependencies=[DependsJwtAuth])
async def update_mcp_public(
    request: Request,
    mcp_id: Annotated[int, Path(description='MCP id')],
    obj: UpdateMcpPublicParam,
) -> ResponseModel:
    """仅创建者可切换；公开后出现在广场"""
    await mcp_server_service.update_public(request.user.username, mcp_id, obj.is_public)
    return response_base.success()


@router.post('/invoke', summary='调用 MCP 工具（Playground）', dependencies=[DependsJwtAuth])
async def call_tool(
    request: Request,
    call_param: CallToolParam,
):
    mcp_server = await mcp_server_service.get_mcp_by_id(call_param.mcp_id)

    # 可见性：非本人只能调用公开 MCP
    is_owner = mcp_server.user_id == request.user.id
    if not is_owner and not mcp_server.is_public:
        raise errors.NotFoundError(msg='MCP服务器不存在')

    server_config = mcp_server.server_config
    if not server_config or 'mcpServers' not in server_config:
        raise errors.NotFoundError(msg='MCP服务器配置不存在')

    # 凭证策略与聊天链路一致：非 owner 先剥离配置里的鉴权材料，
    # 需要鉴权的 MCP 必须使用调用者自己的凭证（个人优先、企业共享兜底）
    mcp_servers_cfg = copy.deepcopy(server_config['mcpServers'])
    if not is_owner and detect_needs_auth(server_config, mcp_server.transport):
        async with async_db_session() as db:
            user_credential, cred_source = await mcp_server_service.resolve_user_credential(
                db, request.user.id, mcp_server.id
            )
        if not user_credential:
            raise McpError(code=403, msg='该 MCP 需要鉴权，请先在详情页配置你自己的 Token')
        logger.info('invoke mcp#{} uses {} credential', call_param.mcp_id, cred_source)
        mcp_servers_cfg = {
            name: mcp_server_service.apply_credential_to_config(
                mcp_server_service.sanitize_server_config(copy.deepcopy(cfg)), user_credential
            )
            for name, cfg in mcp_servers_cfg.items()
        }

    mcp_config = MCPConfig(mcpServers=mcp_servers_cfg)
    client = Client(mcp_config)

    async with client:
        await client.ping()
        result = await client.call_tool(call_param.tool_name, call_param.arguments)
        return response_base.success(data=result)
