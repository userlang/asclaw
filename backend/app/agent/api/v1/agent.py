# 作者：langjunnan
# 开发时间：2025年7月23日

from typing import List

from app.agent.service.agent_server_service import agent_server_service
from app.mcp.schema.agent import (
    AgentCategoryDetail,
    AgentDetail,
    GetAgentDetail,
    PublishAgentParam,
    UpdateAgentParam,
)
from common.pagination import DependsPagination, PageData, paging_data
from common.response.response_schema import ResponseModel, ResponseSchemaModel, response_base
from common.security.jwt import DependsJwtAuth
from database.db import CurrentSession, CurrentSessionTransaction
from fastapi import APIRouter, Path, Query, Request

router = APIRouter()


@router.get(
    '/',
    summary='搜索agent',
    dependencies=[DependsPagination],
)
async def search_agent(
    db: CurrentSession,
    keyword: str | None = Query(None, description='搜索词'),
    category_id: int | None = Query(None, description='分类id'),
) -> ResponseSchemaModel[PageData[AgentDetail]]:
    agent_select = await agent_server_service.get_select(keyword=keyword, category_id=category_id)
    page_data = await paging_data(db, agent_select)
    return response_base.success(data=page_data)


@router.get('/categories', summary='agent categories')
async def get_agent_categories() -> ResponseSchemaModel[List[AgentCategoryDetail]]:
    result = await agent_server_service.get_categories()
    return response_base.success(data=result)


@router.get(
    '/mine',
    summary='获取我的 Agent 列表',
    dependencies=[DependsJwtAuth, DependsPagination],
)
async def get_my_agents(
    request: Request,
    db: CurrentSession,
) -> ResponseSchemaModel[PageData[AgentDetail]]:
    from app.admin.service.admin_agent_service import agent_admin_server_service

    agent_select = await agent_admin_server_service.get_my_agents(user_id=request.user.id)
    page_data = await paging_data(db, agent_select)
    return response_base.success(data=page_data)


@router.post('/publish', summary='创建 agent', dependencies=[DependsJwtAuth])
async def publish_agent(request: Request, obj: PublishAgentParam) -> ResponseSchemaModel[GetAgentDetail]:
    agent = await agent_server_service.publish_agent(
        user_id=request.user.id,
        name=obj.name,
        title=obj.title,
        avatar=obj.avatar,
        description=obj.description,
        system_prompt=obj.system_prompt,
        prologue=obj.prologue,
        mcps=obj.mcps,
        skills=obj.skills,
        enable_search=obj.enable_search,
        enable_multimodal=obj.enable_multimodal,
        enable_suggest=obj.enable_suggest,
        is_public=obj.is_public,
        category_id=obj.category_id,
    )
    return response_base.success(data=agent)


@router.get(
    '/{username}/{agent_name}',
    summary='agent 公开详情',
)
async def get_agent_detail(
    username: str = Path(description='username'),
    agent_name: str = Path(description='agent_name'),
) -> ResponseSchemaModel[GetAgentDetail | None]:
    from app.agent.service.agent_server_service import AgentError

    result = await agent_server_service.get_public_agent_by_user(username=username, agent_name=agent_name)
    if not result:
        # NotFoundError 继承 BaseExceptionMixin（不在全局处理器树），会变成空 500；
        # 必须用 AgentError（BaseExceptionError 子类）才能返回 404 + msg
        raise AgentError(code=404, msg='Agent不存在')
    return response_base.success(data=result)


@router.put('/{agent_id}', summary='更新我的 agent', dependencies=[DependsJwtAuth])
async def update_my_agent(
    request: Request,
    obj: UpdateAgentParam,
    agent_id: int = Path(description='agent_id'),
) -> ResponseModel:
    count = await agent_server_service.update_agent(
        user_id=request.user.id, agent_id=agent_id,
        **obj.model_dump(exclude_none=False),
    )
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.delete('/{agent_id}', summary='删除我的 agent', dependencies=[DependsJwtAuth])
async def delete_my_agent(
    request: Request,
    agent_id: int = Path(description='agent_id'),
) -> ResponseModel:
    count = await agent_server_service.delete_agent(user_id=request.user.id, agent_id=agent_id)
    if count > 0:
        return response_base.success()
    return response_base.fail()
