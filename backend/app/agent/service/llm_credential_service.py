# 作者：langjunnan
# 开发时间：2025年7月23日

import hashlib

from dataclasses import dataclass
from typing import Optional

from app.agent.crud.crud_llm_credential import llm_credential_dao
from app.agent.schema.llm_credential import LlmCredentialParam, LlmCredentialTestParam
from app.admin.crud.crud_user import user_dao
from app.enterprise.model.enterprise import Enterprise
from app.enterprise.service.enterprise_service import get_user_enterprise
from common.exception import errors
from common.log import log
from core.conf import settings
from database.db import async_db_session
from sqlalchemy import select
from utils.encrypt import AESCipher

# 凭证加密器：与 MCP 用户凭证同一套 AES-CBC（hex 密钥由 TOKEN_SECRET_KEY 派生，保证稳定可解）
_cipher = AESCipher(hashlib.sha256(settings.TOKEN_SECRET_KEY.encode()).hexdigest())


@dataclass
class LlmConfig:
    """解析后的可用模型配置（已回落平台默认值）"""

    api_key: str
    base_url: str
    chat_model: str
    title_model: str
    source: str  # personal / enterprise


def _mask_key(key: str) -> str:
    if len(key) <= 8:
        return '****'
    return f'{key[:4]}****{key[-4:]}'


class LlmCredentialError(errors.BaseExceptionError):
    """模型密钥模块业务异常

    继承 BaseExceptionError 以命中全局自定义异常处理器，保证 code/msg 原样返回
    （RequestError 系列会变成无信息的 500）。
    """

    def __init__(self, *, code: int = 400, msg: str = 'Bad Request'):
        self.code = code
        super().__init__(msg=msg)


