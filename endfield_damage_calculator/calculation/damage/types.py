#!/usr/bin/env python3
"""伤害类型推断与展示（装备词条、技能段共用）。"""

from __future__ import annotations

from typing import Any

DEFAULT_DAMAGE_TYPE = "物理"

# 装备词条：标签 -> 作用域（可多值）
EQUIPMENT_DAMAGE_TYPE_TAGS: dict[str, tuple[str, ...]] = {
    "物理": ("物理",),
    "灼热": ("法术-灼热",),
    "电磁": ("法术-电磁",),
    "寒冷": ("法术-寒冷",),
    "自然": ("法术-自然",),
    "法术": ("法术-灼热", "法术-电磁", "法术-寒冷", "法术-自然"),
    "超域": ("超域",),
}

# 技能段：按优先级匹配行标题/列文本 -> 单值规范类型
_SEGMENT_INFER_ORDER: tuple[tuple[str, str], ...] = (
    ("物理", "物理"),
    ("灼热", "法术-灼热"),
    ("电磁", "法术-电磁"),
    ("寒冷", "法术-寒冷"),
    ("自然", "法术-自然"),
    ("超域", "超域"),
    ("法术", "法术"),
)

# 倍率字段 -> 段伤害类型 JSON 字段
SKILL_MULTIPLIER_TO_DAMAGE_TYPE_FIELD: dict[str, str] = {
    "战技倍率": "战技段伤害类型",
    "连携技倍率": "连携技段伤害类型",
    "终结技倍率": "终结技段伤害类型",
}

SKILL_SEED_DAMAGE_TYPE_KEYS: dict[str, str] = {
    "sk1": "sk1_dt",
    "sk2": "sk2_dt",
    "sk3": "sk3_dt",
}


def infer_equipment_damage_types(text: str) -> tuple[str, ...]:
    """从装备词条文案推断作用域（可多值）。"""
    for tag, mapped in EQUIPMENT_DAMAGE_TYPE_TAGS.items():
        if tag in text:
            return mapped
    return ()


def infer_segment_damage_type(*texts: str) -> str:
    """从 Wiki 行标题/类型列推断段级规范伤害类型；无匹配则物理。"""
    combined = " ".join(str(t) for t in texts if t).strip()
    if not combined:
        return DEFAULT_DAMAGE_TYPE
    for tag, canonical in _SEGMENT_INFER_ORDER:
        if tag in combined:
            return canonical
    return DEFAULT_DAMAGE_TYPE


def normalize_canonical_damage_type(raw: Any) -> str:
    """规范化 JSON/seed 中的伤害类型字符串。"""
    text = str(raw or "").strip()
    if not text:
        return DEFAULT_DAMAGE_TYPE
    if text in EQUIPMENT_DAMAGE_TYPE_TAGS:
        inferred = infer_segment_damage_type(text)
        return inferred
    if text.startswith("法术-") or text in {"物理", "法术", "超域"}:
        return text
    return infer_segment_damage_type(text)


def resolve_segment_damage_type(
    char_data: dict[str, Any],
    multiplier_field: str,
    segment_index: int,
) -> tuple[str, bool]:
    """
    读取角色 JSON 中某段伤害类型。

    返回 (规范类型, 是否显式收录)；缺字段或缺段时为 (物理, False)。
    """
    type_field = SKILL_MULTIPLIER_TO_DAMAGE_TYPE_FIELD.get(multiplier_field, "")
    if not type_field:
        return DEFAULT_DAMAGE_TYPE, False
    types = char_data.get(type_field)
    if not isinstance(types, list) or not (1 <= segment_index <= len(types)):
        return DEFAULT_DAMAGE_TYPE, False
    raw = types[segment_index - 1]
    if raw is None or str(raw).strip() == "":
        return DEFAULT_DAMAGE_TYPE, False
    return normalize_canonical_damage_type(raw), True


def format_damage_type_short(canonical: str) -> str:
    """界面短标签：法术-灼热 -> 灼热。"""
    if canonical == "物理":
        return "物理"
    if canonical == "法术":
        return "法术"
    if canonical.startswith("法术-"):
        return canonical.split("-", 1)[1]
    return canonical


def format_damage_type_display(canonical: str, *, is_default: bool = False) -> str:
    """段行/预览用展示文案。"""
    short = format_damage_type_short(canonical)
    if is_default:
        return f"{short}(默认物理)"
    return short


def damage_type_matches_context(ctx_type: str, effect_types: tuple[str, ...]) -> bool:
    """伤害上下文类型是否落入效果作用域。"""
    if not effect_types:
        return True
    if ctx_type in effect_types:
        return True
    return bool(ctx_type == "法术" and any(t.startswith("法术-") for t in effect_types))
