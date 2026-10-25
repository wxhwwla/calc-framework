# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
多段等级曲线蓝图 — N 段 × 独立段长。

游戏通过 ``CurveBlueprint`` 声明分段模型，``SegmentCurveEngine`` 执行段级拟合与物化。
单段游戏（终末地）为 N=1 退化情形。

参见 ADR-0026。
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from .base import FitResult
from .engine import InverseEngine
from .schema import InverseSchema

GROWTH_PARAM_SEGMENTS_KEY = "segments"


@dataclass
class SegmentSpec:
    """单段等级曲线规格（中性段 ID，不含游戏领域命名）。"""

    key: str
    length: int
    formula_id: str = "floor_linear"
    label: str = ""
    special_indices: list[int] | None = None
    search_options: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.length < 1:
            raise ValueError(f"SegmentSpec.length 须 >= 1，实际 {self.length}")
        if not self.key:
            raise ValueError("SegmentSpec.key 不能为空")

    def to_schema(self) -> InverseSchema:
        """转换为 ``InverseSchema``（与 ``GameInverseAdapter`` 互操作）。"""
        return InverseSchema(
            key=self.key,
            length=self.length,
            formula_id=self.formula_id,
            label=self.label or self.key,
            special_indices=self.special_indices,
            search_options=self.search_options,
        )


@dataclass
class CurveBlueprint:
    """有序多段曲线声明（N 段 × 各段 length / formula / special）。"""

    segments: list[SegmentSpec] = field(default_factory=list)

    def get(self, key: str) -> SegmentSpec | None:
        """按段 ID 查找规格。"""
        for spec in self.segments:
            if spec.key == key:
                return spec
        return None

    def keys(self) -> list[str]:
        """所有段 ID。"""
        return [s.key for s in self.segments]

    def schemas(self) -> list[InverseSchema]:
        """导出为 ``InverseSchema`` 列表。"""
        return [s.to_schema() for s in self.segments]

    def specs_with_length(self, length: int) -> list[SegmentSpec]:
        """返回指定段长的全部规格（可能多于一条）。"""
        return [s for s in self.segments if s.length == length]


def single_segment_blueprint(
    length: int,
    *,
    key: str = "main",
    formula_id: str = "floor_linear",
    label: str = "",
    special_indices: list[int] | None = None,
    search_options: dict[str, Any] | None = None,
) -> CurveBlueprint:
    """单段蓝图（终末地式 N=1 退化封装）。"""
    return CurveBlueprint(
        segments=[
            SegmentSpec(
                key=key,
                length=length,
                formula_id=formula_id,
                label=label or f"{length} 级",
                special_indices=special_indices,
                search_options=search_options,
            )
        ]
    )


def expand_segment_linear(start: int | float, end: int | float, num_levels: int) -> list[int]:
    """端点线性插值展开段内数组（Wiki 仅里程碑时使用）。"""
    if num_levels < 1:
        raise ValueError("num_levels 须 >= 1")
    if num_levels == 1:
        return [round(end)]
    return [round(start + (end - start) * i / (num_levels - 1)) for i in range(num_levels)]


def _level_overrides_from_params(params: dict[str, Any], spec: SegmentSpec) -> dict[int, float] | None:
    """将 params 中的 special_values 转为 1-based level_overrides。"""
    special = params.get("special_values")
    if not special:
        return None
    indices = spec.special_indices
    if indices is None:
        indices = list(range(spec.length - len(special), spec.length))
    overrides: dict[int, float] = {}
    for idx, value in zip(indices, special, strict=False):
        overrides[int(idx) + 1] = float(value)
    return overrides or None


def segment_entry_from_fit(spec: SegmentSpec, result: FitResult) -> dict[str, Any]:
    """将段拟合结果转为可 JSON 序列化的段条目。"""
    if not result.params:
        raise ValueError(f"段 {spec.key} 拟合无参数")
    entry: dict[str, Any] = {"key": spec.key, "length": spec.length, **result.params}
    return entry


