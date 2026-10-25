# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
终末地逆推适配器 — 基于 ``SegmentCurveAdapter`` / ``CurveBlueprint``。

将终末地的领域知识（90 级属性、9/12 级技能倍率、94 级去重）
声明为曲线蓝图，委托框架 ``SegmentCurveEngine`` 执行拟合。

旧 `api.py` / `attribute.py` / `skill.py` 的公开函数保留为向后兼容的薄封装。
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from calc_framework.inverse.base import FitResult
from calc_framework.inverse.curve import CurveBlueprint
from calc_framework.inverse.schema import InverseSchema
from calc_framework.inverse.segment_adapter import SegmentCurveAdapter

from games.endfield.calc.damage.inverse.blueprints import (
    ENDFIELD_ATTRIBUTE_BLUEPRINT,
    ENDFIELD_INVERSE_BLUEPRINTS,
    ENDFIELD_SKILL_9_BLUEPRINT,
    ENDFIELD_SKILL_12_BLUEPRINT,
)

_DUPLICATE_INDICES_94 = [20, 41, 62, 83]


def remove_duplicates_94(data: Sequence[float]) -> list[float]:
    """从 94 个数据中移除 4 个重复点，得到标准 90 级数据。"""
    if len(data) != 94:
        raise ValueError(f"输入数据长度应为 94，实际为 {len(data)}")
    return [data[i] for i in range(94) if i not in _DUPLICATE_INDICES_94]


class EndfieldInverseAdapter(SegmentCurveAdapter):
    """终末地逆推适配器（单段属性 90 + 技能 12/9）。"""

    def iter_blueprints(self) -> Iterable[CurveBlueprint]:
        return ENDFIELD_INVERSE_BLUEPRINTS

    def default_formula(self) -> str:
        return "floor_linear"

    def fit_attribute_90(self, data: Sequence[float]) -> FitResult:
        """拟合 90 级属性成长。"""
        return self.curves.fit_by_key(data, ENDFIELD_ATTRIBUTE_BLUEPRINT, "attr_90")

    def fit_skill_12(self, data: Sequence[float]) -> FitResult:
        """拟合 12 级技能倍率（10–12 特殊值）。"""
        return self.curves.fit_by_key(data, ENDFIELD_SKILL_12_BLUEPRINT, "skill_12")

    def fit_skill_9(self, data: Sequence[float]) -> FitResult:
        """拟合 9 级技能倍率。"""
        return self.curves.fit_by_key(data, ENDFIELD_SKILL_9_BLUEPRINT, "skill_9")

    def fit(self, data: Sequence[float]) -> FitResult:
        """按长度匹配单段；多段同长时须 ``fit_with_key``。"""
        matched = [s for s in self.schemas if len(data) == s.length]
        if len(matched) == 1:
            schema = matched[0]
            if schema.key:
                return self.fit_with_key(data, schema.key)
            return self._fit_legacy_schema(schema, data)
        if len(matched) > 1:
            keys = ", ".join(s.key or s.label for s in matched)
            raise ValueError(f"数据长度 {len(data)} 匹配多个 schema（{keys}），请使用 fit_with_key()。")
        self.on_no_match(data)
        raise RuntimeError("unreachable")

    def _fit_legacy_schema(self, schema: InverseSchema, data: Sequence[float]) -> FitResult:
        """无 key 的 schema 拟合并应用 ``fit_special_logic``。"""
        base_data = schema.extract_base_data(data)
        special_values = schema.extract_special_values(data)
        options = schema.search_options or {}
        result = self._engine.fit(base_data, formula_id=schema.formula_id, **options)
        if special_values and result.params:
            result.params["special_values"] = special_values
        return self.fit_special_logic(schema, base_data, result, data)

    def fit_special_logic(
        self,
        schema: InverseSchema,
        base_data: Sequence[float],
        result: FitResult,
        original_data: Sequence[float],
    ) -> FitResult:
        """9 级技能：第 9 级拟合失败时降级为 special 重试。"""
        if schema.length == 12 or schema.key == "skill_12":
            return result
        if (schema.length == 9 or schema.key == "skill_9") and not result.is_exact and result.params:
            special_values = [original_data[8]]
            base_8 = original_data[:8]
            options = schema.search_options or {}
            retry_result = self._engine.fit(base_8, formula_id=schema.formula_id, **options)
            if retry_result.is_exact and retry_result.params:
                retry_result.params["special_values"] = special_values
                return retry_result
        return result

    def fit_with_key(self, data: Sequence[float], schema_key: str) -> FitResult:
        result = super().fit_with_key(data, schema_key)
        schema = next((s for s in self.schemas if s.key == schema_key), None)
        if schema is None:
            return result
        base_data = schema.extract_base_data(data)
        return self.fit_special_logic(schema, base_data, result, data)

    def fit_from_94(self, data: Sequence[float]) -> FitResult:
        """从 94 级数据（含重复点）拟合 90 级属性。"""
        return self.fit_attribute_90(remove_duplicates_94(data))

    def on_no_match(self, data: Sequence[float]) -> None:
        supported = ", ".join(str(s.length) for s in self.schemas)
        raise ValueError(f"不支持的数据长度: {len(data)}。支持的长度: {supported}")
