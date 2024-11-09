# 作者：langjunnan
# 开发时间：2025年7月23日

from app.admin.schema.token import GetLoginToken
from database.db import CurrentSessionTransaction
from fastapi import APIRouter, BackgroundTasks, Request, Response

from app.enterprise.schema.enterprise import EnterpriseApplyParam, EnterpriseLoginParam
from app.enterprise.service.enterprise_service import enterprise_service
from common.response.response_schema import ResponseModel, ResponseSchemaModel, response_base

router = APIRouter()


@router.post('/apply', summary='企业入驻申请')
async def apply_enterprise(
    db: CurrentSessionTransaction, obj: EnterpriseApplyParam
) -> ResponseModel:
    """提交入驻申请，保存后等待管理员审核；审核通过后才能登录"""
    await enterprise_service.apply(db, obj)
    return response_base.success()


@router.post('/login', summary='企业登录')
async def enterprise_login(
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    obj: EnterpriseLoginParam,
) -> ResponseSchemaModel[GetLoginToken]:
    """企业账号登录，签发标准用户 JWT；非企业用户名回退到平台用户密码登录"""
    data = await enterprise_service.login(
        request=request,
        response=response,
        background_tasks=background_tasks,
        username=obj.username,
        password=obj.password,
    )
    return response_base.success(data=data)
