# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""PySide6 后端 — 将 Qt 特定操作隔离到此模块。

此模块提供需要 PySide6 的辅助函数，供 UI 层调用。
核心逻辑（ThemeManager 等）保持纯 Python，不依赖此模块。
"""

from __future__ import annotations

from typing import Any

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget


def apply_font(theme: dict[str, Any], widget: QWidget) -> None:
    """将主题字体配置应用到 QWidget。

    Args:
        theme: 主题字典，需包含 ``font`` 键。
        widget: 目标 Qt 控件。
    """
    font_cfg = theme.get("font", {})
    family = font_cfg.get("family", "")
    size = font_cfg.get("size", 0)
    if family or size:
        font = QFont(family, size or 12)
        widget.setFont(font)
