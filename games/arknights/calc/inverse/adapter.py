# SPDX-License-Identifier: AGPL-3.0
"""明日方舟逆推适配器 — ``SegmentCurveAdapter`` + 动态/静态 ``CurveBlueprint``。"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from calc_framework.inverse.base import FitResult
from calc_framework.inverse.curve import CurveBlueprint, SegmentSpec
from calc_framework.inverse.segment_adapter import SegmentCurveAdapter

from games.arknights.calc.inverse.segments import segment_length

_ATTR_SEARCH: dict[str, Any] = {
    "divisor_range": (1, 201),
    "growth_range": (1, 501),
    "offset_search_limit": 200,
}

_SP_SEARCH: dict[str, Any] = {
    "divisor_range": (1, 101),
    "growth_range": (-500, 501),
    "offset_search_limit": 100,
}

SKILL_SP_BLUEPRINT = CurveBlueprint(
    segments=[
        SegmentSpec(
            key="skill_sp",
            length=10,
            label="技能 SP (1–7 公式 + 8–10 专精)",
            special_indices=[7, 8, 9],
            search_options=dict(_SP_SEARCH),
        )
    ]
)


def blueprint_for_rarity(rarity: int) -> CurveBlueprint:
    """按星级生成属性精英段 blueprint（``e0`` / ``e1`` / ``e2``）。"""
    segments: list[SegmentSpec] = []
    for elite in (0, 1, 2):
        length = segment_length(rarity, elite)
        if length <= 0:
            continue
        segments.append(
            SegmentSpec(
                key=f"e{elite}",
                length=length,
                label=f"精{elite} ({length} 级)",
                search_options=dict(_ATTR_SEARCH),
            )
        )
    return CurveBlueprint(segments=segments)


class ArknightsInverseAdapter(SegmentCurveAdapter):
    """明日方舟逆推适配器。"""

    def __init__(self, engine=None, *, default_rarity: int = 6) -> None:
        super().__init__(engine)
        self._default_rarity = int(default_rarity)

    def iter_blueprints(self) -> Iterable[CurveBlueprint]:
        """注册 6★ 属性段 + 技能 SP（schema 聚合用）。"""
        yield blueprint_for_rarity(self._default_rarity)
        yield SKILL_SP_BLUEPRINT

    def default_formula(self) -> str:
        return "floor_linear"

    def attribute_blueprint(self, rarity: int) -> CurveBlueprint:
        return blueprint_for_rarity(rarity)

    def fit_elite_segment(
        self,
        data: Sequence[float],
        *,
        elite: int,
        rarity: int,
    ) -> FitResult:
        bp = blueprint_for_rarity(rarity)
        key = f"e{elite}"
        if bp.get(key) is None:
            raise ValueError(f"{rarity} 星无精{elite} 段")
        return self.curves.fit_by_key(data, bp, key)

    def fit_skill_sp(self, data: Sequence[float]) -> FitResult:
        return self.curves.fit_by_key(data, SKILL_SP_BLUEPRINT, "skill_sp")

    def compute_segment(
        self,
        params: dict[str, Any],
        *,
        elite: int,
        rarity: int,
    ) -> list[float]:
        return self.curves.compute_by_key(params, blueprint_for_rarity(rarity), f"e{elite}")

    def compute_skill_sp(self, params: dict[str, Any]) -> list[float]:
        return self.curves.compute_by_key(params, SKILL_SP_BLUEPRINT, "skill_sp")

    def materialize_operator_segments(
        self,
        operator: dict[str, Any],
        *,
        rarity: int | None = None,
    ) -> dict[str, list[float]]:
        """物化干员 ``成长参数.segments[]`` 为 ``{段key: 数组}``。"""
        from calc_framework.inverse.materialize import blueprint_from_stored

        stored = operator.get("成长参数") or {}
        blueprint = blueprint_from_stored(stored)
        if not blueprint.segments:
            return {}
        return self.curves.materialize(blueprint, stored)

    def on_no_match(self, data: Sequence[float]) -> None:
        raise ValueError(
            f"不支持的数据长度: {len(data)}。请使用 fit_elite_segment() / fit_skill_sp() / fit_segment_by_key()。"
        )
