#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双后端切换层。

通过环境变量 ``ENDFIELD_UI_BACKEND`` 选择 GUI 后端：
  - ``"ctk"``（默认）：CustomTkinter
  - ``"qt"``：PySide6

各模块的 ``__init__.py`` 可引用 ``_BACKEND`` 来决定导入哪套实现。
"""

from __future__ import annotations

import os
from typing import Literal

_BACKEND: Literal["ctk", "qt"] = "ctk"


def _detect_backend() -> Literal["ctk", "qt"]:
    env = os.environ.get("ENDFIELD_UI_BACKEND", "").strip().lower()
    if env in ("qt", "pyside6"):
        return "qt"
    # TODO: 后续从 ui_preferences.json 读取持久化设置
    return "ctk"


_BACKEND = _detect_backend()


def current_backend() -> Literal["ctk", "qt"]:
    return _BACKEND


def is_qt() -> bool:
    return _BACKEND == "qt"


def is_ctk() -> bool:
    return _BACKEND == "ctk"
