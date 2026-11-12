# 作者：langjunnan
# 开发时间：2025年7月23日

from typing import Annotated, List

from app.enterprise.service.enterprise_service import get_current_enterprise_id
from app.mcp.schema.skill import (
    GetSkillDetail,
    PublishSkillParam,
    SkillCategoryDetail,
    SkillDetail,
)
from app.skills.service.skill_service import SkillError, skill_service
from common.pagination import DependsPagination, PageData, paging_data
from common.response.response_schema import ResponseModel, ResponseSchemaModel, response_base
from common.security.jwt import DependsJwtAuth
from database.db import CurrentSession, CurrentSessionTransaction
from fastapi import APIRouter, Depends, Path, Query, Request

router = APIRouter()


@router.get(
    '/',
    summary='搜索skill',
    dependencies=[DependsJwtAuth, DependsPagination],
)
async def search_skill(
    request: Request,
    db: CurrentSession,
    viewer_enterprise_id: Annotated[int | None, Depends(get_current_enterprise_id)],
    keyword: str | None = Query(None, description='搜索词'),
    category_id: int | None = Query(None, description='分类id'),
) -> ResponseSchemaModel[PageData[SkillDetail]]:
    """广场列表：公开 + 本人 + 本企业私有"""
    skill_select = await skill_service.get_select(
        keyword=keyword,
        category_id=category_id,
        viewer_user_id=request.user.id,
        viewer_enterprise_id=viewer_enterprise_id,
    )
    page_data = await paging_data(db, skill_select)
    return response_base.success(data=page_data)


@router.get('/categories', summary='skill categories')
async def get_skill_categories() -> ResponseSchemaModel[List[SkillCategoryDetail]]:
    result = await skill_service.get_categories()
    return response_base.success(data=result)


@router.get('/mine', summary='获取我的 skill 列表', dependencies=[DependsJwtAuth, DependsPagination])
async def get_my_skills(
    request: Request,
    db: CurrentSession,
) -> ResponseSchemaModel[PageData[GetSkillDetail]]:
    skill_select = await skill_service.get_my_skills(user_id=request.user.id)
    page_data = await paging_data(db, skill_select)
    return response_base.success(data=page_data)


@router.post('/publish', summary='发布（导入）skill', dependencies=[DependsJwtAuth])
async def publish_skill(request: Request, obj: PublishSkillParam) -> ResponseSchemaModel[GetSkillDetail]:
    """发布 skill：source_url 指向 GitHub 目录（含 SKILL.md）时自动抓取正文，否则用 body"""
    skill = await skill_service.publish_skill(
        user_id=request.user.id,
        name=obj.name,
        title=obj.title,
        description=obj.description,
        category_id=obj.category_id,
        source_url=obj.source_url,
        body=obj.body,
        is_public=obj.is_public,
    )
    return response_base.success(data=skill)


@router.delete('/{skill_id}', summary='删除我的 skill', dependencies=[DependsJwtAuth])
async def delete_my_skill(
    request: Request,
    skill_id: Annotated[int, Path(description='skill_id')],
) -> ResponseModel:
    count = await skill_service.delete_my_skill(user_id=request.user.id, skill_id=skill_id)
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.get('/{skill_id}/files', summary='获取 skill 附加文件列表', dependencies=[DependsJwtAuth])
async def get_skill_files(
    request: Request,
    viewer_enterprise_id: Annotated[int | None, Depends(get_current_enterprise_id)],
    skill_id: Annotated[int, Path(description='skill_id')],
) -> ResponseSchemaModel[List[dict]]:
    skill = await skill_service.get_skill_by_id_visible(
        skill_id, viewer_user_id=request.user.id, viewer_enterprise_id=viewer_enterprise_id
    )
    if not skill:
        raise SkillError(code=404, msg='Skill不存在')
    contents = await skill_service.get_skill_contents(skill_id)
    return response_base.success(data=[{'file_path': c.file_path, 'content': c.content} for c in contents])


@router.post('/{skill_id}/install', summary='在线体验计数', dependencies=[DependsJwtAuth])
async def track_skill_install(
    request: Request,
    viewer_enterprise_id: Annotated[int | None, Depends(get_current_enterprise_id)],
    skill_id: Annotated[int, Path(description='skill_id')],
) -> ResponseModel:
    skill = await skill_service.get_skill_by_id_visible(
        skill_id, viewer_user_id=request.user.id, viewer_enterprise_id=viewer_enterprise_id
    )
    if not skill:
        raise SkillError(code=404, msg='Skill不存在')
    await skill_service.increment_install_count(skill_id)
    return response_base.success()


@router.get('/{username}/{skill_name}', summary='skill 详情（按可见性）', dependencies=[DependsJwtAuth])
async def get_skill_detail(
    request: Request,
    viewer_enterprise_id: Annotated[int | None, Depends(get_current_enterprise_id)],
    username: Annotated[str, Path(description='username')],
    skill_name: Annotated[str, Path(description='skill_name')],
) -> ResponseSchemaModel[GetSkillDetail | None]:
    """公开 skill 所有人可见；私有 skill 仅作者本人与其企业成员可见"""
    result = await skill_service.get_skill_for_viewer(
        username,
        skill_name,
        viewer_user_id=request.user.id,
        viewer_enterprise_id=viewer_enterprise_id,
    )
    if not result:
        raise SkillError(code=404, msg='Skill不存在')
    return response_base.success(data=result)
