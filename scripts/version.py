#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
项目版本号（从 _version.py 反向导入，保证单源）。

💡 版本常量已迁移到 `_version.py`，此文件为导入包装器。
"""

from __future__ import annotations

from scripts._version import _EXE_VERSION, _VERSION

__all__ = ["_EXE_VERSION", "_VERSION"]