def parse_stored_segments(stored: Mapping[str, Any]) -> list[dict[str, Any]]:
    """从 ``成长参数`` dict 解析 segments 列表。"""
    raw = stored.get(GROWTH_PARAM_SEGMENTS_KEY)
    if not isinstance(raw, list):
        return []
    return [s for s in raw if isinstance(s, dict) and s.get("key")]


class SegmentCurveEngine:
    """多段曲线拟合与物化引擎。"""

    def __init__(self, engine: InverseEngine | None = None) -> None:
        self._engine = engine or InverseEngine()

    def fit_segment(self, data: Sequence[float], spec: SegmentSpec) -> FitResult:
        """拟合单个段（自动处理 special_indices）。"""
        if len(data) != spec.length:
            raise ValueError(f"段 {spec.key} 期望长度 {spec.length}，实际 {len(data)}")
        schema = spec.to_schema()
        base_data = schema.extract_base_data(data)
        special_values = schema.extract_special_values(data)
        options = spec.search_options or {}
        result = self._engine.fit(base_data, formula_id=spec.formula_id, **options)
        if special_values and result.params:
            result.params["special_values"] = special_values
        return result

    def fit_by_key(
        self,
        data: Sequence[float],
        blueprint: CurveBlueprint,
        key: str,
    ) -> FitResult:
        """按 blueprint 中的段 ID 拟合。"""
        spec = blueprint.get(key)
        if spec is None:
            raise ValueError(f"blueprint 中无段 key={key!r}，已有: {blueprint.keys()}")
        return self.fit_segment(data, spec)

    def compute_segment(self, params: dict[str, Any], spec: SegmentSpec) -> list[float]:
        """正向计算单段曲线（含 special_values）。"""
        overrides = _level_overrides_from_params(params, spec)
        return self._engine.compute(
            spec.formula_id,
            params,
            spec.length,
            level_overrides=overrides,
        )

    def compute_by_key(
        self,
        params: dict[str, Any],
        blueprint: CurveBlueprint,
        key: str,
    ) -> list[float]:
        """按段 ID 正向计算。"""
        spec = blueprint.get(key)
        if spec is None:
            raise ValueError(f"blueprint 中无段 key={key!r}")
        return self.compute_segment(params, spec)

    def materialize(
        self,
        blueprint: CurveBlueprint,
        stored: Mapping[str, Any],
    ) -> dict[str, list[float]]:
        """将 ``成长参数``（含 segments 列表）物化为各段数组。"""
        by_key: dict[str, dict[str, Any]] = {}
        for entry in parse_stored_segments(stored):
            k = str(entry.get("key", ""))
            if k:
                by_key[k] = dict(entry)
        out: dict[str, list[float]] = {}
        for spec in blueprint.segments:
            entry = by_key.get(spec.key)
            if not entry:
                continue
            params = {k: v for k, v in entry.items() if k not in ("key", "length")}
            out[spec.key] = self.compute_segment(params, spec)
        return out

    def fit_blueprint_endpoints(
        self,
        blueprint: CurveBlueprint,
        endpoints_by_key: Mapping[str, tuple[int | float, int | float]],
        *,
        max_error: float = 0.05,
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """从各段端点批量反推，返回 (segment_entries, errors)。"""
        entries: list[dict[str, Any]] = []
        errors: list[str] = []
        for spec in blueprint.segments:
            ep = endpoints_by_key.get(spec.key)
            if ep is None:
                continue
            start, end = ep
            data = expand_segment_linear(start, end, spec.length)
            result = self.fit_segment([float(x) for x in data], spec)
            if not result.params or result.max_error > max_error:
                errors.append(f"{spec.key}: max_error={result.max_error:.4f}")
                continue
            entries.append(segment_entry_from_fit(spec, result))
        return entries, errors
