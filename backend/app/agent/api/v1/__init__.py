# 作者：langjunnan
# 开发时间：2025年7月23日

from app.agent.api.v1.agent import router as agent_router
from app.agent.api.v1.llm_credential import router as llm_credential_router
from app.agent.api.v1.thread import router as thread_router
from fastapi import APIRouter

router = APIRouter()
# 静态前缀路由（/threads/...、/llm-credential）必须先于动态路径参数路由（/{username}/{agent_name}）注册，
# 否则 GET /agent/threads/{id} 会被 get_agent_detail 捕获（username='threads'），
# 触发 NotFoundError → 前端弹窗报错。
router.include_router(thread_router)
router.include_router(llm_credential_router)
router.include_router(agent_router)
