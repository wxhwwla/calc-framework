#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
属性/乘区/单段伤害的展示文案构建（无 GUI 依赖，便于单测）。
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from calculation.damage_engine import (
    ZONE_ORDER,
    DamageContext,
    DamageResult,
    calculate_single_hit_damage,
)
from calculation.multiplicative_zones.final_attack_zone import calculate_final_attack_with_details
from calculation.preview_cache import cached_preview, sync_confirm_dependencies

# 等级相关属性列表（需要根据等级从列表中提取对应值）
LEVEL_ATTRIBUTES = ["力量", "敏捷", "智识", "意志", "基础攻击力"]

# 角色技能类型与 JSON 字段、选择区滑块等级参数对应
CHARACTER_SKILL_TYPES = (
    ("战技", "战技倍率"),
    ("连携技", "连携技倍率"),
    ("终结技", "终结技倍率"),
)

NO_DAMAGE_MULTIPLIER_TEXT = "无伤害倍率"

# 武器 xxx+ 中不按百分数展示的词条（JSON 为去掉 % 的数值，展示为整数）
WEAPON_INTEGER_BONUS_ATTR_KEY = "源石技艺"


def evaluate_display_state(
    char_data: Optional[Dict[str, Any]],
    weapon_data: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """评估本次确认后各列提示及右侧乘区是否可更新（无 CTk）。"""
    state = {
        "char_message": "",
        "weapon_message": "",
        "can_update_zone": bool(char_data and weapon_data),
    }
    if not char_data:
        state["char_message"] = "请选择有效角色"
    if not weapon_data:
        state["weapon_message"] = "请选择有效武器"
    return state


def _weapon_bonus_uses_integer_display(attr_name: str, *, is_first_skill: bool) -> bool:
    """第一技能，或名称含源石技艺的附加属性，均展示为整数、不加 %。"""
    return is_first_skill or WEAPON_INTEGER_BONUS_ATTR_KEY in attr_name


def format_weapon_bonus_display_value(
    raw: Any,
    *,
    attr_name: str = "",
    is_first_skill: bool = False,
) -> str:
    """
    武器属性列中 xxx+ 与特殊能力字段的数值展示格式。

    - 第一技能（第一条 xxx+）：JSON 数值按整数展示，如 60.0 → 60
    - 名称含「源石技艺」的 xxx+：不论第几条，均按整数展示
    - 其余附加属性与特殊能力字段：按百分数展示，JSON 数值即百分比，如 27.6 → 27.6%
    """
    try:
        num = float(raw)
    except (TypeError, ValueError):
        return str(raw)

    if _weapon_bonus_uses_integer_display(attr_name, is_first_skill=is_first_skill):
        return str(int(num))

    if num == int(num):
        return f"{int(num)}%"
    text = format(num, "g")
    return f"{text}%"


def _get_attribute_value(data: Dict[str, Any], level: int, attr_name: str) -> str:
    """根据等级从列表或标量字段取属性展示值。"""
    if attr_name not in data:
        return ""

    value = data[attr_name]
    if isinstance(value, list):
        index = level - 1
        if 0 <= index < len(value):
            return str(value[index])
        return ""
    return str(value)


def format_skill_multiplier_display_value(raw: Any) -> str:
    """技能倍率展示：JSON 去掉百分号，展示时原样补 %。"""
    try:
        num = float(raw)
    except (TypeError, ValueError):
        return str(raw)
    if num == int(num):
        return f"{int(num)}%"
    return f"{format(num, 'g')}%"


def _skill_segment_display_value(segment: Any, skill_level: int) -> Optional[str]:
    """取单段倍率展示值；无伤害倍率时返回 None。"""
    if not isinstance(segment, list) or not segment:
        return None
    index = skill_level - 1
    if not (0 <= index < len(segment)):
        return None
    raw = segment[index]
    if raw is None:
        return None
    return format_skill_multiplier_display_value(raw)


def build_character_skill_lines(
    char_data: Dict[str, Any],
    *,
    skill_1_level: int = 0,
    skill_2_level: int = 0,
    skill_3_level: int = 0,
) -> list[str]:
    """构建角色技能倍率明细行（战技 → 连携技 → 终结技）。"""
    skill_levels = (skill_1_level, skill_2_level, skill_3_level)
    lines: list[str] = []
    for (skill_type, field_name), skill_level in zip(CHARACTER_SKILL_TYPES, skill_levels):
        if skill_level <= 0:
            continue
        segments = char_data.get(field_name)
        if not isinstance(segments, list) or not segments:
            continue
        for segment_index, segment in enumerate(segments, start=1):
            display_value = _skill_segment_display_value(segment, skill_level)
            if display_value is None:
                value_text = NO_DAMAGE_MULTIPLIER_TEXT
            else:
                value_text = display_value
            lines.append(
                f"{skill_type} 等级{skill_level} 第{segment_index}段: {value_text}"
            )
    return lines


def build_character_attribute_lines(
    char_data: Optional[Dict[str, Any]],
    level: int,
    *,
    skill_1_level: int = 0,
    skill_2_level: int = 0,
    skill_3_level: int = 0,
) -> list[str]:
    """构建角色属性列展示明细（不含摘要）。"""
    if not char_data:
        return []
    lines: list[str] = []
    for attr_name in LEVEL_ATTRIBUTES:
        value = _get_attribute_value(char_data, level, attr_name)
        if value:
            lines.append(f"{attr_name}: {value}")
    if skill_1_level or skill_2_level or skill_3_level:
        lines.extend(
            build_character_skill_lines(
                char_data,
                skill_1_level=skill_1_level,
                skill_2_level=skill_2_level,
                skill_3_level=skill_3_level,
            )
        )
    return lines


def build_weapon_attribute_lines(
    weapon_data: Optional[Dict[str, Any]],
    weapon_level: int,
    *,
    sa1_name: str = "",
    sa1_level: int = 1,
    sa2_name: str = "",
    sa2_level: int = 1,
    sa3_name: str = "",
    sa3_level: int = 0,
    ws_name: str = "",
    ws_level: int = 0,
    ws2_name: str = "",
    ws2_level: int = 0,
) -> list[str]:
    """构建武器属性列展示明细（不含摘要）。"""
    if not weapon_data:
        return []

    lines: list[str] = []
    base_attack = _get_attribute_value(weapon_data, weapon_level, "基础攻击力")
    if base_attack:
        lines.append(f"基础攻击力: {base_attack}")

    bonus_attrs = [key for key in weapon_data.keys() if key.endswith("+")]
    for attr_name in bonus_attrs:
        value = weapon_data[attr_name]
        if isinstance(value, list) and value:
            if attr_name == sa1_name:
                level_index = sa1_level - 1
            elif attr_name == sa2_name:
                level_index = sa2_level - 1
            elif attr_name == sa3_name:
                level_index = sa3_level - 1
            else:
                level_index = 0
            raw_value = value[level_index] if 0 <= level_index < len(value) else value[0]
        else:
            raw_value = value
        display_value = format_weapon_bonus_display_value(
            raw_value,
            attr_name=attr_name,
            is_first_skill=(attr_name == sa1_name),
        )
        lines.append(f"{attr_name}: {display_value}")

    from character_weapon_equipment.weapon_data.special_fields import (
        get_special_value_at_level,
    )

    for slot_idx, pick_level, pick_name, label in (
        (0, ws_level, ws_name, "特殊能力1"),
        (1, ws2_level, ws2_name, "特殊能力2"),
    ):
        if not pick_name or pick_name in bonus_attrs:
            continue
        raw_value = get_special_value_at_level(
            weapon_data, slot_idx, name=pick_name, level=pick_level
        )
        display_value = "0%"
        if raw_value is not None:
            display_value = format_weapon_bonus_display_value(
                raw_value,
                attr_name=pick_name,
                is_first_skill=False,
            )
        lines.append(f"{pick_name}({label}): {display_value}")
    return lines


def resolve_selected_skill_for_damage(
    char_data: Dict[str, Any],
    *,
    skill_1_level: int = 0,
    skill_2_level: int = 0,
    skill_3_level: int = 0,
) -> tuple[str, float, str]:
    """根据技能滑块解析单段伤害预览所用的技能倍率。"""
    picks = (
        ("战技", "战技倍率", skill_1_level),
        ("连携技", "连携技倍率", skill_2_level),
        ("终结技", "终结技倍率", skill_3_level),
    )
    for skill_name, field_name, level in picks:
        if level <= 0:
            continue
        segments = char_data.get(field_name)
        if not isinstance(segments, list) or not segments:
            continue
        first_segment = segments[0]
        if not isinstance(first_segment, list) or not first_segment:
            continue
        idx = level - 1
        if not (0 <= idx < len(first_segment)):
            continue
        value = first_segment[idx]
        if value is None:
            continue
        return (
            f"{skill_name} 等级{level} 第1段",
            float(value) / 100.0,
            "",
        )
    return ("默认普攻段", 1.0, "未选择技能等级或无可用倍率，按 100% 计算。")


# 兼容旧私有名（历史模块名，勿再新增引用）
_resolve_selected_skill_for_damage = resolve_selected_skill_for_damage


def format_fifteen_zone_damage_lines(
    result: DamageResult,
    *,
    header_lines: Optional[list[str]] = None,
    show_running_product: bool = True,
) -> list[str]:
    """将伤害引擎结果格式化为 15 乘区分步展示文案。"""
    lines: list[str] = list(header_lines or [])
    running = 1.0
    for zone_name in ZONE_ORDER:
        zone_value = float(result.zone_values[zone_name])
        if show_running_product:
            running *= zone_value
            lines.append(f"{zone_name}: {zone_value:.4f}  (累计: {running:.4f})")
        else:
            lines.append(f"{zone_name}: {zone_value:.4f}")
    lines.append(f"最终伤害: {result.final_damage:.1f}")
    if result.warnings:
        for warning in result.warnings:
            lines.append(f"提示: {warning}")
    if result.unknown_effects:
        lines.append(f"未识别效果数: {len(result.unknown_effects)}")
    return lines


def build_single_hit_damage_lines(
    *,
    char_data: Optional[Dict[str, Any]],
    weapon_data: Optional[Dict[str, Any]],
    char_level: int,
    weapon_level: int,
    trust_level: int = 0,
    skill_1_level: int = 0,
    skill_2_level: int = 0,
    skill_3_level: int = 0,
    sa1_name: str = "",
    sa1_level: int = 1,
    sa2_name: str = "",
    sa2_level: int = 1,
    sa3_name: str = "",
    sa3_level: int = 0,
    ws_name: str = "",
    ws_level: int = 0,
    ws2_name: str = "",
    ws2_level: int = 0,
    enemy_defense: float = 100.0,
) -> list[str]:
    """构建单段伤害计算模式的展示行（带结果缓存）。"""
    if not char_data or not weapon_data:
        return ["请选择有效角色和武器"]

    sync_confirm_dependencies(
        char_data=char_data,
        weapon_data=weapon_data,
        char_level=char_level,
        weapon_level=weapon_level,
        trust_level=trust_level,
        skill_levels=(skill_1_level, skill_2_level, skill_3_level),
        calculation_mode="single_hit",
        enemy_defense=enemy_defense,
    )

    def _compute() -> list[str]:
        return _build_single_hit_damage_lines_impl(
            char_data=char_data,
            weapon_data=weapon_data,
            char_level=char_level,
            weapon_level=weapon_level,
            trust_level=trust_level,
            skill_1_level=skill_1_level,
            skill_2_level=skill_2_level,
            skill_3_level=skill_3_level,
            sa1_name=sa1_name,
            sa1_level=sa1_level,
            sa2_name=sa2_name,
            sa2_level=sa2_level,
            sa3_name=sa3_name,
            sa3_level=sa3_level,
            ws_name=ws_name,
            ws_level=ws_level,
            ws2_name=ws2_name,
            ws2_level=ws2_level,
            enemy_defense=enemy_defense,
        )

    lines, _hit = cached_preview("single_hit_lines", _compute)
    return lines


def _build_single_hit_damage_lines_impl(
    *,
    char_data: Dict[str, Any],
    weapon_data: Dict[str, Any],
    char_level: int,
    weapon_level: int,
    trust_level: int = 0,
    skill_1_level: int = 0,
    skill_2_level: int = 0,
    skill_3_level: int = 0,
    sa1_name: str = "",
    sa1_level: int = 1,
    sa2_name: str = "",
    sa2_level: int = 1,
    sa3_name: str = "",
    sa3_level: int = 0,
    ws_name: str = "",
    ws_level: int = 0,
    ws2_name: str = "",
    ws2_level: int = 0,
    enemy_defense: float = 100.0,
) -> list[str]:
    skill_label, skill_multiplier, skill_warning = resolve_selected_skill_for_damage(
        char_data,
        skill_1_level=skill_1_level,
        skill_2_level=skill_2_level,
        skill_3_level=skill_3_level,
    )
    final = calculate_final_attack_with_details(
        character=char_data,
        weapon=weapon_data,
        char_level=char_level,
        weapon_level=weapon_level,
        sa1_name=sa1_name,
        sa1_level=sa1_level,
        sa2_name=sa2_name,
        sa2_level=sa2_level,
        sa3_name=sa3_name,
        sa3_level=sa3_level,
        ws_name=ws_name,
        ws_level=ws_level,
        ws2_name=ws2_name,
        ws2_level=ws2_level,
        trust_level=trust_level,
    )
    result = calculate_single_hit_damage(
        DamageContext(
            final_attack=float(final["final_attack"]),
            skill_multiplier=skill_multiplier,
            skill_type=skill_label.split()[0],
            enemy_defense=enemy_defense,
        ),
        crit_mode="non_crit",
    )
    header = [
        "计算模式: 单段伤害计算",
        f"技能: {skill_label}",
        f"技能倍率: {format_skill_multiplier_display_value(skill_multiplier * 100)}",
        f"最终攻击力(基础伤害区): {final['final_attack']:.1f}",
        "暴击模式: 不暴击",
    ]
    if skill_warning:
        header.append(f"提示: {skill_warning}")
    return format_fifteen_zone_damage_lines(
        result,
        header_lines=header,
        show_running_product=True,
    )
