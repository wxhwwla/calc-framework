#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
应用层：配装快照、确认刷新、预设与求值编排。

子模块：
- loadout_state：LoadoutState、从面板刮取
- confirm_refresh：确认签名与刷新编排
- loadout_evaluation：预览/仪表盘求值
- loadout_preset：配装 JSON 导入导出
- display_request：确认刷新统一输入
- compute_sheet_variables：ComputeSheet user_input 变量定义（纯 Python）
- enemy_params_state：敌方参数状态 dataclass（纯 Python）
- loadout_reader：loadout 读取统一（纯 Python）
- search_controller：搜索编排逻辑（纯 Python）
"""

from . import (
    compute_sheet_variables,
    confirm_refresh,
    display_request,
    enemy_params_state,
    loadout_evaluation,
    loadout_preset,
    loadout_reader,
    loadout_state,
    search_controller,
)

__all__ = [
    "compute_sheet_variables",
    "confirm_refresh",
    "display_request",
    "enemy_params_state",
    "loadout_evaluation",
    "loadout_preset",
    "loadout_reader",
    "loadout_state",
    "search_controller",
]
