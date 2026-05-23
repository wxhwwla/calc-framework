#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GUI 字体：与系统默认字体一致；matplotlib 图表复用同一套中文字体。"""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont

# customtkinter 仅在 default_ui_font 内按需导入，避免 pytest/脚本触发 WMI 阻塞

# 各平台常见中文字体（matplotlib 按列表顺序选用第一个可用的）
_MATPLOTLIB_CJK_FALLBACKS: tuple[str, ...] = (
    "Microsoft YaHei",
    "SimHei",
    "PingFang SC",
    "Heiti SC",
    "Noto Sans CJK SC",
    "WenQuanYi Micro Hei",
    "Arial Unicode MS",
)

_matplotlib_font_configured = False


def system_font_family() -> str:
    """返回 Tk 默认 UI 字体族名。"""
    return str(tkfont.nametofont("TkDefaultFont").actual("family"))


def default_ui_font(*, size: int = 12, weight: str = "normal"):
    """创建与系统一致的 CustomTkinter 字体。"""
    import customtkinter as ctk

    return ctk.CTkFont(family=system_font_family(), size=size, weight=weight)


def matplotlib_sans_serif_families() -> list[str]:
    """matplotlib 应使用的 sans-serif 字体列表（系统 UI 字体优先）。"""
    families: list[str] = []
    try:
        family = system_font_family()
        if family and family not in families:
            families.append(family)
    except (tk.TclError, RuntimeError):
        # 无 Tk 根窗口（pytest / 脚本）时跳过，改用下方平台中文字体列表
        pass
    for name in _MATPLOTLIB_CJK_FALLBACKS:
        if name not in families:
            families.append(name)
    if "DejaVu Sans" not in families:
        families.append("DejaVu Sans")
    return families


def configure_matplotlib_font() -> None:
    """为 matplotlib 配置中文显示（幂等，绘图前调用）。"""
    global _matplotlib_font_configured
    if _matplotlib_font_configured:
        return
    import matplotlib.pyplot as plt

    plt.rcParams["font.sans-serif"] = matplotlib_sans_serif_families()
    # 负号用 Unicode 减号，避免方块
    plt.rcParams["axes.unicode_minus"] = False
    _matplotlib_font_configured = True


def reset_matplotlib_font_config_for_tests() -> None:
    """测试专用：允许重复验证 configure_matplotlib_font。"""
    global _matplotlib_font_configured
    _matplotlib_font_configured = False
