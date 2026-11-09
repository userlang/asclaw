#!/usr/bin/env python3
# 作者：langjunnan
# 开发时间：2025年7月23日

# -*- coding: utf-8 -*-
from app.admin.api.router import v1 as admin_v1
from app.agent.api.router import v1 as agent_v1
from app.enterprise.api.router import v1 as enterprise_v1
from app.mcp.api.router import v1 as mcp_v1
from app.skills.api.router import v1 as skill_v1
from app.task.api.router import v1 as task_v1
from fastapi import APIRouter

router = APIRouter()

router.include_router(task_v1)
router.include_router(mcp_v1)
router.include_router(admin_v1)
router.include_router(agent_v1)
router.include_router(skill_v1)
router.include_router(enterprise_v1)
