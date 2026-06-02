# SPDX-License-Identifier: AGPL-3.0
"""主题管理器 — 多主题定义 + Qt 样式表渲染。



支持内置主题（light / dark）和从 .calcpack 加载的自定义主题。

提供运行时切换能力。

"""



from __future__ import annotations

from typing import Any

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget

from .theme_presets import _BUILTIN_THEMES


def _build_stylesheet(theme: dict[str, Any]) -> str:

    """从主题字典生成 Qt 样式表。"""

    colors = theme.get("colors", {})

    bg = colors.get("background", "#1E1E1E")

    surface = colors.get("surface", "#2D2D2D")

    text = colors.get("text", "#F0F0F0")

    text_sec = colors.get("text_secondary", "#A0A0A0")

    border = colors.get("border", "#3D3D3D")

    primary = colors.get("primary", "#0078D4")

    primary_hover = colors.get("primary_hover", "#1E8EE8")

    success = colors.get("success", "#4CAF50")

    warning = colors.get("warning", "#FF9800")

    error = colors.get("error", "#F44336")

    input_bg = colors.get("input_bg", "#3C3C3C")

    scrollbar = colors.get("scrollbar", "#555555")

    scrollbar_hover = colors.get("scrollbar_hover", "#777777")



    return f"""

        QMainWindow, QWidget#centralWidget {{ background-color: {bg}; }}

        QGroupBox {{

            background-color: {surface};

            border: 1px solid {border};

            border-radius: 6px;

            margin-top: 8px;

            padding-top: 16px;

            font-weight: bold;

            color: {text};

        }}

        QGroupBox::title {{

            subcontrol-origin: margin;

            subcontrol-position: top left;

            padding: 2px 8px;

            color: {text};

        }}

        QLabel {{ color: {text}; }}

        QLabel#valueLabel {{

            color: {primary};

            font-weight: bold;

        }}

        QLabel#secondaryLabel {{

            color: {text_sec};

        }}

        QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {{

            background-color: {input_bg};

            color: {text};

            border: 1px solid {border};

            border-radius: 4px;

            padding: 2px 6px;

        }}

        QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover, QLineEdit:hover {{

            border: 1px solid {primary};

        }}

        QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus {{

            border: 1px solid {primary};

        }}

        QComboBox::drop-down {{

            border: none;

            background: {surface};

        }}

        QComboBox QAbstractItemView {{

            background-color: {surface};

            color: {text};

            selection-background-color: {primary};

            selection-color: {text};

            border: 1px solid {border};

        }}

        QPushButton {{

            background-color: {primary};

            color: {text};

            border: none;

            border-radius: 4px;

            padding: 6px 16px;

            font-weight: bold;

        }}

        QPushButton:hover {{

            background-color: {primary_hover};

        }}

        QPushButton:pressed {{

            background-color: {primary};

        }}

        QPushButton:disabled {{

            background-color: {border};

            color: {text_sec};

        }}

        QScrollArea {{ background-color: transparent; border: none; }}

        QScrollBar:vertical {{

            background: {bg};

            width: 10px;

            margin: 0;

        }}

        QScrollBar::handle:vertical {{

            background: {scrollbar};

            min-height: 20px;

            border-radius: 5px;

        }}

        QScrollBar::handle:vertical:hover {{

            background: {scrollbar_hover};

        }}

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{

            height: 0;

        }}

        QScrollBar:horizontal {{

            background: {bg};

            height: 10px;

            margin: 0;

        }}

        QScrollBar::handle:horizontal {{

            background: {scrollbar};

            min-width: 20px;

            border-radius: 5px;

        }}

        QScrollBar::handle:horizontal:hover {{

            background: {scrollbar_hover};

        }}

        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{

            width: 0;

        }}

        QSlider::groove:horizontal {{

            background: {input_bg};

            height: 6px;

            border-radius: 3px;

        }}

        QSlider::handle:horizontal {{

            background: {primary};

            width: 16px;

            height: 16px;

            margin: -5px 0;

            border-radius: 8px;

        }}

        QSlider::handle:horizontal:hover {{

            background: {primary_hover};

        }}

        QSlider::sub-page:horizontal {{

            background: {primary};

            border-radius: 3px;

        }}

        QCheckBox {{

            color: {text};

            spacing: 6px;

        }}

        QCheckBox::indicator {{

            width: 16px;

            height: 16px;

            border-radius: 3px;

            border: 1px solid {border};

            background: {input_bg};

        }}

        QCheckBox::indicator:checked {{

            background: {primary};

            border-color: {primary};

        }}

        QStatusBar {{

            background: {surface};

            color: {text_sec};

            border-top: 1px solid {border};

        }}

        QMenuBar {{

            background: {surface};

            color: {text};

            border-bottom: 1px solid {border};

        }}

        QMenuBar::item:selected {{

            background: {primary};

        }}

        QMenu {{

            background: {surface};

            color: {text};

            border: 1px solid {border};

        }}

        QMenu::item:selected {{

            background: {primary};

        }}

        QSplitter::handle {{

            background: {border};

            width: 1px;

        }}

        QProgressBar {{

            background: {input_bg};

            border: 1px solid {border};

            border-radius: 4px;

            text-align: center;

            color: {text};

        }}

        QProgressBar::chunk {{

            background: {primary};

            border-radius: 3px;

        }}

    """





class ThemeManager:

    """主题管理器 — 管理内置主题和自定义主题，支持运行时切换。"""



    def __init__(self) -> None:

        self._themes: dict[str, dict[str, Any]] = {}

        self._current: str = "dark"

        for key, theme in _BUILTIN_THEMES.items():

            self._themes[key] = theme



    @property

    def theme_names(self) -> list[str]:

        """theme_names。"""
        return list(self._themes.keys())



    @property

    def current_name(self) -> str:
        """current_name。"""

        return self._current



    @property
    def current_display_name(self) -> str:

        theme = self._themes.get(self._current, {})

        return theme.get("name", self._current)



    def get_theme(self, name: str) -> dict[str, Any] | None:

        return self._themes.get(name)



    def register(self, name: str, theme: dict[str, Any]) -> None:

        self._themes[name] = theme



    def switch(self, name: str) -> str:

        if name not in self._themes:

            available = ", ".join(self._themes.keys())

            raise KeyError(f"未知主题 '{name}'，可用主题: {available}")

        self._current = name

        return _build_stylesheet(self._themes[name])



    def stylesheet(self, name: str | None = None) -> str:

        target = name or self._current

        theme = self._themes.get(target)

        if theme is None:

            theme = _BUILTIN_THEMES["dark"]

        return _build_stylesheet(theme)



    def apply_font(self, theme: dict[str, Any], widget: QWidget) -> None:

        font_cfg = theme.get("font", {})

        family = font_cfg.get("family", "")

        size = font_cfg.get("size", 0)

        if family or size:

            font = QFont(family, size or 12)

            widget.setFont(font)