class LlmCredentialService:
    """用户/商户自己的大模型密钥：个人优先、企业共享兜底，均未配置则聊天拦截"""

    @staticmethod
    async def _get_user_enterprise(db, user_id: int) -> Enterprise | None:
        """当前用户关联的已审核通过企业（共享实现见 enterprise_service.get_user_enterprise）"""
        return await get_user_enterprise(db, user_id)

    @staticmethod
    def _decrypt_row(row) -> Optional[str]:
        try:
            return _cipher.decrypt(bytes.fromhex(row.api_key))
        except Exception as e:
            log.error('decrypt llm credential failed: {!r}', e)
            return None

    @staticmethod
    async def get_credential_status(username: str) -> dict:
        """设置页数据：个人/企业配置详情 + 平台默认值（密钥只回显掩码）"""
        async with async_db_session() as db:
            user = await user_dao.get_by_username(db, username)
            if not user:
                raise LlmCredentialError(code=404, msg=f'用户 {username} 不存在')
            personal = await llm_credential_dao.get_credential(db, user.id)
            enterprise = await LlmCredentialService._get_user_enterprise(db, user.id)
            enterprise_row = await llm_credential_dao.get_enterprise_credential(db, enterprise.id) if enterprise else None

            def _detail(row):
                if not row:
                    return {'configured': False, 'baseUrl': None, 'chatModel': None, 'titleModel': None, 'apiKeyMasked': None}
                key = LlmCredentialService._decrypt_row(row)
                return {
                    'configured': bool(row.api_key),
                    'baseUrl': row.base_url,
                    'chatModel': row.chat_model,
                    'titleModel': row.title_model,
                    'apiKeyMasked': _mask_key(key) if key else None,
                }

            return {
                'personal': _detail(personal),
                'enterprise': (
                    {'id': enterprise.id, 'name': enterprise.name, **_detail(enterprise_row)} if enterprise else None
                ),
                'defaults': {
                    'baseUrl': settings.DASHSCOPE_BASE_URL,
                    'chatModel': settings.DASHSCOPE_CHAT_MODEL,
                    'titleModel': settings.DASHSCOPE_TITLE_MODEL,
                },
            }

    @staticmethod
    async def save_credential(username: str, param: LlmCredentialParam, scope: str = 'personal') -> None:
        """保存密钥配置。api_key 留空表示沿用已保存的密钥（仅调整网关/模型）"""
        if scope not in ('personal', 'enterprise'):
            raise LlmCredentialError(msg=f'无效的密钥范围: {scope}')
        async with async_db_session.begin() as db:
            user = await user_dao.get_by_username(db, username)
            if not user:
                raise LlmCredentialError(code=404, msg=f'用户 {username} 不存在')
            enterprise_id = None
            if scope == 'enterprise':
                enterprise = await LlmCredentialService._get_user_enterprise(db, user.id)
                if not enterprise:
                    raise LlmCredentialError(code=403, msg='你还没有关联已审核通过的企业，无法配置企业共享密钥')
                enterprise_id = enterprise.id
            encrypted = _cipher.encrypt(param.api_key).hex() if param.api_key else None
            if encrypted is None:
                # 沿用旧密钥：确认对应范围确实已有配置，否则视为未配置
                existing = (
                    await llm_credential_dao.get_enterprise_credential(db, enterprise_id)
                    if enterprise_id is not None
                    else await llm_credential_dao.get_credential(db, user.id)
                )
                if not existing or not existing.api_key:
                    raise LlmCredentialError(msg='请先填写 API Key')
            await llm_credential_dao.upsert_credential(
                db,
                user.id,
                encrypted,
                enterprise_id=enterprise_id,
                base_url=param.base_url,
                chat_model=param.chat_model,
                title_model=param.title_model,
            )

    @staticmethod
    async def delete_credential(username: str, scope: str = 'personal') -> None:
        if scope not in ('personal', 'enterprise'):
            raise LlmCredentialError(msg=f'无效的密钥范围: {scope}')
        async with async_db_session.begin() as db:
            user = await user_dao.get_by_username(db, username)
            if not user:
                raise LlmCredentialError(code=404, msg=f'用户 {username} 不存在')
            if scope == 'enterprise':
                enterprise = await LlmCredentialService._get_user_enterprise(db, user.id)
                if not enterprise:
                    raise LlmCredentialError(code=403, msg='你还没有关联已审核通过的企业')
                deleted = await llm_credential_dao.delete_enterprise_credential(db, enterprise.id)
            else:
                deleted = await llm_credential_dao.delete_credential(db, user.id)
            if not deleted:
                raise LlmCredentialError(code=404, msg='未找到已配置的密钥')

    @staticmethod
    async def resolve_llm_config(db, user_id: int) -> LlmConfig | None:
        """聊天/标题生成用：解析用户可用的模型配置，个人优先、企业共享兜底；均未配置返回 None"""
        personal = await llm_credential_dao.get_credential(db, user_id)
        if personal and personal.api_key:
            key = LlmCredentialService._decrypt_row(personal)
            if key:
                return LlmConfig(
                    api_key=key,
                    base_url=personal.base_url or settings.DASHSCOPE_BASE_URL,
                    chat_model=personal.chat_model or settings.DASHSCOPE_CHAT_MODEL,
                    title_model=personal.title_model or settings.DASHSCOPE_TITLE_MODEL,
                    source='personal',
                )
        enterprise = await LlmCredentialService._get_user_enterprise(db, user_id)
        if enterprise:
            ent_row = await llm_credential_dao.get_enterprise_credential(db, enterprise.id)
            if ent_row and ent_row.api_key:
                key = LlmCredentialService._decrypt_row(ent_row)
                if key:
                    return LlmConfig(
                        api_key=key,
                        base_url=ent_row.base_url or settings.DASHSCOPE_BASE_URL,
                        chat_model=ent_row.chat_model or settings.DASHSCOPE_CHAT_MODEL,
                        title_model=ent_row.title_model or settings.DASHSCOPE_TITLE_MODEL,
                        source='enterprise',
                    )
        return None

    @staticmethod
    async def test_connection(param: LlmCredentialTestParam) -> dict:
        """用表单值直接试连一次对话补全（max_tokens=1），不落库"""
        from openai import AsyncOpenAI

        base_url = param.base_url or settings.DASHSCOPE_BASE_URL
        model = param.chat_model or settings.DASHSCOPE_CHAT_MODEL
        client = AsyncOpenAI(api_key=param.api_key, base_url=base_url, timeout=15, max_retries=0)
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[{'role': 'user', 'content': 'hi'}],
                max_tokens=1,
            )
            return {'ok': True, 'model': response.model or model}
        except Exception as e:
            log.warning('llm credential test failed against {}: {!r}', base_url, e)
            return {'ok': False, 'error': str(e)[:300]}
        finally:
            await client.close()


llm_credential_service = LlmCredentialService()
