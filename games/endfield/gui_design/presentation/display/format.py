#!/usr/bin/env python3
"""
属性/乘区/单段伤害的展示文案构建（无 GUI 依赖，便于单测）。
"""

from __future__ import annotations

from typing import Any, NamedTuple

from adapters.endfield.calc.core.config import CHARACTER_NORMAL_ATTRS

# 等级相关属性列表（需要根据等级从列表中提取对应值）
LEVEL_ATTRIBUTES = ["力量", "敏捷", "智识", "意志", "基础攻击力"]

# 角色技能类型与 JSON 字段、选择区滑块等级参数对应（见 skill_segments.CHARACTER_SKILL_TYPES）

NO_DAMAGE_MULTIPLIER_TEXT = "无伤害倍率"

# 武器 xxx+ 中不按百分数展示的词条（JSON 为去掉 % 的数值，展示为整数）
WEAPON_INTEGER_BONUS_ATTR_KEY = "源石技艺"
WEAPON_FLAT_BONUS_ATTRS: frozenset[str] = frozenset({"附加攻击力+", "主能力+", "副能力+"})


def weapon_bonus_display_uses_percent(attr_name: str) -> bool:
    """
    武器 xxx+ 在属性列是否带 % 展示。

    与 ``final_attack_zone`` / ``ability_bonus_zone`` 一致：
    - ``攻击力+``、*伤害+、*率+、充能效率 → 百分数
    - ``附加攻击力+``、四维+、主/副能力+、源石技艺 → 固定数值
    """
    if attr_name in WEAPON_FLAT_BONUS_ATTRS:
        return False
    if any(attr_name == f"{stat}+" for stat in CHARACTER_NORMAL_ATTRS):
        return False
    if WEAPON_INTEGER_BONUS_ATTR_KEY in attr_name:
        return False
    if attr_name == "攻击力+":
        return True
    if attr_name.endswith("伤害+"):
        return True
    if "充能效率" in attr_name:
        return True
    if attr_name.endswith("率+"):
        return True
    return True


def _weapon_bonus_uses_integer_display(attr_name: str, *, is_first_skill: bool = False) -> bool:
    """是否按固定整数展示（``is_first_skill`` 保留兼容，实际以词条名为准）。"""
    _ = is_first_skill
    return not weapon_bonus_display_uses_percent(attr_name)


def evaluate_display_state(
    char_data: dict[str, Any] | None,
    weapon_data: dict[str, Any] | None,
) -> dict[str, Any]:
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


def format_weapon_bonus_display_value(
    raw: Any,
    *,
    attr_name: str = "",
    is_first_skill: bool = False,
) -> str:
    """
    武器属性列中 xxx+ 与特殊能力字段的数值展示格式。

    按 ``weapon_bonus_display_uses_percent`` 区分百分数与固定数值；
    JSON 中百分类词条存的是去掉 % 的数值（如 27.6 表示 27.6%）。
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


def _get_attribute_value(data: dict[str, Any], level: int, attr_name: str) -> str:
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


def _skill_segment_display_value(segment: Any, skill_level: int) -> str | None:
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


class SelectedSkillForDamage(NamedTuple):
    """单段预览/单技能搜索使用的技能与伤害类型。"""

    label: str
    multiplier: float
    warning: str
    damage_type: str
    damage_type_display: str
    skill_type: str
