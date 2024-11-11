# 作者：langjunnan
# 开发时间：2025年7月23日

import asyncio
import re

from agentscope.mcp import HttpStatefulClient
from app.admin.crud.crud_user import user_dao
from app.mcp.crud.crud_mcp_server import mcp_server_dao
from app.mcp.model import McpServer
from app.mcp.schema.enums import CompileType, ServerType, TransportType
from app.mcp.schema.mcp import AddMcpServerParam
from common.exception import errors
from database.db import async_db_session
from fastmcp import Client
from fastmcp.mcp_config import MCPConfig, RemoteMCPServer
from loguru import logger


class CompileMcpService:
    async def judge_mcp_transport(self, transport, url):
        # CancelledError 继承自 BaseException 而非 Exception，
        # MCP 连接失败时 anyio cancel-scope 会抛出它，必须显式捕获
        base_exceptions = (Exception, asyncio.CancelledError)
        try:
            stateful_client = HttpStatefulClient(
                name='mcp_services_stateful',
                transport=transport,
                url=url,
            )
            await stateful_client.connect()
            tools = await stateful_client.list_tools()
            logger.info(f'tools: {tools}')
            await stateful_client.close()
            return transport
        except base_exceptions as e:
            logger.error(f'judge_mcp_transport {transport} failed: {e!r}')
            fallback = 'sse' if transport == 'streamable_http' else 'streamable_http'
            # 用 fallback 协议再探测一次，成功则以 fallback 为准
            try:
                stateful_client = HttpStatefulClient(
                    name='mcp_services_stateful',
                    transport=fallback,
                    url=url,
                )
                await stateful_client.connect()
                tools = await stateful_client.list_tools()
                logger.info(f'tools: {tools}')
                await stateful_client.close()
                return fallback
            except base_exceptions as e2:
                logger.error(f'judge_mcp_transport {fallback} failed: {e2!r}')
                # 两个协议都失败，返回原值走后续正常报错流程
                return transport

    async def compile_mcp_by_mcp_config(self, mcp_user: str, obj_data: dict):
        mcp_server_param = AddMcpServerParam(**obj_data)
        mcp_servers = mcp_server_param.mcpServers.mcpServers
        mcp_config = MCPConfig(mcpServers=mcp_servers)
        # 和serverInfo.name不一定一样
        mcp_name = list(mcp_config.mcpServers.keys())[0]
        # server_name 用于详情路由 /api/v1/mcp/{username}/{server_name}，
        # 配置键里的 / ? # % 等字符会拆断 URL 路径（如 “本地/云端文件处理”），统一替换成 -
        server_name = re.sub(r'[/\\?#%]+', '-', mcp_name)
        server_cfg = mcp_config.mcpServers[mcp_name]

        transport = TransportType.stdio.name
        logger.info(f'server_cfg: {server_cfg}, {type(server_cfg)}')
        if isinstance(server_cfg, RemoteMCPServer):
            mcp_transport = await self.judge_mcp_transport('streamable_http', server_cfg.url)
            logger.info(f'mcp_transport: {mcp_transport}')
            if mcp_transport == 'sse':
                transport = TransportType.sse.name
            elif mcp_transport == 'streamable_http':
                transport = TransportType.streamable_http.name

        async with Client(mcp_config) as client:
            await client.ping()
            server_meta = client.initialize_result

            capability_map = {
                'tools': client.list_tools_mcp,
                'resources': client.list_resources_mcp,
                'prompts': client.list_prompts_mcp,
            }

            results = {}
            for name, fetch_fn in capability_map.items():
                enabled = getattr(server_meta.capabilities, name, False)
                if not enabled:
                    results[name] = None
                    continue
                try:
                    fn_result = (await fetch_fn()).model_dump(mode='json').get(name)
                    if fn_result:
                        results[name] = fn_result
                    else:
                        results[name] = None
                except Exception as e:
                    logger.warning(f'Fetch {name} failed: {e}')
                    results[name] = None

            # 本地/远程以 transport 为准：stdio 是本地进程，sse/streamable_http 是远程服务
            server_type = ServerType.local.name if transport == TransportType.stdio.name else ServerType.remote.name

            mcp_server = McpServer(
                server_title=mcp_server_param.server_title,
                server_name=server_name,
                transport=transport,
                server_type=server_type,
                compile_type=CompileType.package.name,
                server_config=mcp_config.model_dump(mode='json'),
                server_metadata=server_meta.model_dump(mode='json'),
                tools=results['tools'],
                resources=results['resources'],
                prompts=results['prompts'],
                description=mcp_server_param.description,
                avatar=f'https://api.dicebear.com/9.x/bottts/svg?seed={server_meta.serverInfo.name}',
            )
            logger.info('compile mcp_server success')
            async with async_db_session.begin() as db:
                user = await user_dao.get_by_username(db, mcp_user)
                if not user:
                    raise errors.NotFoundError(msg=f'用户 {mcp_user} 不存在')
                existing = await mcp_server_dao.get_by_user_and_title(db, user.id, mcp_server_param.server_title)
                if existing:
                    raise errors.ConflictError(msg=f'已存在同名 MCP：{mcp_server_param.server_title}')
                mcp_server.user_id = user.id
                await mcp_server_dao.add_mcp(db, mcp_server)
            return f'compile mcp_server success: {obj_data}'


compile_mcp_service = CompileMcpService()
