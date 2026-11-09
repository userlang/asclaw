#!/usr/bin/env python3
# 作者：langjunnan
# 开发时间：2025年7月23日

# -*- coding: utf-8 -*-
from common.schema import SchemaBase


class TaskRegisteredDetail(SchemaBase):
    name: str
    task: str
