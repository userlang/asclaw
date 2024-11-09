#!/usr/bin/env python3
# 作者：langjunnan
# 开发时间：2025年7月23日

# -*- coding: utf-8 -*-
from app.admin.api.v1.oauth.google import router as google_router
from fastapi import APIRouter

router = APIRouter(prefix='/oauth')

router.include_router(google_router, tags=['Google oauth登录'])
