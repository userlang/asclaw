# 作者：langjunnan
# 开发时间：2025年7月23日

import asyncio

import copy
from collections import defaultdict
from datetime import datetime

from ag_ui.core.events import (
    EventType as AGUIEventType,
)
from ag_ui.core.events import (
    RunErrorEvent,
)
from agentscope.agent import ReActAgent
from agentscope.formatter import OpenAIChatFormatter
from agentscope.mcp import HttpStatefulClient, StdIOStatefulClient
from agentscope.memory import (
    AsyncSQLAlchemyMemory,
)
from agentscope.message import Msg
from agentscope.model import OpenAIChatModel
from agentscope.pipeline import stream_printing_messages
from agentscope.plan import PlanNotebook
from agentscope.token import OpenAITokenCounter
from agentscope.tool import Toolkit
from agentscope_runtime.engine.deployers.adapter.agui.agui_adapter_utils import AGUIAdapter
from app.agent.model.chat import AgentChat
from app.agent.schema.agent import RunBody
from app.agent.service.agent_server_service import AgentError, agent_server_service
from app.agent.service.llm_credential_service import LlmConfig, llm_credential_service
from app.mcp.schema.mcp import detect_needs_auth
from app.mcp.service.mcp_server_service import mcp_server_service
from app.skills.service.skill_service import skill_service
from common.response.response_schema import response_base
from common.security.jwt import DependsJwtAuth
from core.conf import settings
from database.chat_db import async_engine as async_chat_engine
from database.chat_db import get_db as get_chat_db
from database.db import async_db_session, get_db
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from loguru import logger
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from utils.agui import msg_to_runtime_events, sse
from utils.openai import call_model

router = APIRouter()

SSE_HEADERS = {
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'X-Accel-Buffering': 'no',
}


async def generate_title(thread_id: str, query: str, llm_config: LlmConfig):
    """异步调用 AI 生成聊天标题（用调用者自己的模型密钥）"""
    try:
        title = await call_model(
            query=query,
            api_key=llm_config.api_key,
            base_url=llm_config.base_url,
            model=llm_config.title_model,
        )
        if not title:
            title = '新对话'

        async with async_db_session() as session:
            thread = await session.get(AgentChat, thread_id)
            if thread:
                thread.chat_title = title
                thread.title_generated = True
                await session.commit()
    except Exception as e:
        logger.error('Failed to generate title for thread %s: %s', thread_id, e)


