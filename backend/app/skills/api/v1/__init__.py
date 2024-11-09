# 作者：langjunnan
# 开发时间：2025年7月23日

from app.skills.api.v1.skill import router as skill_router
from fastapi import APIRouter

router = APIRouter()
router.include_router(skill_router)
