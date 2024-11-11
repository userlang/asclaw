#!/usr/bin/env python3
# 作者：langjunnan
# 开发时间：2025年7月23日

# -*- coding: utf-8 -*-
import asyncio

from typing import Any

from celery import Task
from common.socketio.actions import task_notification
from core.conf import settings
from loguru import logger
from sqlalchemy.exc import SQLAlchemyError


class TaskBase(Task):
    """Celery 任务基类"""

    autoretry_for = (SQLAlchemyError,)
    max_retries = settings.CELERY_TASK_MAX_RETRIES

    async def before_start(self, task_id: str, args, kwargs) -> None:
        """
        任务开始前执行钩子

        :param task_id: 任务 ID
        :return:
        """
        await task_notification(msg=f'任务 {task_id} 开始执行')

    async def on_success(self, retval: Any, task_id: str, args, kwargs) -> None:
        """
        任务成功后执行钩子

        :param retval: 任务返回值
        :param task_id: 任务 ID
        :return:
        """
        await task_notification(msg=f'任务 {task_id} 执行成功')

    def on_failure(self, exc: Exception, task_id: str, args, kwargs, einfo) -> None:
        """
        任务失败后执行钩子

        :param exc: 异常对象
        :param task_id: 任务 ID
        :param einfo: 异常信息
        :return:
        """
        # on_failure 在无运行事件循环的线程中回调，不能直接 create_task（会抛
        # RuntimeError 掩盖真实错误），也不能 asyncio.run 走共享 sio/redis：
        # 临时 loop 会把连接池里绑在主 loop 上的连接用废，毒死后续所有任务。
        # 失败状态由 result backend 落 task_result 表，sync_deploy_logs 会同步进
        # deploy_log，前端部署记录可见，这里只记日志
        logger.warning(f'任务 {task_id} 执行失败: {exc!r}')
