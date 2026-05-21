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
from calculation.multiplicative_zones import (
    calculate_attribute_zones,
    calculate_attribute_zones_with_details,
    DefenseReductionZone,
    calculate_ability_bonus_with_details,
    calculate_final_attack_with_details
)


# 等级相关属性列表（需要根据等级从列表中提取对应值）
LEVEL_ATTRIBUTES = ['力量', '敏捷', '智识', '意志', '基础攻击力']


def format_weapon_bonus_display_value(raw: Any, *, is_first_skill: bool) -> str:
    """
    武器属性列中 xxx+ 与特殊能力字段的数值展示格式。

    - 第一技能（第一条 xxx+）：JSON 数值按整数展示，如 60.0 → 60
    - 其余附加属性与特殊能力字段：按百分数展示，JSON 数值即百分比，如 27.6 → 27.6%
    """
    try:
        num = float(raw)
    except (TypeError, ValueError):
        return str(raw)

    if is_first_skill:
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


def build_character_attribute_lines(
    char_data: Optional[Dict[str, Any]],
    level: int,
) -> list[str]:
    """构建角色属性列展示明细（不含摘要）。"""
    if not char_data:
        return []
    lines: list[str] = []
    for attr_name in LEVEL_ATTRIBUTES:
        value = _get_attribute_value(char_data, level, attr_name)
        if value:
            lines.append(f"{attr_name}: {value}")
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
            is_first_skill=(attr_name == sa1_name),
        )
        lines.append(f"{attr_name}: {display_value}")

    if ws_name and ws_name not in bonus_attrs:
        field = weapon_data.get("特殊能力", [])
        display_value = "0%"
        if ws_level > 0 and isinstance(field, list) and len(field) >= 3:
            values = field[2]
            if isinstance(values, list) and values:
                idx = ws_level - 1
                raw_value = values[idx] if 0 <= idx < len(values) else values[0]
                display_value = format_weapon_bonus_display_value(
                    raw_value,
                    is_first_skill=False,
                )
        lines.append(f"{ws_name}(特殊能力): {display_value}")
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
    small_font: ctk.CTkFont
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
        char_lines = build_character_attribute_lines(char_data, char_level)
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
        trust_level,
        big_font, small_font
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
    trust_level: int = 0,
    big_font: Optional[ctk.CTkFont] = None,
    small_font: Optional[ctk.CTkFont] = None
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
    # 创建乘区标题
    zone_title = ctk.CTkLabel(
        right_scroll,
        text="=== 乘区数据 ===",
        font=big_font,
        text_color="#FF6B6B"
    )
    zone_title.grid(row=0, column=0, sticky="w", pady=(5, 5))

    row_idx = 1

    # 1. 敌方防御区
    defense_zone = DefenseReductionZone()
    defense_value = defense_zone.calculate()
    defense_label = ctk.CTkLabel(
        right_scroll,
        text=f"敌方防御减伤: {defense_value:.4f}",
        font=small_font,
        text_color="#4ECDC4"
    )
    defense_label.grid(row=row_idx, column=0, sticky="w", pady=2)
    row_idx += 1

    # 2. 能力乘区（按顺序：敏捷、力量、智识、意志）
    if char_data:
        # 使用带详细信息的计算函数（传递特殊能力等级和信赖等级）
        attr_details = calculate_attribute_zones_with_details(
            char_data, weapon_data, level=char_level,
            sa1_name=sa1_name, sa1_level=sa1_level,
            sa2_name=sa2_name, sa2_level=sa2_level,
            sa3_name=sa3_name, sa3_level=sa3_level,
            ws_name=ws_name, ws_level=ws_level,
            trust_level=trust_level
        )

        # 按指定顺序展示
        display_order = ['力量', '敏捷', '智识', '意志']
        for attr_name in display_order:
            details = attr_details.get(attr_name, {'base': 0.0, 'bonus': 0.0, 'total': 0.0})
            base_value = details['base']
            bonus_value = details['bonus']
            total_value = details['total']

            # 构建显示文本：如果有武器加成，显示括号说明
            if bonus_value > 0:
                display_text = f"{attr_name}: {total_value:.1f} ({base_value:.1f}+{bonus_value:.1f})"
            else:
                display_text = f"{attr_name}: {total_value:.1f}"

            attr_label = ctk.CTkLabel(
                right_scroll,
                text=display_text,
                font=small_font,
                text_color="#B8B8B8"
            )
            attr_label.grid(row=row_idx, column=0, sticky="w", pady=2)
            row_idx += 1

    # 3. 能力值加成乘区
    if char_data:
        ability_details = calculate_ability_bonus_with_details(
            char_data, weapon_data, level=char_level,
            sa1_name=sa1_name, sa1_level=sa1_level,
            sa2_name=sa2_name, sa2_level=sa2_level,
            sa3_name=sa3_name, sa3_level=sa3_level,
            ws_name=ws_name, ws_level=ws_level,
            trust_level=trust_level
        )
        bonus_value = ability_details['bonus']
        main_attr = ability_details['main_attr']
        main_value = ability_details['main_value']
        sub_attr = ability_details['sub_attr']
        sub_value = ability_details['sub_value']
        
        # 构建显示文本：能力值加成: 值 (主能力*0.005+副能力*0.002)
        if main_attr and sub_attr:
            display_text = f"能力值加成: {bonus_value:.4f} ({main_attr}:{main_value:.1f}*0.005+{sub_attr}:{sub_value:.1f}*0.002)"
        else:
            display_text = f"能力值加成: {bonus_value:.4f}"
        
        ability_bonus_label = ctk.CTkLabel(
            right_scroll,
            text=display_text,
            font=small_font,
            text_color="#FFD700"
        )
        ability_bonus_label.grid(row=row_idx, column=0, sticky="w", pady=2)
        row_idx += 1

    # 4. 基础攻击力（角色+武器）
    if char_data:
        # 获取角色基础攻击力（使用角色等级）
        char_base_attack = 0.0
        char_level_index = char_level - 1
        if '基础攻击力' in char_data and isinstance(char_data['基础攻击力'], list):
            if 0 <= char_level_index < len(char_data['基础攻击力']):
                char_base_attack = float(char_data['基础攻击力'][char_level_index])
        
        # 获取武器基础攻击力（使用武器等级）
        weapon_base_attack = 0.0
        if weapon_data and '基础攻击力' in weapon_data and isinstance(weapon_data['基础攻击力'], list):
            weapon_level_index = weapon_level - 1
            if 0 <= weapon_level_index < len(weapon_data['基础攻击力']):
                weapon_base_attack = float(weapon_data['基础攻击力'][weapon_level_index])
        
        # 计算总基础攻击力
        total_base_attack = char_base_attack + weapon_base_attack
        
        # 构建显示文本：基础攻击力: 值 (角色值+武器值)
        display_text = f"基础攻击力: {total_base_attack:.1f} ({char_base_attack:.1f}+{weapon_base_attack:.1f})"
        
        base_attack_label = ctk.CTkLabel(
            right_scroll,
            text=display_text,
            font=small_font,
            text_color="#00D4AA"
        )
        base_attack_label.grid(row=row_idx, column=0, sticky="w", pady=2)
        row_idx += 1

    # 5. 攻击加成攻击力和中间攻击力
    if char_data:
        final_attack_details = calculate_final_attack_with_details(
            char_data, weapon_data,
            char_level=char_level, weapon_level=weapon_level,
            sa1_name=sa1_name, sa1_level=sa1_level,
            sa2_name=sa2_name, sa2_level=sa2_level,
            sa3_name=sa3_name, sa3_level=sa3_level,
            ws_name=ws_name, ws_level=ws_level,
            trust_level=trust_level
        )
        base_attack = final_attack_details['base_attack']
        attack_bonus_multiplier = final_attack_details['attack_bonus_multiplier']
        attack_bonus_attack = final_attack_details['attack_bonus_attack']
        additional_attack = final_attack_details['additional_attack']
        intermediate_attack = final_attack_details['intermediate_attack']
        final_attack = final_attack_details['final_attack']
        ability_bonus = final_attack_details['ability_bonus']
        
        # 显示攻击加成攻击力
        display_text = f"攻击加成攻击力: {attack_bonus_attack:.1f} ({base_attack:.1f}×{attack_bonus_multiplier:.3f})"
        attack_bonus_attack_label = ctk.CTkLabel(
            right_scroll,
            text=display_text,
            font=small_font,
            text_color="#9B59B6"
        )
        attack_bonus_attack_label.grid(row=row_idx, column=0, sticky="w", pady=2)
        row_idx += 1
        
        # 显示中间攻击力
        display_text = f"中间攻击力: {intermediate_attack:.1f} ({attack_bonus_attack:.1f}+{additional_attack:.1f})"
        intermediate_attack_label = ctk.CTkLabel(
            right_scroll,
            text=display_text,
            font=small_font,
            text_color="#3498DB"
        )
        intermediate_attack_label.grid(row=row_idx, column=0, sticky="w", pady=2)
        row_idx += 1
        
        # 显示最终攻击力
        display_text = f"最终攻击力: {final_attack:.1f} ({intermediate_attack:.1f}*({ability_bonus:.4f}+1))"
        final_attack_label = ctk.CTkLabel(
            right_scroll,
            text=display_text,
            font=small_font,
            text_color="#FF6B6B"
        )
        final_attack_label.grid(row=row_idx, column=0, sticky="w", pady=2)
        row_idx += 1

    # 添加说明标签
    hint_label = ctk.CTkLabel(
        right_scroll,
        text="\n* 能力乘区已包含角色基础属性和武器加成",
        font=small_font,
        text_color="#666666"
    )
    hint_label.grid(row=row_idx, column=0, sticky="w", pady=(5, 2))
