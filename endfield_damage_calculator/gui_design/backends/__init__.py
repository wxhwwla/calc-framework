#!/usr/bin/env python3
"""
双后端切换层。

通过环境变量 ``ENDFIELD_UI_BACKEND`` 选择 GUI 后端：
  - ``"qt"``（默认）：PySide6
  - ``"ctk"``：CustomTkinter

各模块的 ``__init__.py`` 可引用 ``_BACKEND`` 来决定导入哪套实现。
"""

from __future__ import annotations

import os
from typing import Literal

_BACKEND: Literal["ctk", "qt"] = "qt"


def _detect_backend() -> Literal["ctk", "qt"]:
    env = os.environ.get("ENDFIELD_UI_BACKEND", "").strip().lower()
    if env in ("ctk", "customtkinter"):
        return "ctk"
    return "qt"


_BACKEND = _detect_backend()


def current_backend() -> Literal["ctk", "qt"]:
    return _BACKEND


def is_qt() -> bool:
    return _BACKEND == "qt"


def is_ctk() -> bool:
    return _BACKEND == "ctk"
