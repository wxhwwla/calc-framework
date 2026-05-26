#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI 设置模块

此模块包含 GUI 全局设置初始化函数和常量定义。

字体规范：所有 CTk 文本控件（CTkButton / CTkLabel / CTkEntry / CTkOptionMenu /
CTkCheckBox / CTkSwitch / CTkComboBox / CTkTextbox）必须在创建时显式传入 ``font=``
参数，字体通过 ``default_ui_font()`` 或 ``app.small_font`` / ``app.big_font`` 创建，
确保与系统 UI 字体（TkDefaultFont）保持一致。

全局兜底：``configure_tk_default_font()`` 在 CTk 根窗口创建后立即被调用，
将 TkDefaultFont 覆写为系统字体；``configure_all_tk_fonts()`` 在所有
widget 构建完毕后再次遍历所有 ``ctk_font_*`` 命名字体统一族名，覆盖
CTkTabview 页签、CTkOptionMenu 下拉等内部控件自行创建的字体。
"""

from utils.platform_win32_patch import apply_platform_win32_patch

apply_platform_win32_patch()
import customtkinter as ctk

from utils.gui_fonts import system_font_family


def configure_tk_default_font(root: ctk.CTk) -> None:
    """根窗口创建后立即调用：覆写 TkDefaultFont 与 CTk 主题默认字体族名。

    两步缺一不可：
    1. ``font configure TkDefaultFont`` — 修复 tk 层（显式传了 font= 的控件）
    2. ``ThemeManager.theme["CTkFont"]["family"]`` — 修复 CTk 内部
       ``CTkFont()`` 无参构造路径（DropdownMenu、CTkTabview 页签等动态创建的
       字体均从此取值）
    """
    family = system_font_family()
    if not family:
        return
    try:
        root.tk.call("font", "configure", "TkDefaultFont", "-family", family)
    except Exception:
        pass
    try:
        ctk.ThemeManager.theme["CTkFont"]["family"] = family
    except Exception:
        pass


def configure_all_tk_fonts(root: ctk.CTk) -> None:
    """在所有 widget 创建完毕后调用，统一全部字体族名为系统字体。

    CTk 内部控件（CTkTabview 页签、CTkOptionMenu / CTkComboBox 下拉菜单等）
    在运行时动态创建 ``CTkFont()``，其默认 family 取自
    ``ThemeManager.theme["CTkFont"]["family"]``。本函数在该值已覆写为系统字体
    之后，遍历所有 tk 命名字体强制同步（包括 CTk 创建的 ``font1``/``font2``/…
    以及 tk 标准的 TkDefaultFont / TkMenuFont 等）。
    """
    family = system_font_family()
    if not family:
        return

    _TK_STANDARD_FONTS = (
        "TkDefaultFont",
        "TkTextFont",
        "TkFixedFont",
        "TkMenuFont",
        "TkHeadingFont",
        "TkCaptionFont",
        "TkSmallCaptionFont",
        "TkIconFont",
        "TkTooltipFont",
    )
    for std_name in _TK_STANDARD_FONTS:
        try:
            root.tk.call("font", "configure", std_name, "-family", family)
        except Exception:
            pass

    try:
        names = root.tk.call("font", "names")
    except Exception:
        return
    for font_name in names:
        if not isinstance(font_name, str):
            continue
        try:
            root.tk.call("font", "configure", font_name, "-family", family)
        except Exception:
            pass


def gui_settings() -> None:
    """
    初始化 GUI 全局设置

    功能：
    1. 设置应用外观模式为深色模式（"dark"）
    2. 设置应用颜色主题为蓝色（"blue"）

    调用时机：应在创建任何 CTk 组件之前调用

    示例：
        gui_settings()  # 在创建 CTk 窗口之前调用
    """
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
