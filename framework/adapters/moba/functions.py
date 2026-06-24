# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""MOBA 适配器 — DAG 表达式自定义函数。"""


def percent_of(value: float, total: float) -> float:
    """value / total，防除零。"""

    return value / total if total else 0.0


def armor_mult(armor: float, penetration_pct: float, lethality: float) -> float:
    """MOBA 护甲减伤公式（含穿甲）。



    有效护甲 = 护甲 × (1 - 百分比穿透) - 固定穿甲

    减伤比 = 100 / (100 + 有效护甲)

    """

    effective = max(0, armor * (1 - penetration_pct) - lethality)

    return 100.0 / (100.0 + effective)
