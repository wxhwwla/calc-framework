# SPDX-License-Identifier: AGPL-3.0
"""``成长参数`` 多段存储的检测与实体物化（加载层双读）。"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any, TypeGuard

from .curve import (
    CurveBlueprint,
    SegmentCurveEngine,
    SegmentSpec,
    parse_stored_segments,
)

GROWTH_PARAM_KEY = "成长参数"


def has_segment_storage(params: Mapping[str, Any] | None) -> TypeGuard[Mapping[str, Any]]:
    """``成长参数`` 是否采用 ``segments[]`` 多段形态。"""
    if not isinstance(params, Mapping):
        return False
    return bool(parse_stored_segments(params))


def materialize_segment_curves(
    blueprint: CurveBlueprint,
    stored: Mapping[str, Any],
    *,
    engine: SegmentCurveEngine | None = None,
) -> dict[str, list[float]]:
    """将 stored 中的 segments 按 blueprint 物化为段数组。"""
    return (engine or SegmentCurveEngine()).materialize(blueprint, stored)


def materialize_entity_segment_fields(
    entity: dict[str, Any],
    blueprint: CurveBlueprint,
    *,
    growth_key: str = GROWTH_PARAM_KEY,
    field_from_segment_key: Mapping[str, str] | None = None,
    engine: SegmentCurveEngine | None = None,
) -> dict[str, Any]:
    """若实体含 ``segments[]`` 成长参数，烘焙到顶层字段并返回新 dict。

    Args:
        entity: 原始实体 dict。
        blueprint: 段声明（决定物化哪些 key）。
        growth_key: 成长参数顶层键名。
        field_from_segment_key: 段 key → 实体字段名；缺省为恒等映射。

    Returns:
        物化后的实体副本；无 segments 或物化失败时返回原样 deepcopy。
    """
    params = entity.get(growth_key)
    if not has_segment_storage(params):
        return deepcopy(entity)
    curves = materialize_segment_curves(blueprint, params, engine=engine)
    if not curves:
        return deepcopy(entity)
    out = deepcopy(entity)
    mapping = field_from_segment_key or {}
    for seg_key, values in curves.items():
        field = mapping.get(seg_key, seg_key)
        out[field] = values
    return out


def merge_blueprint_segments(blueprints: list[CurveBlueprint]) -> CurveBlueprint:
    """合并多个 blueprint 的段列表（同 key 后者覆盖）。"""
    by_key: dict[str, SegmentSpec] = {}
    order: list[str] = []
    for blueprint in blueprints:
        for spec in blueprint.segments:
            if spec.key not in by_key:
                order.append(spec.key)
            by_key[spec.key] = spec
    return CurveBlueprint(segments=[by_key[k] for k in order])


def blueprint_from_stored(stored: Mapping[str, Any]) -> CurveBlueprint:
    """从 ``成长参数.segments[]`` 条目动态构建 blueprint（物化用）。"""
    specs: list[SegmentSpec] = []
    for entry in parse_stored_segments(stored):
        key = str(entry.get("key", ""))
        length = int(entry.get("length", 0) or 0)
        if not key or length < 1:
            continue
        special = entry.get("special_values")
        special_indices = None
        if isinstance(special, list) and special:
            n = len(special)
            special_indices = list(range(max(0, length - n), length))
        specs.append(SegmentSpec(key=key, length=length, special_indices=special_indices))
    return CurveBlueprint(segments=specs)


def materialize_entity_from_stored_segments(
    entity: dict[str, Any],
    *,
    growth_key: str = GROWTH_PARAM_KEY,
    field_from_segment_key: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """根据 stored 内 segments 动态 blueprint 物化实体字段。"""
    params = entity.get(growth_key)
    if not has_segment_storage(params):
        return deepcopy(entity)
    blueprint = blueprint_from_stored(params)
    if not blueprint.segments:
        return deepcopy(entity)
    return materialize_entity_segment_fields(
        entity,
        blueprint,
        growth_key=growth_key,
        field_from_segment_key=field_from_segment_key,
    )
