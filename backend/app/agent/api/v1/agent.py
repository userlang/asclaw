# 作者：langjunnan
# 开发时间：2025年7月23日

from typing import Annotated, List

from app.agent.service.agent_server_service import AgentError, agent_server_service
from app.enterprise.service.enterprise_service import get_current_enterprise_id
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
from fastapi import APIRouter, Depends, Path, Query, Request

router = APIRouter()


@router.get(
    '/',
    summary='搜索agent',
    dependencies=[DependsJwtAuth, DependsPagination],
)
async def search_agent(
    request: Request,
    db: CurrentSession,
    viewer_enterprise_id: Annotated[int | None, Depends(get_current_enterprise_id)],
    keyword: str | None = Query(None, description='搜索词'),
    category_id: int | None = Query(None, description='分类id'),
) -> ResponseSchemaModel[PageData[AgentDetail]]:
    """广场列表：公开 + 本人 + 本企业私有"""
    agent_select = await agent_server_service.get_select(
        keyword=keyword,
        category_id=category_id,
        viewer_user_id=request.user.id,
        viewer_enterprise_id=viewer_enterprise_id,
    )
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
    summary='agent 详情（按可见性）',
    dependencies=[DependsJwtAuth],
)
async def get_agent_detail(
    request: Request,
    viewer_enterprise_id: Annotated[int | None, Depends(get_current_enterprise_id)],
    username: str = Path(description='username'),
    agent_name: str = Path(description='agent_name'),
) -> ResponseSchemaModel[GetAgentDetail | None]:
    """公开 agent 所有人可见；私有 agent 仅作者本人与其企业成员可见"""
    result = await agent_server_service.get_agent_for_viewer(
        username,
        agent_name,
        viewer_user_id=request.user.id,
        viewer_enterprise_id=viewer_enterprise_id,
    )
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
