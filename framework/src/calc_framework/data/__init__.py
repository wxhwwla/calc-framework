#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""数据引擎子包 — DataContext、加载器接口、属性 Schema、变量校验。"""

from calc_framework.data.attr_schema import AttributeDecl, AttributeSchema
from calc_framework.data.context import DataContext, make_context
from calc_framework.data.loader import DataContextLoader

__all__ = [
    "AttributeDecl",
    "AttributeSchema",
    "DataContext",
    "DataContextLoader",
    "make_context",
]
