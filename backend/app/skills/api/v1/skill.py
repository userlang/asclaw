from typing import Annotated, List

from app.admin.schema.skill import AdminSkillBaseDetail
from app.mcp.schema.skill import GetSkillDetail, SkillCategoryDetail, SkillDetail
from app.skills.service.skill_service import skill_service
from common.exception import errors
from common.pagination import DependsPagination, PageData, paging_data
from common.response.response_schema import ResponseSchemaModel, response_base
from common.security.jwt import DependsJwtAuth
from database.db import CurrentSession
from fastapi import APIRouter, Path, Query, Request

router = APIRouter()


@router.get(
    '/',
    summary='搜索skill',
    dependencies=[DependsPagination],
)
async def search_skill(
    db: CurrentSession,
    keyword: str | None = Query(None, description='搜索词'),
    category_id: int | None = Query(None, description='分类id'),
) -> ResponseSchemaModel[PageData[SkillDetail]]:
    skill_select = await skill_service.get_select(keyword=keyword, category_id=category_id)
    page_data = await paging_data(db, skill_select)
    return response_base.success(data=page_data)


@router.get('/categories', summary='skill categories')
async def get_skill_categories() -> ResponseSchemaModel[List[SkillCategoryDetail]]:
    result = await skill_service.get_categories()
    return response_base.success(data=result)


@router.get('/{username}/{skill_name}', summary='skill detail')
async def get_skill_detail(
    username: Annotated[str, Path(description='username')],
    skill_name: Annotated[str, Path(description='skill_name')],
) -> ResponseSchemaModel[GetSkillDetail | None]:
    result = await skill_service.get_public_skill_by_user(username=username, skill_name=skill_name)
    if not result:
        raise errors.NotFoundError(msg='Skill不存在')
    return response_base.success(data=result)


@router.get(
    '/mine',
    summary='获取我的 skill 列表',
    dependencies=[DependsJwtAuth, DependsPagination],
)
async def get_my_skills(
    request: Request,
    db: CurrentSession,
) -> ResponseSchemaModel[PageData[AdminSkillBaseDetail]]:
    skill_select = await skill_service.get_my_skills(user_id=request.user.id)
    page_data = await paging_data(db, skill_select)
    return response_base.success(data=page_data)
