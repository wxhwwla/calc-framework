# SPDX-License-Identifier: AGPL-3.0
"""装备面板显示值 → 实战数值校正（NGA PART 05 附表节选）。"""

from __future__ import annotations

# (属性名, 面板整数显示) → 实战值
_FLAT_STAT_CORRECTIONS: dict[tuple[str, int], float] = {
    ("攻击力", 11): 11.7167,
    ("攻击力", 16): 16.1877,
    ("防御力", 21): 21.6,
}

_PERCENT_CORRECTIONS: dict[tuple[str, float], float] = {
    ("攻击力", 12.3): 12.25,
}

# 源石技艺强度面板显示 → 实战（节选 70 级）
_ORIGINIUM_DISPLAY_TO_ACTUAL: dict[int, float] = {
    20: 20.0,
    24: 24.5,
    29: 29.4,
    41: 41.4,
}


def correct_flat_stat_value(stat_name: str, display_value: float) -> float:
    """固定数值词条：若附表有记录则返回实战值。"""
    try:
        key = (stat_name, int(display_value))
    except (TypeError, ValueError):
        return float(display_value)
    return float(_FLAT_STAT_CORRECTIONS.get(key, display_value))


def correct_percent_display(display_percent: float) -> float:
    """百分比显示校正（输入为百分数，如 12.3 表示 12.3%）。"""
    return float(_PERCENT_CORRECTIONS.get(("攻击力", round(display_percent, 1)), display_percent))


def correct_originium_display(display_int: int) -> float:
    """源石技艺强度词条显示整数 → 实战值。"""
    return float(_ORIGINIUM_DISPLAY_TO_ACTUAL.get(int(display_int), display_int))
