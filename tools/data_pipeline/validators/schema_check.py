#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""标准 schema 校验器 — 检查 EntitySchema 的完整性和合法性。"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from ..schema import EntitySchema, SkillSchema, SegmentSchema


class SchemaError(ValueError):
    """Schema 校验失败。"""


def validate(entity: EntitySchema, *, strict: bool = False) -> List[str]:
    """校验单个 EntitySchema，返回错误信息列表。

    Args:
        entity: 要校验的实体
        strict: 严格模式（额外检查非强制字段）

    Returns:
        错误信息列表，空列表表示合法
    """
    errors: List[str] = []
    name = entity.get("名称", "")
    if not name:
        errors.append("缺少必填字段 '名称'")

    skills = entity.get("技能", [])
    if not skills:
        errors.append(f"'{name}': 技能列表为空")

    for i, skill in enumerate(skills):
        _validate_skill(skill, name, i, errors, strict=strict)

    return errors


def _validate_skill(
    skill: SkillSchema,
    entity_name: str,
    index: int,
    errors: List[str],
    *,
    strict: bool,
) -> None:
    prefix = f"'{entity_name}'.技能[{index}]"
    name = skill.get("名称", "")
    if not name:
        errors.append(f"{prefix}: 缺少 '名称'")

    label = skill.get("标签", "")
    if label not in ("主动", "被动"):
        errors.append(f"{prefix}.名称='{name}': 标签应为 '主动' 或 '被动', 实际 '{label}'")

    percent = skill.get("百分比")
    if percent is None:
        errors.append(f"{prefix}.名称='{name}': 缺少 '百分比'")

    segments = skill.get("段", [])
    if not segments:
        errors.append(f"{prefix}.名称='{name}': 段列表为空")

    for j, seg in enumerate(segments):
        _validate_segment(seg, entity_name, name, j, errors, strict=strict)


def _validate_segment(
    seg: SegmentSchema,
    entity_name: str,
    skill_name: str,
    index: int,
    errors: List[str],
    *,
    strict: bool,
) -> None:
    prefix = f"'{entity_name}'.技能'{skill_name}'.段[{index}]"
    rates = seg.get("倍率", [])
    if not rates:
        errors.append(f"{prefix}: 倍率列表为空")
    if strict:
        for v in rates:
            if not isinstance(v, int):
                errors.append(f"{prefix}: 倍率值应为 int, 实际 {type(v).__name__} ({v})")


def validate_all(entities: List[EntitySchema], *, strict: bool = False) -> List[Tuple[int, List[str]]]:
    """批量校验，返回 (序号, 错误列表) 列表。"""
    return [
        (i, validate(e, strict=strict))
        for i, e in enumerate(entities)
    ]
