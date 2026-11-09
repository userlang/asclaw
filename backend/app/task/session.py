#!/usr/bin/env python3
# 作者：langjunnan
# 开发时间：2025年7月23日

# -*- coding: utf-8 -*-
from celery.backends.database.session import SessionManager as CelerySessionManager


class SessionManager(CelerySessionManager):
    """
    重写 celery SessionManager
    """

    def __init__(self):
        super().__init__()

        # 禁止自动创建 celery 内部定义的任务结果表
        self.prepared = True
