# SPDX-License-Identifier: AGPL-3.0
"""明日方舟 ``成长参数.segments[]`` 加载物化。"""

from __future__ import annotations

from typing import Any

from calc_framework.inverse.materialize import (
    GROWTH_PARAM_KEY,
    has_segment_storage,
)

from games.arknights.calc.inverse.adapter import ArknightsInverseAdapter


def materialize_operator_entity(operator: dict[str, Any]) -> dict[str, Any]:
    """若含 ``成长参数.segments[]`` 则物化段曲线到 ``段曲线`` 字段。"""
    params = operator.get(GROWTH_PARAM_KEY)
    if not has_segment_storage(params):
        return operator
    adapter = ArknightsInverseAdapter()
    curves = adapter.materialize_operator_segments(operator)
    if not curves:
        return operator
    out = dict(operator)
    out["段曲线"] = curves
    return out


def materialize_operator_list(operators: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """批量物化干员列表。"""
    return [materialize_operator_entity(o) for o in operators]
