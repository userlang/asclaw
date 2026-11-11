# 作者：langjunnan
# 开发时间：2025年7月23日

from common.response.response_schema import ResponseModel, ResponseSchemaModel, response_base
from common.security.jwt import DependsJwtAuth
from fastapi import APIRouter, Query, Request

from app.agent.schema.llm_credential import LlmCredentialParam, LlmCredentialTestParam
from app.agent.service.llm_credential_service import llm_credential_service

router = APIRouter()


@router.get('/llm-credential', summary='查询我的模型密钥配置', dependencies=[DependsJwtAuth])
async def get_llm_credential(request: Request) -> ResponseSchemaModel[dict]:
    """返回个人/企业配置详情（密钥仅掩码回显）与平台默认值，供设置页一次拉齐"""
    result = await llm_credential_service.get_credential_status(request.user.username)
    return response_base.success(data=result)


@router.put('/llm-credential', summary='保存我的模型密钥', dependencies=[DependsJwtAuth])
async def update_llm_credential(
    request: Request,
    obj: LlmCredentialParam,
    scope: str = Query('personal', description='密钥范围：personal=个人 / enterprise=企业共享'),
) -> ResponseModel:
    """AES 加密落库，仅本人（或企业全体成员）可用；重复提交覆盖"""
    await llm_credential_service.save_credential(request.user.username, obj, scope=scope)
    return response_base.success()


@router.delete('/llm-credential', summary='清除我的模型密钥', dependencies=[DependsJwtAuth])
async def delete_llm_credential(
    request: Request,
    scope: str = Query('personal', description='密钥范围：personal=个人 / enterprise=企业共享'),
) -> ResponseModel:
    await llm_credential_service.delete_credential(request.user.username, scope=scope)
    return response_base.success()


@router.post('/llm-credential/test', summary='测试模型网关连通性', dependencies=[DependsJwtAuth])
async def test_llm_credential(obj: LlmCredentialTestParam) -> ResponseSchemaModel[dict]:
    """用表单值直接试连一次对话补全（不落库），返回 ok / 错误信息"""
    result = await llm_credential_service.test_connection(obj)
    return response_base.success(data=result)
