#!/usr/bin/env python3
# 作者：langjunnan
# 开发时间：2025年7月23日

# -*- coding: utf-8 -*-
from common.enums import IntEnum, StrEnum


class TaskSchedulerType(IntEnum):
    """任务调度类型"""

    INTERVAL = 0
    CRONTAB = 1


class PeriodType(StrEnum):
    """周期类型"""

    DAYS = 'days'
    HOURS = 'hours'
    MINUTES = 'minutes'
    SECONDS = 'seconds'
    MICROSECONDS = 'microseconds'
