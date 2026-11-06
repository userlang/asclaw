from typing import Annotated

from app.enterprise.schema.enterprise import (
    DeleteEnterpriseParam,
    EnterpriseDetail,
    EnterpriseReviewParam,
    UpdateEnterpriseParam,
)
from app.enterprise.service.enterprise_service import enterprise_service
from common.pagination import DependsPagination, PageData, paging_data
from common.response.response_schema import ResponseModel, ResponseSchemaModel, response_base
from common.security.jwt import DependsJwtAuth
from database.db import CurrentSession, CurrentSessionTransaction
from fastapi import APIRouter, Path, Query, Request

router = APIRouter(prefix='/enterprise')


@router.post(
    '',
    summary='返回企业列表（分页，按状态筛选）',
    dependencies=[DependsPagination, DependsJwtAuth],
)
async def get_enterprises(
    db: CurrentSession,
    status: Annotated[int | None, Query(description='审核状态（0待审核 1已通过 2已拒绝），不传查全部')] = None,
    keyword: Annotated[str | None, Query(description='企业名称关键字')] = None,
) -> ResponseSchemaModel[PageData[EnterpriseDetail]]:
    enterprise_select = await enterprise_service.get_select(status=status, keyword=keyword)
    page_data = await paging_data(db, enterprise_select)
    return response_base.success(data=page_data)


@router.put(
    '/status',
    summary='批量审核（通过/拒绝）',
    dependencies=[DependsJwtAuth],
)
async def review_enterprises(
    db: CurrentSessionTransaction,
    request: Request,
    obj: EnterpriseReviewParam,
) -> ResponseModel:
    count = await enterprise_service.review(db, obj, reviewed_by=request.user.id)
    return response_base.success(data={'count': count})


@router.get(
    '/{pk}',
    summary='查询企业详情',
    dependencies=[DependsJwtAuth],
)
async def get_enterprise(pk: Annotated[int, Path(description='企业 ID')]) -> ResponseSchemaModel[EnterpriseDetail | None]:
    result = await enterprise_service.get_detail(pk)
    return response_base.success(data=result)


@router.put(
    '/{pk}',
    summary='修改企业信息 / 重置商家密码',
    dependencies=[DependsJwtAuth],
)
async def update_enterprise(
    db: CurrentSessionTransaction,
    pk: Annotated[int, Path(description='企业 ID')],
    obj: UpdateEnterpriseParam,
) -> ResponseModel:
    await enterprise_service.update(db, pk, obj)
    return response_base.success()


@router.delete(
    '',
    summary='批量删除企业',
    dependencies=[DependsJwtAuth],
)
async def delete_enterprises(
    db: CurrentSessionTransaction, obj: DeleteEnterpriseParam
) -> ResponseModel:
    count = await enterprise_service.delete_batch(db, obj.pks)
    return response_base.success(data={'count': count})
