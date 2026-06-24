# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""从 ``段曲线`` 解析干员指定精英/等级的基础属性。"""

from __future__ import annotations

from typing import Any

from games.arknights.calc.inverse.materialize import materialize_operator_entity
from games.arknights.calc.inverse.segments import STAT_KEYS, elite_segment_key, segment_length


def resolve_stats_from_segments(
    operator: dict[str, Any],
    *,
    elite: int = 2,
    level: int | None = None,
) -> dict[str, float]:
    """从 ``段曲线`` 取 hp/atk/def/res；无段曲线时返回空 dict。

    Args:
        operator: 干员 dict（可含 ``成长参数.segments[]`` 或已物化的 ``段曲线``）。
        elite: 精英阶段 0/1/2。
        level: 段内等级（1 起）；默认该段满级。

    Returns:
        属性键 → 数值；无法解析时返回 ``{}``。
    """
    curves = operator.get("段曲线")
    if not isinstance(curves, dict):
        materialized = materialize_operator_entity(operator)
        curves = materialized.get("段曲线")
    if not isinstance(curves, dict):
        return {}

    rarity = int(operator.get("星级", 6))
    seg_len = segment_length(rarity, elite)
    if seg_len <= 0:
        return {}

    seg_key = elite_segment_key(elite)
    idx = (seg_len - 1) if level is None else max(0, min(int(level) - 1, seg_len - 1))

    out: dict[str, float] = {}
    for stat in STAT_KEYS:
        arr = curves.get(f"{seg_key}.{stat}")
        if isinstance(arr, list) and arr:
            out[stat] = float(arr[idx])
    return out
