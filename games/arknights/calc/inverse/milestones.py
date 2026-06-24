# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""从 Wiki 属性里程碑批量反推 ``成长参数``。"""

from __future__ import annotations

from typing import Any

from calc_framework.inverse.curve import GROWTH_PARAM_SEGMENTS_KEY, expand_segment_linear

from games.arknights.calc.inverse.adapter import ArknightsInverseAdapter, blueprint_for_rarity
from games.arknights.calc.inverse.segments import STAT_KEYS, elite_segment_key, segment_endpoints, segment_length

GROWTH_PARAM_KEY = "成长参数"


def fit_operator_growth_params(
    operator: dict[str, Any],
    *,
    adapter: ArknightsInverseAdapter | None = None,
    max_error: float = 0.05,
) -> dict[str, Any]:
    """从干员 ``属性里程碑`` 反推分段 ``成长参数``（``segments`` 数组形态）。

    Args:
        operator: 含 ``星级``、``属性里程碑`` 的干员 dict。
        adapter: 逆推适配器（默认新建）。
        max_error: 段内拟合允许的最大误差。

    Returns:
        ``{"segments": [...], "技能SP": {...}, "_errors": [...]}``。
    """
    inv = adapter or ArknightsInverseAdapter()
    rarity = int(operator.get("星级", 6))
    milestones = operator.get("属性里程碑") or (operator.get("基础属性") or {}).get("属性里程碑") or {}
    attr_bp = blueprint_for_rarity(rarity)
    segment_entries: list[dict[str, Any]] = []
    skill_sp: dict[str, Any] = {}
    errors: list[str] = []

    for stat_key in STAT_KEYS:
        for elite in (0, 1, 2):
            seg_len = segment_length(rarity, elite)
            if seg_len <= 0:
                continue
            endpoints = segment_endpoints(milestones, stat_key, elite)
            if endpoints is None:
                continue
            start, end = endpoints
            data = expand_segment_linear(start, end, seg_len)
            seg_key = elite_segment_key(elite)
            spec = attr_bp.get(seg_key)
            if spec is None:
                continue
            composite_key = f"{seg_key}.{stat_key}"
            try:
                result = inv.curves.fit_segment([float(x) for x in data], spec)
            except ValueError as exc:
                errors.append(f"{composite_key}: {exc}")
                continue
            if not result.params or result.max_error > max_error:
                errors.append(f"{composite_key}: max_error={result.max_error:.4f}")
                continue
            entry = {"key": composite_key, "length": seg_len, "stat": stat_key, **result.params}
            segment_entries.append(entry)

    for skill in operator.get("技能") or []:
        sp = skill.get("SP消耗")
        if not isinstance(sp, list) or len(sp) != 10:
            continue
        if not all(isinstance(x, int | float) for x in sp):
            continue
        name = str(skill.get("名称", ""))
        try:
            result = inv.fit_skill_sp([float(x) for x in sp])
        except ValueError as exc:
            errors.append(f"技能 {name} SP: {exc}")
            continue
        if not result.params or result.max_error > max_error:
            errors.append(f"技能 {name} SP: max_error={result.max_error:.4f}")
            continue
        skill_sp[name] = result.params

    out: dict[str, Any] = {"_errors": errors}
    if segment_entries:
        out[GROWTH_PARAM_SEGMENTS_KEY] = segment_entries
    if skill_sp:
        out["技能SP"] = skill_sp
    return out


def attach_growth_params(operator: dict[str, Any], growth: dict[str, Any]) -> dict[str, Any]:
    """将反推结果写入干员 dict 的 ``成长参数`` 键（浅拷贝）。"""
    merged = dict(operator)
    merged[GROWTH_PARAM_KEY] = growth
    return merged