@router.post('/chat', dependencies=[DependsJwtAuth])
async def chat_endpoint(
    request: Request,
    chat_req: RunBody,
    mcps: str | None = Query(None, description='选中的MCP服务器，格式: owner/name，逗号分隔'),
    skills: str | None = Query(None, description='选中的技能，格式: owner/name，逗号分隔'),
    agent: str | None = Query(None, description='Agent 配置，格式: owner/name（加载其 mcps/skills/system_prompt）'),
    db_session: AsyncSession = Depends(get_db),
):
    thread_id = chat_req.threadId
    run_id = chat_req.runId
    user_id = str(request.user.id)
    agent_name = agent

    # 从最后一条有内容的 user 消息中提取 first_query
    first_query = ''
    for m in reversed(chat_req.messages):
        if m.role == 'user' and m.content:
            first_query = m.content
            break

    # BYOK：解析调用者自己的模型密钥（个人优先、企业共享兜底），未配置则拦截聊天并引导去设置页。
    # 放在线程持久化之前，避免被拦截的请求积累空线程
    llm_config = await llm_credential_service.resolve_llm_config(db_session, request.user.id)
    if llm_config is None:
        logger.warning('chat blocked: user {} has no llm credential', user_id)
        raise AgentError(code=403, msg='尚未配置模型密钥，请先在「设置 → 模型密钥」中完成配置')

    # 持久化聊天线程元信息
    existing = await db_session.get(AgentChat, thread_id)
    if not existing:
        chat_thread = AgentChat(
            thread_id=thread_id,
            user_id=user_id,
            first_query=first_query,
            chat_title='新对话',
            title_generated=False,
            start_time=datetime.now(),
        )
        db_session.add(chat_thread)
        await db_session.commit()
        need_title = True
    else:
        need_title = not existing.title_generated

    # 异步生成标题
    if need_title and first_query:
        asyncio.create_task(generate_title(thread_id, first_query, llm_config))

    # type=agent 时：加载 agent 配置，把它的 mcps/skills 并入请求参数，system_prompt 作为主提示词
    agent_system_prompt: str | None = None
    agent_prologue: str | None = None
    if agent_name:  # 从 ?agent=owner/name 传入
        try:
            a_owner, a_name = agent_name.split('/', 1)
            agent = await agent_server_service.get_public_agent_by_user(username=a_owner, agent_name=a_name)
            if agent:
                agent_system_prompt = agent.system_prompt
                agent_prologue = agent.prologue
                agent_mcps = [m for m in (agent.mcps or []) if isinstance(m, str)]
                agent_skills = [s for s in (agent.skills or []) if isinstance(s, str)]
                if agent_mcps:
                    mcps = f'{mcps},{",".join(agent_mcps)}' if mcps else ','.join(agent_mcps)
                if agent_skills:
                    skills = f'{skills},{",".join(agent_skills)}' if skills else ','.join(agent_skills)
        except Exception as e:
            logger.warning('Failed to load agent config {}: {}', agent_name, e)

    # 加载选中的 MCP 配置（在生成器外提前加载，避免在 async generator 中做 DB 操作）
    mcp_configs: list[tuple[str, dict, str]] = []  # (name, config, transport)
    if mcps:
        for item in mcps.split(','):
            item = item.strip()
            if '/' not in item:
                continue
            owner, server_name = item.split('/', 1)
            try:
                mcp_server = await mcp_server_service.get_mcp_by_owner_name(owner=owner, server_name=server_name)
                if not mcp_server or not mcp_server.server_config:
                    continue
                # 可见性：非本人只能使用公开 MCP，防止猜 owner/name 拉起私有服务
                is_owner = mcp_server.user_id == request.user.id
                if not is_owner and not mcp_server.is_public:
                    logger.warning('MCP {}/{} not public, skip for user {}', owner, server_name, user_id)
                    continue
                # 凭证：非 owner 一律先剥离配置里的鉴权材料（header + URL 敏感参数），
                # 需要鉴权的 MCP 必须叠加调用者自己的凭证（个人优先、企业共享兜底），
                # 严禁沿用 owner 的 token
                server_needs_auth = detect_needs_auth(mcp_server.server_config, mcp_server.transport)
                for mcp_name, mcp_cfg in mcp_server.server_config.get('mcpServers', {}).items():
                    if is_owner:
                        mcp_configs.append((mcp_name, mcp_cfg, mcp_server.transport))
                        continue
                    if not server_needs_auth:
                        # 无鉴权材料，配置本身可安全复用
                        mcp_configs.append((mcp_name, copy.deepcopy(mcp_cfg), mcp_server.transport))
                        continue
                    user_credential, cred_source = await mcp_server_service.resolve_user_credential(
                        db_session, request.user.id, mcp_server.id
                    )
                    if not user_credential:
                        logger.warning(
                            'MCP {}/{} requires auth but user {} has no credential, skip',
                            owner,
                            server_name,
                            user_id,
                        )
                        continue
                    logger.info('MCP {}/{} uses {} credential', owner, server_name, cred_source)
                    sanitized_cfg = mcp_server_service.sanitize_server_config(copy.deepcopy(mcp_cfg))
                    merged_cfg = mcp_server_service.apply_credential_to_config(sanitized_cfg, user_credential)
                    mcp_configs.append((mcp_name, merged_cfg, mcp_server.transport))

            except Exception as e:
                logger.warning('Failed to load MCP {}: {}', item, e)

    # 加载选中的技能：描述 + SKILL.md 正文拼入 sys_prompt，并累计使用次数
    skill_parts: list[str] = []
    if skills:
        for item in skills.split(','):
            item = item.strip()
            if '/' not in item:
                continue
            owner, skill_name = item.split('/', 1)
            try:
                skill = await skill_service.get_skill_by_user(username=owner, skill_name=skill_name)
                if skill and skill.description:
                    part = f"Skill '{skill.title}': {skill.description}"
                    if skill.body:
                        part += f"\n{skill.body}"
                    skill_parts.append(part)
                if skill:
                    await skill_service.increment_install_count(skill.id)
            except Exception as e:
                logger.warning('Failed to load skill {}: {}', item, e)

    if agent_system_prompt:
        sys_prompt = agent_system_prompt
    else:
        sys_prompt = '你是一个名为 Jarvis 的助手'
    if skill_parts:
        sys_prompt += '\n\n可用技能:\n' + '\n'.join(skill_parts)

    async def event_generator():
        adapter = AGUIAdapter(thread_id=thread_id, run_id=run_id)
        # Track cumulative text length per msg.id to compute delta
        text_sent_len: dict[str, int] = defaultdict(int)

        # 注意：这里必须传 engine 而不是 Depends 注入的 chat_db_session。
        # 原因：AsyncSQLAlchemyMemory 内部 add() 的写入顺序是
        #   ① session.add(message)（未 flush，挂在 session 里）
        #   ② bulk_insert_mappings(message_mark)（bulk 路径绕过 ORM flush）
        # 内部自建 session（autoflush 默认 True）会在 bulk 前自动 flush 消息，外键满足；
        # 而 database/chat_db.py 的 sessionmaker 配了 autoflush=False，
        # 传入该 session 时 ② 先于 ① 落库，触发 message_mark.ibfk_1 外键错误
        #（ReActAgent 的 HINT/COMPRESSED mark 全部中招）。
        # 传 engine 则由 memory 自建 session（autoflush=True），不受影响。
        memory = AsyncSQLAlchemyMemory(
            engine_or_session=async_chat_engine,
            user_id=user_id,
            session_id=thread_id,
        )

        toolkit = Toolkit()
        mcp_clients: list[HttpStatefulClient | StdIOStatefulClient] = []

        try:
            for name, config, transport in mcp_configs:
                if transport == 'stdio':
                    stdio_config = {
                        'command': config.get('command'),
                        'args': config.get('args'),
                        'env': config.get('env'),
                        'cwd': config.get('cwd'),
                    }
                    stdio_client = StdIOStatefulClient(
                        name=name,
                        **stdio_config,
                    )
                    await stdio_client.connect()
                    await toolkit.register_mcp_client(stdio_client)
                    mcp_clients.append(stdio_client)
                elif transport == 'sse':
                    sse_config = {
                        'transport': 'sse',
                        'url': config.get('url'),
                        'headers': config.get('headers'),
                        'timeout': config.get('timeout'),
                        'sse_read_timeout': config.get('sse_read_timeout'),
                    }
                    stateful_client = HttpStatefulClient(
                        name=name,
                        **sse_config,
                    )

                    await stateful_client.connect()
                    await toolkit.register_mcp_client(stateful_client)
                    mcp_clients.append(stateful_client)
                elif transport == 'streamable_http':
                    http_config = {
                        'transport': 'streamable_http',
                        'url': config.get('url'),
                        'headers': config.get('headers'),
                        'timeout': config.get('timeout'),
                        'sse_read_timeout': config.get('sse_read_timeout'),
                    }
                    stateful_client = HttpStatefulClient(
                        name=name,
                        **http_config,
                    )

                    await stateful_client.connect()
                    await toolkit.register_mcp_client(stateful_client)
                    mcp_clients.append(stateful_client)

            agent = ReActAgent(
                # agent 名字，出现在消息的 name 字段里，前端用它区分是谁说的话
                name='Jarvis',
                # 系统提示词：由「基础人设 + 已选技能描述」拼成（见上方 sys_prompt 拼接逻辑）
                sys_prompt=sys_prompt,
                # 对话模型：OpenAI 兼容客户端，指向调用者自己配置的网关（BYOK，未配置已在入口拦截）
                model=OpenAIChatModel(
                    model_name=llm_config.chat_model,
                    api_key=llm_config.api_key,
                    stream=True,
                    client_kwargs={'base_url': llm_config.base_url},
                ),
                # 短期记忆：AsyncSQLAlchemyMemory 持久化到 asclaw_chat 库（按 user_id + thread_id 隔离）
                memory=memory,
                # 消息格式化器：把 agentscope Msg 列表转成 OpenAI chat 格式
                formatter=OpenAIChatFormatter(),
                # 工具箱：已注册选中的 MCP 客户端（每个 MCP server 的工具都在这里）
                toolkit=toolkit,
                # ============ 以下为本次学习补全的参数（原代码只配了上面 7 个） ============

                # 长期记忆（跨会话）：暂不启用。启用需要向量库/外部服务（Mem0 / ReMe），
                # 留 None 时 agent 只用上面的短期记忆。
                # 若以后想加：long_term_memory=Mem0LongTermMemory(...) 并配合 mode 使用
                long_term_memory=None,
                # 长期记忆模式（只有配了 long_term_memory 才生效）：
                #   agent_control  → 注册 retrieve/record 两个工具，模型自己决定何时存取
                #   static_control → 每轮回复前自动检索、回复后自动记录，模型无感知
                #   both           → 两者都开
                long_term_memory_mode='both',
                # 元工具：给 agent 一个 reset_equipped_tools 工具，让它能自己启停工具组
                #（如 plan_related 组）。配合 plan_notebook 才有意义
                enable_meta_tool=True,
                # 并行工具调用：模型一轮生成多个 tool_call 时并发执行（asyncio.gather）。
                # 注意：多个 MCP 工具并发调用时，模型必须正确填参数；排错困难时可关掉
                parallel_tool_calls=True,
                # RAG 知识库：本项目未接（agentscope KnowledgeBase 需要文档源），留 None
                knowledge=None,
                # 检索前改写查询（"我是谁" → "{用户名}"），只配了 knowledge 才生效，保持默认
                enable_rewrite_query=True,
                # 任务规划本：让 agent 把复杂任务拆成子任务清单、逐个推进。
                # max_subtasks 限制单个计划的子任务数，防止无限拆分
                plan_notebook=PlanNotebook(max_subtasks=8),
                # 调试开关：把规划提示/记忆检索等 hint 消息也推给前端（SSE 里多一种事件）。
                # hint 仍会进 memory 参与推理（agentscope 设计如此），关掉只影响前端展示——
                # 开着会把 agentscope 的英文规划提示（"If the user's query is complex...create_plan"）
                # 当作消息文本渲染到聊天窗口，用户可见，故关闭
                print_hint_msg=False,
                # ReAct 循环最大轮数（默认 10）。MCP 编排类任务链路长，调到 25；
                # 超限后 _summarizing() 会强制模型总结当前进展作为回答，不会崩
                max_iters=25,
                # 语音合成模型：不需要，留 None
                tts_model=None,
                # 记忆自动压缩：对话 token 超阈值时，把较早的历史压缩成结构化摘要
                #（任务概览/当前状态/关键发现/下一步/需保留上下文 五段），
                # 最近 keep_recent 条保持原文。
                # counter 用 OpenAITokenCounter（tiktoken 本地计数，不联网、不花 token）；
                # qwen 不在 tiktoken 模型表里会自动 fallback 到 o200k_base 编码，够准
                compression_config=ReActAgent.CompressionConfig(
                    enable=True,
                    agent_token_counter=OpenAITokenCounter('gpt-4o'),
                    trigger_threshold=24000,
                    keep_recent=4,
                ),
            )

            async for msg, last in stream_printing_messages(
                agents=[agent],
                coroutine_task=agent(
                    Msg('user', first_query or '', 'user'),
                ),
            ):
                # Convert Msg chunk -> runtime Content events
                runtime_events = msg_to_runtime_events(
                    msg,
                    last,
                    text_sent_len,
                )
                # Feed each runtime event through AGUIAdapter
                for rt_event in runtime_events:
                    agui_events = adapter.convert_agent_event_to_agui_events(
                        rt_event,
                    )
                    for agui_event in agui_events:
                        yield sse(agui_event)

            # Ensure RUN_FINISHED
            if not adapter.run_finished_emitted:
                yield sse(
                    adapter.build_run_event(
                        event_type=AGUIEventType.RUN_FINISHED,
                    )
                )

            # 更新 end_time
            async with async_db_session() as session:
                thread = await session.get(AgentChat, thread_id)
                if thread:
                    thread.end_time = datetime.now()
                    await session.commit()

        except Exception as e:
            logger.error('Failed to load thread %s: %s', thread_id, e)
            error_event = RunErrorEvent(
                message=f'Unexpected stream error: {e}',
                code='internal_error',
            )
            yield sse(error_event)

        finally:
            # Close MCP clients in LIFO order
            for client in reversed(mcp_clients):
                await client.close()

    return StreamingResponse(
        event_generator(),
        media_type='text/event-stream',
        headers=SSE_HEADERS,
    )


