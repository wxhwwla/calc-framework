#!/usr/bin/env python3
"""GUI 后端：统一提供 PySide6（Qt）引用标记。"""

from __future__ import annotations

from typing import Literal

_BACKEND: Literal["qt"] = "qt"


def current_backend() -> Literal["qt"]:
    return _BACKEND


def is_qt() -> bool:
    return True
