#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GUI 字体：与系统默认字体一致。"""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont

import customtkinter as ctk


def system_font_family() -> str:
    """返回 Tk 默认 UI 字体族名。"""
    return str(tkfont.nametofont("TkDefaultFont").actual("family"))


def default_ui_font(*, size: int = 12, weight: str = "normal") -> ctk.CTkFont:
    """创建与系统一致的 CustomTkinter 字体。"""
    return ctk.CTkFont(family=system_font_family(), size=size, weight=weight)
