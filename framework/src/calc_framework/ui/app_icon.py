# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""应用图标与 Windows 任务栏身份。

开发模式下查看器/启动器由 ``pythonw`` 启动；若不给窗口设置图标，
Windows 会回退显示解释器的蛇形图标，用户容易把它当成残留的控制台窗口。
这里用 QPainter 现场绘制图标，不依赖外部资源文件，PyInstaller 打包后同样可用。
"""

from __future__ import annotations

import sys
from contextlib import suppress

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication

__all__ = ["apply_application_identity", "build_app_icon"]

_ICON_SIZES = (16, 32, 48, 64, 256)
_BACKGROUND = "#1B2436"
_ACCENT = "#4FC3F7"
_KEY = "#E6EDF3"
_EQUALS = "#FFB74D"


def _render_pixmap(size: int) -> QPixmap:
    """按边长绘制一张计算器风格图标。

    Args:
        size: 正方形位图的边长（像素）。

    Returns:
        带透明背景的图标位图。
    """
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    try:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        unit = float(size)

        def rect(x: float, y: float, width: float, height: float) -> QRectF:
            return QRectF(x * unit, y * unit, width * unit, height * unit)

        margin = 0.04 * unit
        painter.setPen(QPen(QColor(_ACCENT), max(1.0, 0.035 * unit)))
        painter.setBrush(QColor(_BACKGROUND))
        painter.drawRoundedRect(
            QRectF(margin, margin, unit - 2 * margin, unit - 2 * margin),
            0.18 * unit,
            0.18 * unit,
        )

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(_ACCENT))
        painter.drawRoundedRect(rect(0.18, 0.16, 0.64, 0.20), 0.03 * unit, 0.03 * unit)

        painter.setBrush(QColor(_KEY))
        for row in (0.44, 0.62):
            for column in (0.18, 0.40, 0.62):
                painter.drawRoundedRect(rect(column, row, 0.20, 0.13), 0.025 * unit, 0.025 * unit)

        painter.setBrush(QColor(_EQUALS))
        painter.drawRoundedRect(rect(0.18, 0.82, 0.64, 0.08), 0.02 * unit, 0.02 * unit)
    finally:
        painter.end()
    return pixmap


def build_app_icon() -> QIcon:
    """构造多尺寸应用图标（不依赖外部资源文件）。"""
    icon = QIcon()
    for size in _ICON_SIZES:
        icon.addPixmap(_render_pixmap(size))
    return icon


def _set_windows_app_id(app_id: str) -> None:
    """Windows 下声明独立 AppUserModelID，避免任务栏按解释器归类。"""
    if sys.platform != "win32":
        return

    import ctypes

    with suppress(AttributeError, OSError):
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)  # type: ignore[attr-defined]


def apply_application_identity(app: QApplication, app_id: str = "CalcFramework.Desktop") -> None:
    """给 QApplication 设置窗口图标与任务栏身份。

    Args:
        app: 已创建的 QApplication。
        app_id: Windows AppUserModelID；同一应用应保持一致。
    """
    app.setWindowIcon(build_app_icon())
    _set_windows_app_id(app_id)
