# SPDX-License-Identifier: AGPL-3.0
"""内置主题预设 — 亮色/暗色/高对比度主题数据。"""

from __future__ import annotations

from typing import Any

_BUILTIN_THEMES: dict[str, dict[str, Any]] = {

    "dark": {

        "name": "深色",

        "colors": {

            "background": "#1E1E1E",

            "surface": "#2D2D2D",

            "text": "#F0F0F0",

            "text_secondary": "#A0A0A0",

            "border": "#3D3D3D",

            "primary": "#0078D4",

            "primary_hover": "#1E8EE8",

            "success": "#4CAF50",

            "warning": "#FF9800",

            "error": "#F44336",

            "input_bg": "#3C3C3C",

            "scrollbar": "#555555",

            "scrollbar_hover": "#777777",

        },

        "font": {"family": "", "size": 0},

    },

    "light": {

        "name": "浅色",

        "colors": {

            "background": "#F5F5F5",

            "surface": "#FFFFFF",

            "text": "#212121",

            "text_secondary": "#757575",

            "border": "#E0E0E0",

            "primary": "#1976D2",

            "primary_hover": "#1565C0",

            "success": "#388E3C",

            "warning": "#F57C00",

            "error": "#D32F2F",

            "input_bg": "#FAFAFA",

            "scrollbar": "#BDBDBD",

            "scrollbar_hover": "#9E9E9E",

        },

        "font": {"family": "", "size": 0},

    },

    "high_contrast": {

        "name": "高对比",

        "colors": {

            "background": "#000000",

            "surface": "#1A1A1A",

            "text": "#FFFFFF",

            "text_secondary": "#CCCCCC",

            "border": "#FFFFFF",

            "primary": "#FFFF00",

            "primary_hover": "#FFEA00",

            "success": "#00FF00",

            "warning": "#FFA500",

            "error": "#FF0000",

            "input_bg": "#2A2A2A",

            "scrollbar": "#888888",

            "scrollbar_hover": "#AAAAAA",

        },

        "font": {"family": "", "size": 0},

    },

}
