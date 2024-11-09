# 作者：langjunnan
# 开发时间：2025年7月23日

from app.admin.crud.crud_user import user_dao
from app.mcp.crud.crud_mcp_category import mcp_category_dao
from app.mcp.crud.crud_mcp_server import mcp_server_dao
from app.mcp.model import McpServer
from common.exception import errors
from database.db import async_db_session
from fastmcp.mcp_config import StdioMCPServer
from sqlalchemy import Select


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
    async def get_mcp_by_user(username: str, server_name: str) -> McpServer:
        async with async_db_session() as db:
            user = await user_dao.get_by_username(db, username)
            if not user:
                raise errors.NotFoundError(msg='用户不存在')
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


mcp_server_service: McpServerService = McpServerService()
