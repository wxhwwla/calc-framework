#!/usr/bin/env python3
"""
matplotlib 中文字体配置与系统 UI 字体检测。
"""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont

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
    return str(tkfont.nametofont("TkDefaultFont").actual("family"))


def matplotlib_sans_serif_families() -> list[str]:
    families: list[str] = []
    try:
        family = system_font_family()
        if family and family not in families:
            families.append(family)
    except (tk.TclError, RuntimeError):
        pass
    for name in _MATPLOTLIB_CJK_FALLBACKS:
        if name not in families:
            families.append(name)
    if "DejaVu Sans" not in families:
        families.append("DejaVu Sans")
    return families


def configure_matplotlib_font() -> None:
    global _matplotlib_font_configured
    if _matplotlib_font_configured:
        return
    import matplotlib.pyplot as plt
    plt.rcParams["font.sans-serif"] = matplotlib_sans_serif_families()
    plt.rcParams["axes.unicode_minus"] = False
    _matplotlib_font_configured = True


def reset_matplotlib_font_config_for_tests() -> None:
    global _matplotlib_font_configured
    _matplotlib_font_configured = False
