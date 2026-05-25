#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""可换行标签布局辅助。"""

from __future__ import annotations

from utils.platform_win32_patch import apply_platform_win32_patch

apply_platform_win32_patch()
import customtkinter as ctk

from gui_design.layout.label_wrap import compute_wraplength

# 主界面各列建议最小宽度（像素）；布局常量以 gui_layout 为准
from gui_design.layout.gui_layout import (  # noqa: E402
    ATTR_COLUMN_MINSIZE,
    SELECTION_COLUMN_MINSIZE,
)

# 旧版窄列宽（仅兼容引用，新布局使用底栏）
CONTROL_COLUMN_MINSIZE = 360


def _wrap_viewport(container: ctk.CTkBaseClass) -> ctk.CTkBaseClass | None:
    """Scrollable 内层过宽时，用外层 Frame 作为可见宽度参考。"""
    if isinstance(container, ctk.CTkScrollableFrame):
        master = container.master
        if master is not None:
            return master
    return None


def bind_wrapped_label(
    label: ctk.CTkLabel,
    container: ctk.CTkBaseClass,
    *,
    padding: int = 24,
    min_wrap: int = 160,
    viewport: ctk.CTkBaseClass | None = None,
) -> None:
    """随容器/可见列宽度更新 wraplength，避免长文案在窄列中被裁切。"""
    viewport_widget = viewport if viewport is not None else _wrap_viewport(container)
    last_wrap: int | None = None

    def _update(_event: object | None = None) -> None:
        nonlocal last_wrap
        # 隐藏页签里的控件会先经历 0/1 像素过渡态，跳过可减少切页跳动感
        if not bool(container.winfo_ismapped()):
            return
        if viewport_widget is not None and not bool(viewport_widget.winfo_ismapped()):
            return
        try:
            container_width = int(container.winfo_width())
        except Exception:
            return
        if container_width <= 1:
            return
        viewport_width: int | None = None
        if viewport_widget is not None:
            try:
                viewport_width = int(viewport_widget.winfo_width())
            except Exception:
                viewport_width = None
        wrap = compute_wraplength(
            container_width,
            viewport_width=viewport_width,
            padding=padding,
            min_wrap=min_wrap,
        )
        if last_wrap == wrap:
            return
        last_wrap = wrap
        label.configure(wraplength=wrap)

    for widget in (container, label):
        widget.bind("<Configure>", _update, add="+")
    if viewport_widget is not None and viewport_widget is not container:
        viewport_widget.bind("<Configure>", _update, add="+")
    container.after_idle(_update)
