#!/usr/bin/env python3
# 作者：langjunnan
# 开发时间：2025年7月23日

# -*- coding: utf-8 -*-
from common.socketio.server import sio


async def task_notification(msg: str):
    """
    任务通知

    :param msg: 通知信息
    :return:
    """
    await sio.emit('task_notification', {'msg': msg})
