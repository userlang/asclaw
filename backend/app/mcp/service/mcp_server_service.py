# 作者：langjunnan
# 开发时间：2025年7月23日

import copy
import hashlib
import json

from app.admin.crud.crud_user import user_dao
from app.enterprise.model.enterprise import Enterprise
from app.enterprise.service.enterprise_service import get_user_enterprise
from app.mcp.crud.crud_mcp_category import mcp_category_dao
from app.mcp.crud.crud_mcp_credential import CRUDMcpUserCredential
from app.mcp.crud.crud_mcp_server import mcp_server_dao
from app.mcp.model import McpServer
from app.mcp.model.credential import McpUserCredential
from app.mcp.schema.mcp import detect_auth_header_keys, detect_needs_auth
from common.exception import errors
from core.conf import settings
from database.db import async_db_session
from fastmcp.mcp_config import StdioMCPServer
from loguru import logger
from sqlalchemy import Select, select
from sqlalchemy.orm import noload, selectinload
from utils.encrypt import AESCipher


class McpError(errors.BaseExceptionError):
    """mcp 模块业务异常

    继承 BaseExceptionError 以命中全局自定义异常处理器，
    保证 code/msg 原样返回（RequestError 系列会变成无信息的 500）。
    """

    def __init__(self, *, code: int = 400, msg: str = 'Bad Request'):
        self.code = code
        super().__init__(msg=msg)


