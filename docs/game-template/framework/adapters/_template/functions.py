# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""TEMPLATE（{Game}）DAG 表达式自定义函数。

TODO: 根据游戏数值公式添加自定义函数。示例含 clamp 供参考。
"""

from __future__ import annotations


def clamp(value: float, min_val: float, max_val: float) -> float:
    """将值限制到 [min_val, max_val] 区间。"""
    return max(min_val, min(value, max_val))


# TODO: 在此处添加游戏专属函数，如：
# def physical_damage(*, atk: float, skill_mult: float, def_: float) -> float:
#     ...
