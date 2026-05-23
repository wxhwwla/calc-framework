#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""可换行标签布局辅助。"""

from __future__ import annotations

import customtkinter as ctk

# 主界面各列建议最小宽度（像素）
SELECTION_COLUMN_MINSIZE = 260
CONTROL_COLUMN_MINSIZE = 360
ATTR_COLUMN_MINSIZE = 168


def bind_wrapped_label(
    label: ctk.CTkLabel,
    container: ctk.CTkBaseClass,
    *,
    padding: int = 24,
    min_wrap: int = 160,
) -> None:
    """随容器宽度更新 wraplength，避免长文案在窄列中被裁切。"""

    def _update(_event: object | None = None) -> None:
        try:
            width = int(container.winfo_width())
        except Exception:
            return
        if width <= padding:
            return
        label.configure(wraplength=max(min_wrap, width - padding))

    container.bind("<Configure>", _update, add="+")
    label.bind("<Configure>", _update, add="+")
    container.after_idle(_update)
