#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""数据沙箱 — 在隔离环境中测试自定义游戏数据。

数据沙箱提供一个 CLI 工具集，允许用户在本地测试自定义角色/武器 JSON 数据，
**不会修改任何真实数据文件**。所有操作基于临时/内存数据。

使用方式::

    # CLI
    python -m tools.data_sandbox.sandbox validate my_data.json
    python -m tools.data_sandbox.sandbox test my_data.json
    python -m tools.data_sandbox.sandbox report my_data.json -o report.md
    python -m tools.data_sandbox.sandbox diff my_data.json reference.json

    # 程序化使用
    from tools.data_sandbox import Validator, Tester, Reporter
    v = Validator()
    errors = v.validate(my_data)
"""

from .validator import Validator, ValidationResult
from .tester import Tester, TestResult
from .reporter import Reporter, Report

__all__ = [
    "Report",
    "Reporter",
    "TestResult",
    "Tester",
    "ValidationResult",
    "Validator",
]
