#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
属性展示模块

确认选择后，在「角色属性」「武器属性」两列分别展示等级曲线明细，
并在角色与武器数据均有效时刷新右侧乘区。
"""

import customtkinter as ctk
from typing import Dict, Any, Optional
from .selection_panel import ChooseTypesStarsNamesLevels
from calculation.multiplicative_zones import calculate_attribute_zones
from calculation.multiplicative_zones.zone_snapshot import (
    MultiplicativeZoneSelection,
    WeaponBonusSelection,
    compute_multiplicative_zone_snapshot,
)
from calculation.damage_engine import (
    ZONE_ORDER,
    DamageContext,
    DamageResult,
    calculate_single_hit_damage,
)
from calculation.multiplicative_zones.final_attack_zone import calculate_final_attack_with_details
from calculation.loadout_optimizer import (
    OptimizerConfig,
    WeaponCandidate,
    search_best_single_skill_loadouts,
)
from calculation.multi_skill_optimizer import (
    MultiSkillConfig,
    SkillScenario,
    optimize_multi_skill_loadouts,
)
from calculation.equipment_system import build_equipment_catalog_from_local_rows
from data.loader import DataLoadError, get_equipments


# 等级相关属性列表（需要根据等级从列表中提取对应值）
LEVEL_ATTRIBUTES = ['力量', '敏捷', '智识', '意志', '基础攻击力']

# 角色技能类型与 JSON 字段、选择区滑块等级参数对应
CHARACTER_SKILL_TYPES = (
    ("战技", "战技倍率"),
    ("连携技", "连携技倍率"),
    ("终结技", "终结技倍率"),
)

NO_DAMAGE_MULTIPLIER_TEXT = "无伤害倍率"

# 武器 xxx+ 中不按百分数展示的词条（JSON 为去掉 % 的数值，展示为整数）
WEAPON_INTEGER_BONUS_ATTR_KEY = "源石技艺"


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
    """
    根据等级获取属性值

    参数：
        data: 角色/武器数据字典
        level: 当前选中的等级
        attr_name: 属性名称

    返回：
        属性值字符串，如果不存在或等级超出范围则返回空字符串
    """
    if attr_name not in data:
        return ""

    value = data[attr_name]
    if isinstance(value, list):
        # 等级从1开始，列表索引从0开始
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


def _resolve_selected_skill_for_damage(
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
) -> list[str]:
    """构建单段伤害计算模式的展示行。"""
    if not char_data or not weapon_data:
        return ["请选择有效角色和武器"]

    skill_label, skill_multiplier, skill_warning = _resolve_selected_skill_for_damage(
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
            enemy_defense=100.0,
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


def build_single_skill_search_preview_lines(
    *,
    char_data: Optional[Dict[str, Any]],
    weapon_data: Optional[Dict[str, Any]],
    char_level: int,
    weapon_level: int,
    trust_level: int = 0,
    skill_1_level: int = 0,
    skill_2_level: int = 0,
    skill_3_level: int = 0,
    preview_weapon_candidates: Optional[list[WeaponCandidate]] = None,
    preview_scope_label: str = "",
    preview_equipment_catalog: Optional[Dict[str, list[dict]]] = None,
    preview_equipment_scope_label: str = "",
) -> list[str]:
    """构建单技能遍历模式的快速预览文案。"""
    if not char_data or not weapon_data:
        return ["请选择有效角色和武器"]
    if preview_equipment_catalog is None:
        try:
            equipment_rows = get_equipments()
        except DataLoadError:
            return [
                "计算模式: 单技能遍历(快速预览)",
                "未加载到本地装备数据，请先执行 sync_equipments.py --apply。",
            ]
        catalog = build_equipment_catalog_from_local_rows(equipment_rows)
    else:
        catalog = preview_equipment_catalog
    if not catalog["chest"] or not catalog["gloves"] or not catalog["accessories"]:
        return [
            "计算模式: 单技能遍历(快速预览)",
            "装备数据不完整（缺护甲/护手/配件），无法进行预览。",
        ]
    sampled_catalog = {
        "chest": catalog["chest"][:2],
        "gloves": catalog["gloves"][:2],
        "accessories": catalog["accessories"][:2],
    }
    skill_label, skill_multiplier, skill_warning = _resolve_selected_skill_for_damage(
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
        trust_level=trust_level,
    )
    candidates = preview_weapon_candidates or [
        WeaponCandidate(
            name=str(weapon_data.get("名称", "当前武器")),
            final_attack=float(final["final_attack"]),
        )
    ]
    result = search_best_single_skill_loadouts(
        base_context=DamageContext(
            final_attack=0.0,
            skill_multiplier=skill_multiplier,
            skill_type=skill_label.split()[0],
            enemy_defense=100.0,
        ),
        weapons=candidates,
        equipment_catalog=sampled_catalog,
        config=OptimizerConfig(
            top_n=3,
            warn_on_unfiltered=False,
            prune_non_beneficial=False,
        ),
    )
    lines = [
        "计算模式: 单技能遍历(快速预览)",
        f"技能: {skill_label}",
        f"候选范围: {preview_scope_label or '当前武器'}",
        f"装备范围: {preview_equipment_scope_label or '全部装备'}",
        f"预览组合数: {result.total_combinations}",
        "说明: 当前仅采样每个部位前2件装备；全量遍历请点武器区「全量遍历(弹窗结果)」。",
    ]
    if skill_warning:
        lines.append(f"提示: {skill_warning}")
    for idx, score in enumerate(result.top_results, start=1):
        loadout = score.loadout_names
        lines.append(
            f"Top{idx}: 武器:{score.weapon_name} 伤害 {score.final_damage:.1f} | "
            f"护甲:{loadout['chest']} 护手:{loadout['gloves']} "
            f"配件A:{loadout['accessory_a']} 配件B:{loadout['accessory_b']}"
        )
    if not result.top_results:
        lines.append("无可用结果，请检查装备数据。")
    return lines


def _skill_multiplier_from_curve(
    char_data: Dict[str, Any],
    field_name: str,
    level: int,
) -> float:
    """从技能曲线读取第一段倍率（小数）。"""
    if level <= 0:
        return 0.0
    segments = char_data.get(field_name)
    if not isinstance(segments, list) or not segments:
        return 0.0
    first_segment = segments[0]
    if not isinstance(first_segment, list) or not first_segment:
        return 0.0
    idx = level - 1
    if not (0 <= idx < len(first_segment)):
        return 0.0
    value = first_segment[idx]
    if value is None:
        return 0.0
    return float(value) / 100.0


def build_multi_skill_search_preview_lines(
    *,
    char_data: Optional[Dict[str, Any]],
    weapon_data: Optional[Dict[str, Any]],
    char_level: int,
    weapon_level: int,
    trust_level: int = 0,
    skill_1_level: int = 0,
    skill_2_level: int = 0,
    skill_3_level: int = 0,
    manual_weights: Optional[Dict[str, float]] = None,
    use_manual_weights: bool = False,
) -> list[str]:
    """构建多技能遍历模式的快速预览文案。"""
    if not char_data or not weapon_data:
        return ["请选择有效角色和武器"]
    try:
        equipment_rows = get_equipments()
    except DataLoadError:
        return [
            "计算模式: 多技能遍历(快速预览)",
            "未加载到本地装备数据，请先执行 sync_equipments.py --apply。",
        ]
    catalog = build_equipment_catalog_from_local_rows(equipment_rows)
    if not catalog["chest"] or not catalog["gloves"] or not catalog["accessories"]:
        return [
            "计算模式: 多技能遍历(快速预览)",
            "装备数据不完整（缺护甲/护手/配件），无法进行预览。",
        ]
    sampled_catalog = {
        "chest": catalog["chest"][:2],
        "gloves": catalog["gloves"][:2],
        "accessories": catalog["accessories"][:2],
    }
    multipliers = {
        "战技": _skill_multiplier_from_curve(char_data, "战技倍率", skill_1_level),
        "连携技": _skill_multiplier_from_curve(char_data, "连携技倍率", skill_2_level),
        "终结技": _skill_multiplier_from_curve(char_data, "终结技倍率", skill_3_level),
    }
    scenarios = [
        SkillScenario(skill_name=name, skill_multiplier=val, skill_type=name)
        for name, val in multipliers.items()
        if val > 0
    ]
    if not scenarios:
        scenarios = [SkillScenario(skill_name="战技", skill_multiplier=1.0, skill_type="战技")]
        selected_skill = "战技"
        warning = "未选择技能等级或无可用倍率，按战技 100% 预览。"
    else:
        selected_skill = scenarios[0].skill_name
        warning = ""
    final = calculate_final_attack_with_details(
        character=char_data,
        weapon=weapon_data,
        char_level=char_level,
        weapon_level=weapon_level,
        trust_level=trust_level,
    )
    config = MultiSkillConfig(
        selected_skill=selected_skill,
        top_n=3,
    )
    weight_desc = f"默认权重: 当前选中技能 {selected_skill}=1，其它=0"
    if use_manual_weights:
        weights = {
            "战技": float((manual_weights or {}).get("战技", 0.0)),
            "连携技": float((manual_weights or {}).get("连携技", 0.0)),
            "终结技": float((manual_weights or {}).get("终结技", 0.0)),
        }
        if all(v == 0.0 for v in weights.values()):
            return [
                "计算模式: 多技能遍历(快速预览)",
                "手动权重不能全为0，请至少设置一项 > 0。",
            ]
        config = MultiSkillConfig(
            selected_skill=selected_skill,
            top_n=3,
            weights=weights,
        )
        weight_desc = (
            "手动权重: "
            f"战技={weights['战技']:.2f}, 连携技={weights['连携技']:.2f}, 终结技={weights['终结技']:.2f}"
        )

    result = optimize_multi_skill_loadouts(
        base_context=DamageContext(
            final_attack=0.0,
            skill_multiplier=1.0,
            enemy_defense=100.0,
        ),
        weapons=[
            WeaponCandidate(
                name=str(weapon_data.get("名称", "当前武器")),
                final_attack=float(final["final_attack"]),
            )
        ],
        equipment_catalog=sampled_catalog,
        scenarios=scenarios,
        config=config,
    )
    lines = [
        "计算模式: 多技能遍历(快速预览)",
        f"预览组合数: {result.total_combinations}",
        weight_desc,
        "说明: 当前仅采样每个部位前2件装备；全量遍历请点武器区「全量遍历(弹窗结果)」。",
    ]
    if warning:
        lines.append(f"提示: {warning}")
    for idx, score in enumerate(result.top_results, start=1):
        breakdown_text = " / ".join(
            [f"{name}:{value:.1f}" for name, value in score.skill_breakdown.items()]
        )
        lines.append(
            f"Top{idx}: 总伤 {score.weighted_total_damage:.1f} | {breakdown_text}"
        )
    if not result.top_results:
        lines.append("无可用结果，请检查装备数据。")
    return lines


def _render_lines(
    target_scroll: ctk.CTkScrollableFrame,
    lines: list[str],
    *,
    font: ctk.CTkFont,
    text_color: str,
) -> None:
    """按顺序渲染文本行。"""
    for row, text in enumerate(lines):
        label = ctk.CTkLabel(
            target_scroll,
            text=text,
            font=font,
            text_color=text_color,
        )
        label.grid(row=row, column=0, sticky="w", pady=2)


def _render_placeholder(
    target_scroll: ctk.CTkScrollableFrame,
    message: str,
    *,
    font: ctk.CTkFont,
) -> None:
    """渲染空状态或错误提示。"""
    label = ctk.CTkLabel(
        target_scroll,
        text=message,
        font=font,
        text_color="#888888",
    )
    label.grid(row=0, column=0, sticky="w", pady=(6, 2))


def evaluate_display_state(
    char_data: Optional[Dict[str, Any]],
    weapon_data: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """评估本次确认后各列提示及右侧乘区是否可更新。"""
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


def confirm_selection(
    char_attr_scroll: 'ctk.CTkScrollableFrame | None',
    weapon_attr_scroll: 'ctk.CTkScrollableFrame | None',
    right_scroll: 'ctk.CTkScrollableFrame | None',
    char_panel: 'ChooseTypesStarsNamesLevels',
    weapon_panel: 'ChooseTypesStarsNamesLevels',
    big_font: ctk.CTkFont,
    small_font: ctk.CTkFont,
    calculation_mode: str = "zone_snapshot",
    multi_skill_manual_weights: Optional[Dict[str, float]] = None,
    use_manual_multi_skill_weights: bool = False,
    preview_weapon_candidates: Optional[list[WeaponCandidate]] = None,
    preview_scope_label: str = "",
    preview_equipment_catalog: Optional[Dict[str, list[dict]]] = None,
    preview_equipment_scope_label: str = "",
) -> None:
    """
    确认选择并刷新角色属性列、武器属性列，以及右侧乘区数据。

    参数：
        char_attr_scroll: 角色属性展示区域（滚动框架）
        weapon_attr_scroll: 武器属性展示区域（滚动框架）
        right_scroll: 右侧展示区域（滚动框架）- 乘区数据
        char_panel: 角色选择面板实例
        weapon_panel: 武器选择面板实例
        big_font: 大号字体（用于标题）
        small_font: 小号字体（用于内容）

    执行流程：
    1. 清空三个展示区域的组件
    2. 分别渲染角色属性与武器属性明细（无摘要）
    3. 角色和武器均有效时，刷新右侧乘区
    """
    # None 检查
    if char_attr_scroll is None or weapon_attr_scroll is None or right_scroll is None:
        return

    for widget in char_attr_scroll.winfo_children():
        widget.destroy()
    for widget in weapon_attr_scroll.winfo_children():
        widget.destroy()
    for widget in right_scroll.winfo_children():
        widget.destroy()

    char_data = char_panel.get_selected_data()
    weapon_data = weapon_panel.get_selected_data()
    state = evaluate_display_state(char_data, weapon_data)
    char_level = char_panel.get_level()
    weapon_level = weapon_panel.get_level()
    trust_level = char_panel.get_trust_level()
    if not state["char_message"] and char_data:
        char_lines = build_character_attribute_lines(
            char_data,
            char_level,
            skill_1_level=char_panel.get_skill_1_level(),
            skill_2_level=char_panel.get_skill_2_level(),
            skill_3_level=char_panel.get_skill_3_level(),
        )
        _render_lines(
            char_attr_scroll,
            char_lines,
            font=small_font,
            text_color="#B8B8B8",
        )
    else:
        _render_placeholder(char_attr_scroll, state["char_message"], font=small_font)

    special_ability_1_name = weapon_panel.get_special_ability_1_name()
    special_ability_1_level = weapon_panel.get_special_ability_1_level()
    special_ability_2_name = weapon_panel.get_special_ability_2_name()
    special_ability_2_level = weapon_panel.get_special_ability_2_level()
    special_ability_3_name = weapon_panel.get_special_ability_3_name()
    special_ability_3_level = weapon_panel.get_special_ability_3_level()
    weapon_special_name = weapon_panel.get_weapon_special_name()
    weapon_special_level = weapon_panel.get_weapon_special_level()
    weapon_special_2_name = weapon_panel.get_weapon_special_2_name()
    weapon_special_2_level = weapon_panel.get_weapon_special_2_level()

    if not state["weapon_message"] and weapon_data:
        weapon_lines = build_weapon_attribute_lines(
            weapon_data,
            weapon_level,
            sa1_name=special_ability_1_name,
            sa1_level=special_ability_1_level,
            sa2_name=special_ability_2_name,
            sa2_level=special_ability_2_level,
            sa3_name=special_ability_3_name,
            sa3_level=special_ability_3_level,
            ws_name=weapon_special_name,
            ws_level=weapon_special_level,
            ws2_name=weapon_special_2_name,
            ws2_level=weapon_special_2_level,
        )
        _render_lines(
            weapon_attr_scroll,
            weapon_lines,
            font=small_font,
            text_color="#4ECDC4",
        )
    else:
        _render_placeholder(weapon_attr_scroll, state["weapon_message"], font=small_font)

    if not state["can_update_zone"]:
        return

    _display_zone_data(
        right_scroll, char_data, weapon_data, char_level, weapon_level,
        special_ability_1_name, special_ability_1_level,
        special_ability_2_name, special_ability_2_level,
        special_ability_3_name, special_ability_3_level,
        weapon_special_name, weapon_special_level,
        weapon_special_2_name, weapon_special_2_level,
        trust_level,
        big_font, small_font,
        calculation_mode=calculation_mode,
        skill_1_level=char_panel.get_skill_1_level(),
        skill_2_level=char_panel.get_skill_2_level(),
        skill_3_level=char_panel.get_skill_3_level(),
        multi_skill_manual_weights=multi_skill_manual_weights,
        use_manual_multi_skill_weights=use_manual_multi_skill_weights,
        preview_weapon_candidates=preview_weapon_candidates,
        preview_scope_label=preview_scope_label,
        preview_equipment_catalog=preview_equipment_catalog,
        preview_equipment_scope_label=preview_equipment_scope_label,
    )


def _display_zone_data(
    right_scroll: ctk.CTkScrollableFrame,
    char_data: Optional[Dict[str, Any]],
    weapon_data: Optional[Dict[str, Any]],
    char_level: int,
    weapon_level: int,
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
    trust_level: int = 0,
    big_font: Optional[ctk.CTkFont] = None,
    small_font: Optional[ctk.CTkFont] = None,
    calculation_mode: str = "zone_snapshot",
    skill_1_level: int = 0,
    skill_2_level: int = 0,
    skill_3_level: int = 0,
    multi_skill_manual_weights: Optional[Dict[str, float]] = None,
    use_manual_multi_skill_weights: bool = False,
    preview_weapon_candidates: Optional[list[WeaponCandidate]] = None,
    preview_scope_label: str = "",
    preview_equipment_catalog: Optional[Dict[str, list[dict]]] = None,
    preview_equipment_scope_label: str = "",
) -> None:
    """
    在右侧区域展示乘区数据

    参数：
        right_scroll: 右侧展示区域（滚动框架）
        char_data: 角色数据字典（包含属性、主/副能力等）
        weapon_data: 武器数据字典（包含属性、特殊能力等）
        char_level: 角色等级（1-90）
        weapon_level: 武器等级（1-90）
        sa1_name: 第一个特殊能力名称（如"敏捷+"）
        sa1_level: 第一个特殊能力等级（1-9）
        sa2_name: 第二个特殊能力名称（如"物理伤害+"）
        sa2_level: 第二个特殊能力等级（1-9）
        sa3_name: 第三条附加属性名称（如"攻击力+"）
        sa3_level: 第三条附加属性等级（无第三条时为 0）
        ws_name: 武器「特殊能力」字段名称（如"源石技艺强度+"）
        ws_level: 武器「特殊能力」等级（0 表示开关关闭）
        trust_level: 信赖等级（0-4），信赖加成会加到角色主能力上
        big_font: 大号字体（用于标题）
        small_font: 小号字体（用于内容）

    返回：
        None

    展示顺序：
        1. 敌方防御减伤区
        2. 能力乘区（力量、敏捷、智识、意志）
        3. 能力值加成乘区
        4. 基础攻击力（角色+武器）
        5. 攻击加成攻击力
        6. 中间攻击力
        7. 最终攻击力
    """
    mode_title = "乘区数据" if calculation_mode == "zone_snapshot" else "单段伤害预览"
    zone_title = ctk.CTkLabel(
        right_scroll,
        text=f"=== {mode_title} ===",
        font=big_font,
        text_color="#FF6B6B",
    )
    zone_title.grid(row=0, column=0, sticky="w", pady=(5, 5))

    row_idx = 1
    if calculation_mode == "single_hit":
        for text in build_single_hit_damage_lines(
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
        ):
            label = ctk.CTkLabel(
                right_scroll,
                text=text,
                font=small_font,
                text_color="#B8B8B8",
            )
            label.grid(row=row_idx, column=0, sticky="w", pady=2)
            row_idx += 1
        return

    if calculation_mode == "single_skill_search":
        for text in build_single_skill_search_preview_lines(
            char_data=char_data,
            weapon_data=weapon_data,
            char_level=char_level,
            weapon_level=weapon_level,
            trust_level=trust_level,
            skill_1_level=skill_1_level,
            skill_2_level=skill_2_level,
            skill_3_level=skill_3_level,
            preview_weapon_candidates=preview_weapon_candidates,
            preview_scope_label=preview_scope_label,
            preview_equipment_catalog=preview_equipment_catalog,
            preview_equipment_scope_label=preview_equipment_scope_label,
        ):
            label = ctk.CTkLabel(
                right_scroll,
                text=text,
                font=small_font,
                text_color="#B8B8B8",
            )
            label.grid(row=row_idx, column=0, sticky="w", pady=2)
            row_idx += 1
        return

    if calculation_mode == "multi_skill_search":
        for text in build_multi_skill_search_preview_lines(
            char_data=char_data,
            weapon_data=weapon_data,
            char_level=char_level,
            weapon_level=weapon_level,
            trust_level=trust_level,
            skill_1_level=skill_1_level,
            skill_2_level=skill_2_level,
            skill_3_level=skill_3_level,
            manual_weights=multi_skill_manual_weights,
            use_manual_weights=use_manual_multi_skill_weights,
        ):
            label = ctk.CTkLabel(
                right_scroll,
                text=text,
                font=small_font,
                text_color="#B8B8B8",
            )
            label.grid(row=row_idx, column=0, sticky="w", pady=2)
            row_idx += 1
        return

    if calculation_mode != "zone_snapshot":
        tip = ctk.CTkLabel(
            right_scroll,
            text="该模式开发中，当前先支持“单段伤害计算”。",
            font=small_font,
            text_color="#888888",
        )
        tip.grid(row=row_idx, column=0, sticky="w", pady=(6, 2))
        return

    if char_data:
        selection = MultiplicativeZoneSelection(
            character=char_data,
            weapon=weapon_data,
            char_level=char_level,
            weapon_level=weapon_level,
            trust_level=trust_level,
            bonuses=WeaponBonusSelection(
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
            ),
        )
        for line in compute_multiplicative_zone_snapshot(selection):
            label = ctk.CTkLabel(
                right_scroll,
                text=line.text,
                font=small_font,
                text_color=line.color,
            )
            label.grid(row=row_idx, column=0, sticky="w", pady=2)
            row_idx += 1

    # 添加说明标签
    hint_label = ctk.CTkLabel(
        right_scroll,
        text="\n* 能力乘区已包含角色基础属性和武器加成",
        font=small_font,
        text_color="#666666"
    )
    hint_label.grid(row=row_idx, column=0, sticky="w", pady=(5, 2))
