#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
GUI 壳层：主窗口与应用生命周期。

子模块（mixin）：
- app：DamageCalculatorApp 组合入口
- app_main_layout：计算页五列 + 高级页 dock 骨架
- app_selection：trace 绑定与页签切换
- app_window / app_window_events：响应式布局与窗口防抖
- app_char_weapon_link：角色→武器类型过滤
- app_control_dock：高级页三列控件
- app_loadout_bridge / app_loadout_access：配装刮取与预览候选
"""

from __future__ import annotations

from typing import Literal

__all__ = [
    "app",
    "app_char_weapon_link",
    "app_control_dock",
    "app_loadout_access",
    "app_loadout_bridge",
    "app_main_layout",
    "app_selection",
    "app_window",
    "app_window_events",
]

_BACKEND: Literal["qt"] = "qt"


def current_backend() -> Literal["qt"]:
    """current backend。"""
    return _BACKEND


def is_qt() -> bool:
    """判断是否为qt。"""
    return True