class McpServerService:
    @staticmethod
    def get_base_image(cmd) -> str:
        # bun deno 支持
        base_image = {
            'npx': 'registry.cn-beijing.aliyuncs.com/biyao/public:asclaw-node20-v3',
            'node': 'registry.cn-beijing.aliyuncs.com/biyao/public:asclaw-node20-v3',
            'uvx': 'registry.cn-beijing.aliyuncs.com/biyao/public:asclaw-python3.10-v8',
            'python': 'registry.cn-beijing.aliyuncs.com/biyao/public:asclaw-python3.10-v8',
        }
        return base_image[cmd]

    @staticmethod
    def compile_command(mcp_conf: StdioMCPServer):
        base_command = [
            'mcp-proxy',
            '--sse-port',
            '8080',
            '--sse-host',
            '0.0.0.0',
            '--allow-origin',
            '*',
            '--pass-environment',
            '--',
            mcp_conf.command,
        ]
        base_command.extend(mcp_conf.args)
        return base_command

    @staticmethod
    async def get_select(*, keyword: str, category_id: int) -> Select:
        return await mcp_server_dao.get_list(keyword, category_id)

    @staticmethod
    async def get_mcp_last_7_day():
        async with async_db_session() as db:
            stmt = await mcp_server_dao.get_mcp_last_7_day()
            result = await db.execute(stmt)
            return result.scalars().all()

    @staticmethod
    async def get_mcp(pk: int) -> McpServer:
        async with async_db_session() as db:
            return await mcp_server_dao.get_mcp(db, pk)

    @staticmethod
    async def get_mcp_by_id(mcp_id: int) -> McpServer:
        """按 id 查 MCP 详情；user 预加载供响应序列化（owner 字段），不存在抛 404"""
        async with async_db_session() as db:
            stmt = (
                select(McpServer)
                .where(McpServer.id == mcp_id)
                .options(selectinload(McpServer.user), noload(McpServer.category))
            )
            result = await db.execute(stmt)
            mcp_server = result.scalars().first()
            if not mcp_server:
                raise McpError(code=404, msg='MCP 不存在')
            return mcp_server

    @staticmethod
    async def get_mcp_by_owner_name(owner: str, server_name: str) -> McpServer | None:
        """按 owner/name 查 MCP，供聊天绑定（mcps=owner/name）解析；查不到返回 None"""
        async with async_db_session() as db:
            user = await user_dao.get_by_username(db, owner)
            if not user:
                return None
            return await mcp_server_dao.get_mcp_with_user(db, server_name, user.id)

    @staticmethod
    async def get_recommend_mcp() -> list:
        async with async_db_session() as db:
            stmt = await mcp_server_dao.get_recommend_mcp()
            result = await db.execute(stmt)
            return result.scalars().all()

    @staticmethod
    async def get_categories() -> list:
        async with async_db_session() as db:
            stmt = await mcp_category_dao.get_all_categories()
            result = await db.execute(stmt)
            return result.scalars().all()

    @staticmethod
    async def update_cover(username: str, mcp_id: int, cover: str | None) -> None:
        """仅允许 MCP 创建者修改自己的封面"""
        async with async_db_session.begin() as db:
            user = await user_dao.get_by_username(db, username)
            if not user:
                raise McpError(code=404, msg=f'用户 {username} 不存在')
            mcp_server = await mcp_server_dao.get_mcp(db, mcp_id)
            if not mcp_server or mcp_server.user_id != user.id:
                raise McpError(code=404, msg='MCP 不存在')
            mcp_server.cover = cover

    @staticmethod
    async def update_avatar(username: str, mcp_id: int, avatar: str | None) -> None:
        """仅允许 MCP 创建者修改自己的头像；置空则回落默认机器人头像"""
        async with async_db_session.begin() as db:
            user = await user_dao.get_by_username(db, username)
            if not user:
                raise McpError(code=404, msg=f'用户 {username} 不存在')
            mcp_server = await mcp_server_dao.get_mcp(db, mcp_id)
            if not mcp_server or mcp_server.user_id != user.id:
                raise McpError(code=404, msg='MCP 不存在')
            mcp_server.avatar = avatar

    @staticmethod
    async def update_public(username: str, mcp_id: int, is_public: int) -> None:
        """仅允许 MCP 创建者切换公开/私有；公开后出现在广场"""
        async with async_db_session.begin() as db:
            user = await user_dao.get_by_username(db, username)
            if not user:
                raise McpError(code=404, msg=f'用户 {username} 不存在')
            mcp_server = await mcp_server_dao.get_mcp(db, mcp_id)
            if not mcp_server or mcp_server.user_id != user.id:
                raise McpError(code=404, msg='MCP 不存在')
            mcp_server.is_public = 1 if is_public else 0

    # ---------- 广场凭证：MCP 为模板，token 各自配置 ----------

    # 凭证加密器：AES-CBC 真加密（ItsDangerous 只签名不加密，明文可解码）。
    # AESCipher 要求 hex 密钥，TOKEN_SECRET_KEY 是 base64url，用 sha256 派生稳定的 32 字节 hex 密钥
    _cipher = AESCipher(hashlib.sha256(settings.TOKEN_SECRET_KEY.encode()).hexdigest())

    credential_dao: CRUDMcpUserCredential = CRUDMcpUserCredential(McpUserCredential)

    @staticmethod
    async def _get_user_enterprise(db, user_id: int) -> Enterprise | None:
        """当前用户关联的已审核通过企业（共享实现见 enterprise_service.get_user_enterprise）"""
        return await get_user_enterprise(db, user_id)

    @staticmethod
    async def get_credential_status(username: str, mcp_id: int) -> dict:
        """凭证配置状态：是否需要 token、需要的 header 键、个人/企业配置情况"""
        async with async_db_session() as db:
            user = await user_dao.get_by_username(db, username)
            if not user:
                raise McpError(code=404, msg=f'用户 {username} 不存在')
            mcp_server = await mcp_server_dao.get_mcp(db, mcp_id)
            if not mcp_server:
                raise McpError(code=404, msg='MCP 不存在')
            personal = await McpServerService.credential_dao.get_credential(db, user.id, mcp_server.id)
            enterprise = await McpServerService._get_user_enterprise(db, user.id)
            enterprise_row = (
                await McpServerService.credential_dao.get_enterprise_credential(db, enterprise.id, mcp_server.id)
                if enterprise
                else None
            )
            return {
                'needs_auth': detect_needs_auth(mcp_server.server_config, mcp_server.transport),
                'auth_keys': detect_auth_header_keys(mcp_server.server_config),
                'configured': personal is not None and bool(personal.credential),
                'enterprise': (
                    {
                        'id': enterprise.id,
                        'name': enterprise.name,
                        'configured': enterprise_row is not None and bool(enterprise_row.credential),
                    }
                    if enterprise
                    else None
                ),
            }

    @staticmethod
    async def save_credential(username: str, mcp_id: int, headers: dict, scope: str = 'personal') -> None:
        """保存当前用户对某个广场 MCP 的凭证（整体加密落库）

        scope=personal：个人凭证；scope=enterprise：企业共享凭证（要求用户关联已通过审核的企业）
        """
        if not headers or not all(isinstance(k, str) and k and isinstance(v, str) and v for k, v in headers.items()):
            raise McpError(msg='凭证格式无效：应为非空的 {header名: 值} 字典')
        if scope not in ('personal', 'enterprise'):
            raise McpError(msg=f'无效的凭证范围: {scope}')
        async with async_db_session.begin() as db:
            user = await user_dao.get_by_username(db, username)
            if not user:
                raise McpError(code=404, msg=f'用户 {username} 不存在')
            mcp_server = await mcp_server_dao.get_mcp(db, mcp_id)
            if not mcp_server:
                raise McpError(code=404, msg='MCP 不存在')
            enterprise_id = None
            if scope == 'enterprise':
                enterprise = await McpServerService._get_user_enterprise(db, user.id)
                if not enterprise:
                    raise McpError(code=403, msg='你还没有关联已审核通过的企业，无法配置企业共享凭证')
                enterprise_id = enterprise.id
            encrypted = McpServerService._cipher.encrypt(json.dumps(headers, ensure_ascii=False)).hex()
            await McpServerService.credential_dao.upsert_credential(
                db, user.id, mcp_server.id, encrypted, enterprise_id=enterprise_id
            )

    @staticmethod
    async def delete_credential(username: str, mcp_id: int, scope: str = 'personal') -> None:
        if scope not in ('personal', 'enterprise'):
            raise McpError(msg=f'无效的凭证范围: {scope}')
        async with async_db_session.begin() as db:
            user = await user_dao.get_by_username(db, username)
            if not user:
                raise McpError(code=404, msg=f'用户 {username} 不存在')
            if scope == 'enterprise':
                enterprise = await McpServerService._get_user_enterprise(db, user.id)
                if not enterprise:
                    raise McpError(code=403, msg='你还没有关联已审核通过的企业')
                deleted = await McpServerService.credential_dao.delete_enterprise_credential(
                    db, enterprise.id, mcp_id
                )
            else:
                deleted = await McpServerService.credential_dao.delete_credential(db, user.id, mcp_id)
            if not deleted:
                raise McpError(code=404, msg='未找到已配置的凭证')

    @staticmethod
    async def resolve_user_credential(db, user_id: int, mcp_server_id: int) -> tuple[dict | None, str | None]:
        """聊天合并用：解析某用户对某 MCP 可用的凭证，个人优先、企业共享兜底

        返回 (headers, source)，source ∈ {'personal', 'enterprise', None}
        """
        personal = await McpServerService.credential_dao.get_credential(db, user_id, mcp_server_id)
        if personal and personal.credential:
            try:
                return json.loads(McpServerService._cipher.decrypt(bytes.fromhex(personal.credential))), 'personal'
            except Exception as e:
                logger.error(f'decrypt personal credential failed: {e!r}')
        # 企业共享凭证：用户关联的已审核企业配置的凭证
        enterprise = await McpServerService._get_user_enterprise(db, user_id)
        if enterprise:
            ent_row = await McpServerService.credential_dao.get_enterprise_credential(
                db, enterprise.id, mcp_server_id
            )
            if ent_row and ent_row.credential:
                try:
                    return (
                        json.loads(McpServerService._cipher.decrypt(bytes.fromhex(ent_row.credential))),
                        'enterprise',
                    )
                except Exception as e:
                    logger.error(f'decrypt enterprise credential failed: {e!r}')
        return None, None

    @staticmethod
    async def get_configured_credential_server_ids(username: str) -> list[int]:
        """当前用户已配置凭证的 MCP id 并集（个人 + 其企业共享），供前端过滤聊天可选列表"""
        async with async_db_session() as db:
            user = await user_dao.get_by_username(db, username)
            if not user:
                raise McpError(code=404, msg=f'用户 {username} 不存在')
            enterprise = await McpServerService._get_user_enterprise(db, user.id)
            return await McpServerService.credential_dao.get_user_credential_server_ids(
                db, user.id, enterprise.id if enterprise else None
            )

    # ---------- 凭证净化/叠加（防止 owner 的 token 被其他用户沿用） ----------

    @staticmethod
    def sanitize_server_config(cfg: dict) -> dict:
        """深度拷贝并剥离配置里的鉴权材料：敏感 header 清空、URL 敏感参数移除。

        用于非 owner 用户：先剥掉 owner 的 token，再叠加调用者自己的凭证。
        """
        from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

        from app.mcp.schema.mcp import _URL_SENSITIVE_PARAMS, _AUTH_HEADER_PATTERN

        sanitized = copy.deepcopy(cfg)
        headers = sanitized.get('headers')
        if isinstance(headers, dict):
            sanitized['headers'] = {
                k: v for k, v in headers.items()
                if not any(p in k.lower() for p in _AUTH_HEADER_PATTERN)
            }
        url = sanitized.get('url')
        if isinstance(url, str) and url:
            try:
                parts = urlsplit(url)
                kept = [
                    (k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
                    if k.lower() not in _URL_SENSITIVE_PARAMS
                ]
                if kept != parse_qsl(parts.query, keep_blank_values=True):
                    sanitized['url'] = urlunsplit(parts._replace(query=urlencode(kept)))
            except ValueError:
                pass
        return sanitized

    @staticmethod
    def apply_credential_to_config(cfg: dict, credential: dict) -> dict:
        """把用户自己的凭证叠加到（已净化的）配置上。

        credential 形如 {"Authorization": "Bearer x", "url:key": "xxx"}：
        普通键 → headers；'url:' 前缀键 → 替换 URL query 中的同名参数。
        """
        from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

        from app.mcp.schema.mcp import URL_PARAM_PREFIX

        merged = dict(cfg)
        url_params = {k[len(URL_PARAM_PREFIX):]: v for k, v in credential.items() if k.startswith(URL_PARAM_PREFIX)}
        headers = {k: v for k, v in credential.items() if not k.startswith(URL_PARAM_PREFIX)}
        if headers:
            merged_headers = dict(merged.get('headers') or {})
            merged_headers.update(headers)
            merged['headers'] = merged_headers
        if url_params:
            url = merged.get('url')
            if isinstance(url, str) and url:
                try:
                    parts = urlsplit(url)
                    kept = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k not in url_params]
                    kept.extend(url_params.items())
                    merged['url'] = urlunsplit(parts._replace(query=urlencode(kept)))
                except ValueError:
                    pass
        return merged


mcp_server_service: McpServerService = McpServerService()