@router.get('/threads', dependencies=[DependsJwtAuth])
async def list_threads(
    request: Request,
    db_session: AsyncSession = Depends(get_db),
):
    """消息摘要列表"""
    user_id = str(request.user.id)
    result = await db_session.execute(
        select(AgentChat).where(AgentChat.user_id == user_id).order_by(AgentChat.start_time.desc())
    )
    threads = result.scalars().all()
    return response_base.success(
        data=[
            {
                'thread_id': t.thread_id,
                'chat_title': t.chat_title,
            }
            for t in threads
        ]
    )


@router.get('/threads/{thread_id}', dependencies=[DependsJwtAuth])
async def get_thread(
    request: Request,
    thread_id: str,
    db_session: AsyncSession = Depends(get_db),
):
    """获取线程详情（含 title_generated，用于前端轮询）"""
    thread = await db_session.get(AgentChat, thread_id)
    if not thread or thread.user_id != str(request.user.id):
        return response_base.success(
            data={
                'thread_id': thread_id,
                'chat_title': '新对话',
                'title_generated': False,
            }
        )
    return response_base.success(
        data={
            'thread_id': thread.thread_id,
            'chat_title': thread.chat_title,
            'title_generated': thread.title_generated,
        }
    )


@router.delete('/threads/{thread_id}', dependencies=[DependsJwtAuth])
async def delete_thread(
    request: Request,
    thread_id: str,
    db_session: AsyncSession = Depends(get_db),
    chat_db_session: AsyncSession = Depends(get_chat_db),
):
    """删除对话：清理主库线程元信息与聊天库消息（幂等，不存在或非本人时同样返回成功）"""
    thread = await db_session.get(AgentChat, thread_id)
    if thread and thread.user_id == str(request.user.id):
        # 聊天库按外键依赖顺序清理：message_mark（无 session_id，需经 message 关联）→ message → session
        await chat_db_session.execute(
            text('DELETE FROM message_mark WHERE msg_id IN (SELECT id FROM message WHERE session_id = :tid)'),
            {'tid': thread_id},
        )
        await chat_db_session.execute(text('DELETE FROM message WHERE session_id = :tid'), {'tid': thread_id})
        await chat_db_session.execute(text('DELETE FROM session WHERE id = :tid'), {'tid': thread_id})
        await chat_db_session.commit()
        await db_session.delete(thread)
        await db_session.commit()
    return response_base.success()


@router.get('/threads/{thread_id}/messages', dependencies=[DependsJwtAuth])
async def get_thread_messages(
    request: Request,
    thread_id: str,
    db_session: AsyncSession = Depends(get_chat_db),
):
    user_id = str(request.user.id)
    async with AsyncSQLAlchemyMemory(
        engine_or_session=db_session,
        user_id=user_id,
        session_id=thread_id,
    ) as memory:
        msgs = await memory.get_memory()

    agui_messages = []
    for msg in msgs:
        d = msg if isinstance(msg, dict) else msg.to_dict()
        role = d.get('role', 'user')
        content = d.get('content', '')
        # Flatten content blocks to plain text if needed
        if isinstance(content, list):
            content = ''.join(b.get('text', '') for b in content if isinstance(b, dict) and b.get('type') == 'text')
        content = str(content).strip()
        # 过滤掉空内容和 system 角色的中间消息（ReAct tool call/result）
        if not content or role == 'system':
            continue
        agui_msg = {
            'id': d.get('id', ''),
            'role': role,
            'content': content,
        }
        agui_messages.append(agui_msg)

    return response_base.success(data=agui_messages)
