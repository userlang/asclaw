# 作者：langjunnan
# 开发时间：2025年7月23日

import re

from app.admin.crud.crud_user import user_dao
from app.agent.crud.crud_agent_category import agent_category_dao
from app.agent.crud.crud_agent_server import agent_server_dao
from app.agent.model import AgentServer
from app.mcp.crud.crud_mcp_server import mcp_server_dao
from app.skills.crud.crud_skill import skill_dao
from common.exception import errors
from database.db import async_db_session
from loguru import logger
from sqlalchemy import Select

# 引用只要求传输格式合法：单斜杠分隔、不含逗号（逗号是 ?mcps= 列表分隔符）、两段非空。
# 名字本身允许空格/中文等字符（compile 只消毒 / \ ? # %，server_name 原样入库）
_ITEM_RE = re.compile(r'^[^/,]+/[^/,]+$')


class AgentError(errors.BaseExceptionError):
    """agent 模块业务异常

    继承 BaseExceptionError 以命中全局自定义异常处理器，
    保证 code/msg 原样返回（RequestError 系列会变成无信息的 500）。
    """

    def __init__(self, *, code: int = 400, msg: str = 'Bad Request'):
        self.code = code
        super().__init__(msg=msg)


class AgentServerService:
    @staticmethod
    async def get_select(*, keyword: str, category_id: int) -> Select:
        return await agent_server_dao.get_list(keyword=keyword, category_id=category_id)

    @staticmethod
    async def get_categories() -> list:
        async with async_db_session() as db:
            stmt = await agent_category_dao.get_all_categories()
            result = await db.execute(stmt)
            return result.scalars().all()

    @staticmethod
    async def get_public_agent_by_user(username: str, agent_name: str) -> AgentServer | None:
        """获取用户已公开的 agent 详情（详情页 + chat 配置加载共用）"""
        async with async_db_session() as db:
            user = await user_dao.get_by_username(db, username)
            if not user:
                # NotFoundError 继承 BaseExceptionMixin，不在全局异常处理器树里，
                # 会变成无信息的 500；必须用 AgentError（BaseExceptionError 子类）
                raise AgentError(code=404, msg='Agent不存在')
            return await agent_server_dao.get_by_user_and_name(db, agent_name, user.id, is_public=True)

    @staticmethod
    async def get_agent_by_user(username: str, agent_name: str) -> AgentServer | None:
        """获取用户的 agent（不限公开状态，本人配置页用）"""
        async with async_db_session() as db:
            user = await user_dao.get_by_username(db, username)
            if not user:
                raise AgentError(code=404, msg='Agent不存在')
            return await agent_server_dao.get_by_user_and_name(db, agent_name, user.id)

    @staticmethod
    async def _validate_bindings(db, user_id: int, mcps: list[str], skills: list[str]) -> None:
        """校验 mcps/skills 引用格式与归属：必须是自己名下存在的资源"""
        for label, items, dao_getter in (
            ('MCP', mcps, AgentServerService._check_mcp),
            ('Skill', skills, AgentServerService._check_skill),
        ):
            for item in items:
                if not _ITEM_RE.match(item):
                    raise AgentError(msg=f'{label} 引用格式错误：{item}（应为 owner/name）')
                await dao_getter(db, user_id, item)

    @staticmethod
    async def _check_mcp(db, user_id: int, item: str) -> None:
        owner, server_name = item.split('/', 1)
        # MCP 引用要求是自己的资源：owner 必须等于引用者（与 chat 加载逻辑一致）
        mcp = await mcp_server_dao.get_mcp_with_user(db, server_name, user_id)
        if not mcp:
            raise AgentError(msg=f'MCP 不存在或无权引用：{item}')

    @staticmethod
    async def _check_skill(db, user_id: int, item: str) -> None:
        owner, skill_name = item.split('/', 1)
        skill = await skill_dao.get_by_name_and_user(db, skill_name, user_id)
        if not skill:
            raise AgentError(msg=f'Skill 不存在或无权引用：{item}')

    @staticmethod
    async def publish_agent(
        *,
        user_id: int,
        name: str,
        title: str,
        avatar: str | None = None,
        description: str | None = None,
        system_prompt: str | None = None,
        prologue: str | None = None,
        mcps: list[str] | None = None,
        skills: list[str] | None = None,
        enable_search: bool = False,
        enable_multimodal: bool = False,
        enable_suggest: bool = False,
        is_public: bool = True,
        category_id: int | None = None,
    ) -> AgentServer:
        """创建 agent：校验引用归属后落库"""
        mcps = mcps or []
        skills = skills or []
        async with async_db_session.begin() as db:
            user = await user_dao.get(db, user_id)
            if not user:
                raise AgentError(msg='用户不存在')

            existing = await agent_server_dao.get_by_user_and_name(db, name, user_id)
            if existing:
                raise AgentError(msg=f'你已存在同名 agent：{name}')

            if category_id is not None:
                stmt = await agent_category_dao.get_all_categories()
                result = await db.execute(stmt)
                valid_ids = {c.id for c in result.scalars().all()}
                if category_id not in valid_ids:
                    raise AgentError(msg='分类不存在')

            await AgentServerService._validate_bindings(db, user_id, mcps, skills)

            agent = AgentServer(
                name=name,
                title=title,
                avatar=avatar or '',
                description=description,
                system_prompt=system_prompt,
                prologue=prologue or '',
                mcps=mcps,
                skills=skills,
                enable_search=enable_search,
                enable_multimodal=enable_multimodal,
                enable_suggest=enable_suggest,
                is_public=is_public,
                category_id=category_id,
                user_id=user_id,
            )
            # user 关系是 lazy viewonly，新建对象不会自动加载；响应序列化读 data.user.username，
            # 不补上的话 owner 返回空串 → 前端跳 /agent/me/{name} → 404 "Agent不存在"
            agent.user = user
            db.add(agent)
            await db.flush()
            return agent

    @staticmethod
    async def update_agent(*, user_id: int, agent_id: int, **fields) -> int:
        """更新自己的 agent（字段级更新，mcps/skills 变更时重新校验归属）"""
        mcps = fields.pop('mcps', None)
        skills = fields.pop('skills', None)
        category_id = fields.pop('category_id', None)
        async with async_db_session.begin() as db:
            agent = await agent_server_dao.select_model(db, pk=agent_id)
            if not agent:
                raise AgentError(code=404, msg='Agent 不存在')
            if agent.user_id != user_id:
                raise AgentError(code=403, msg='无权修改他人的 agent')

            if mcps is not None or skills is not None:
                await AgentServerService._validate_bindings(
                    db, user_id, mcps if mcps is not None else (agent.mcps or []),
                    skills if skills is not None else (agent.skills or []),
                )
                if mcps is not None:
                    agent.mcps = mcps
                if skills is not None:
                    agent.skills = skills

            if category_id is not None:
                stmt = await agent_category_dao.get_all_categories()
                result = await db.execute(stmt)
                valid_ids = {c.id for c in result.scalars().all()}
                if category_id not in valid_ids:
                    raise AgentError(msg='分类不存在')
                agent.category_id = category_id

            for key, value in fields.items():
                if value is not None and hasattr(agent, key):
                    setattr(agent, key, value)
            return 1

    @staticmethod
    async def delete_agent(*, user_id: int, agent_id: int) -> int:
        async with async_db_session.begin() as db:
            agent = await agent_server_dao.select_model(db, pk=agent_id)
            if not agent:
                raise AgentError(code=404, msg='Agent 不存在')
            if agent.user_id != user_id:
                raise AgentError(code=403, msg='无权删除他人的 agent')
            return await agent_server_dao.delete_model(db, agent_id)


agent_server_service: AgentServerService = AgentServerService()
