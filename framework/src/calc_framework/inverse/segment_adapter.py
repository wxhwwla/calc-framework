# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
``SegmentCurveAdapter`` — 基于 ``CurveBlueprint`` 的游戏逆推适配器基类。

子类声明一个或多个 ``CurveBlueprint``，框架聚合 schema、段级 fit/compute/materialize。
参见 ADR-0026。
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from .base import FitResult
from .curve import CurveBlueprint, SegmentCurveEngine, SegmentSpec
from .engine import InverseEngine
from .schema import GameInverseAdapter, InverseSchema


class SegmentCurveAdapter(GameInverseAdapter):
    """多段曲线游戏逆推适配器基类。

    子类实现 ``iter_blueprints()`` 返回该适配器可见的蓝图集合（可含动态生成项）。
    ``schemas`` 自动聚合各段 ``InverseSchema``；段级 API 委托 ``SegmentCurveEngine``。
    """

    def __init__(self, engine: InverseEngine | None = None) -> None:
        super().__init__(engine)
        self.curves = SegmentCurveEngine(self._engine)

    @abstractmethod
    def iter_blueprints(self) -> Iterable[CurveBlueprint]:
        """返回适配器注册的全部曲线蓝图（用于 schema 聚合与 key 查找）。"""

    def find_spec(self, segment_key: str) -> tuple[CurveBlueprint, SegmentSpec] | None:
        """在已注册蓝图中按段 key 查找规格。"""
        for blueprint in self.iter_blueprints():
            spec = blueprint.get(segment_key)
            if spec is not None:
                return blueprint, spec
        return None

    @property
    def schemas(self) -> list[InverseSchema]:
        """聚合各 blueprint 的 schema；同 key 仅保留首次出现。"""
        seen: set[str] = set()
        out: list[InverseSchema] = []
        for blueprint in self.iter_blueprints():
            for schema in blueprint.schemas():
                if schema.key:
                    if schema.key in seen:
                        continue
                    seen.add(schema.key)
                out.append(schema)
        return out

    def fit_segment_by_key(self, data: Sequence[float], segment_key: str) -> FitResult:
        """按段 key 拟合（跨 blueprint 查找）。"""
        found = self.find_spec(segment_key)
        if found is None:
            keys = self.segment_keys()
            raise ValueError(f"未知段 key: {segment_key!r}。已注册: {keys}")
        _blueprint, spec = found
        return self.curves.fit_segment(data, spec)

    def compute_segment_by_key(
        self,
        params: dict[str, Any],
        segment_key: str,
    ) -> list[float]:
        """按段 key 正向计算。"""
        found = self.find_spec(segment_key)
        if found is None:
            raise ValueError(f"未知段 key: {segment_key!r}")
        _blueprint, spec = found
        return self.curves.compute_segment(params, spec)

    def materialize_stored(
        self,
        stored: Mapping[str, Any],
        *,
        blueprint: CurveBlueprint | None = None,
    ) -> dict[str, list[float]]:
        """将 ``成长参数`` 中的 ``segments[]`` 物化为 ``{段key: 数组}``。

        Args:
            stored: 含 ``segments`` 的 ``成长参数`` dict。
            blueprint: 限定物化范围；默认合并 ``iter_blueprints()`` 中各段。
        """
        if blueprint is not None:
            return self.curves.materialize(blueprint, stored)
        merged: dict[str, list[float]] = {}
        for bp in self.iter_blueprints():
            merged.update(self.curves.materialize(bp, stored))
        return merged

    def segment_keys(self) -> list[str]:
        """所有已注册段 key（去重保序）。"""
        keys: list[str] = []
        seen: set[str] = set()
        for blueprint in self.iter_blueprints():
            for spec in blueprint.segments:
                key = spec.key
                if key not in seen:
                    seen.add(key)
                    keys.append(key)
        return keys

    def fit_with_key(self, data: Sequence[float], schema_key: str) -> FitResult:
        """按 schema/段 key 拟合；优先走 ``SegmentCurveEngine``。"""
        if self.find_spec(schema_key) is not None:
            return self.fit_segment_by_key(data, schema_key)
        return super().fit_with_key(data, schema_key)
