#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
属性展示模块

此模块包含确认选择并展示角色/武器属性的相关函数。
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


def confirm_selection(
    middle_scroll: 'ctk.CTkScrollableFrame | None',
    right_scroll: 'ctk.CTkScrollableFrame | None',
    char_panel: 'ChooseTypesStarsNamesLevels',
    weapon_panel: 'ChooseTypesStarsNamesLevels',
    big_font: ctk.CTkFont,
    small_font: ctk.CTkFont
) -> None:
    """
    确认选择并在中间区域展示角色和武器属性，在右侧区域展示乘区数据

    参数：
        middle_scroll: 中间展示区域（滚动框架）- 角色和武器属性
        right_scroll: 右侧展示区域（滚动框架）- 乘区数据
        char_panel: 角色选择面板实例
        weapon_panel: 武器选择面板实例
        big_font: 大号字体（用于标题）
        small_font: 小号字体（用于内容）

    执行流程：
    1. 清空中间区域的现有组件
    2. 获取用户选中的角色和武器数据
    3. 创建标签展示选中信息
    4. 根据等级展示对应的属性值（力量、敏捷、智识、意志、基础攻击力）
    5. 在右侧区域展示乘区数据（敌方防御区、敏捷、力量、智识、意志）
    """
    # None 检查
    if middle_scroll is None or right_scroll is None:
        return

    # 清空中间区域的所有子组件（避免重复显示）
    for widget in middle_scroll.winfo_children():
        widget.destroy()

    # 清空右侧区域的所有子组件
    for widget in right_scroll.winfo_children():
        widget.destroy()

    # 获取选中的角色数据
    char_data = char_panel.get_selected_data()
    # 获取选中的武器数据
    weapon_data = weapon_panel.get_selected_data()

    # 获取当前选中的等级
    char_level = char_panel.get_level()
    weapon_level = weapon_panel.get_level()
    
    # 获取信赖等级
    trust_level = char_panel.get_trust_level()

    # 创建角色信息展示标签
    char_label_text = f"角色：{char_data.get('名称', '未选择')}" if char_data else "角色：未选择"
    char_label = ctk.CTkLabel(
        middle_scroll,
        text=char_label_text,
        font=big_font,
        text_color="#00D4AA"
    )
    char_label.grid(row=0, column=0, sticky="w", pady=(5, 2))

    # 创建角色等级标签
    char_level_label = ctk.CTkLabel(
        middle_scroll,
        text=f"角色等级：{char_level}",
        font=small_font,
        text_color="white"
    )
    char_level_label.grid(row=1, column=0, sticky="w", pady=(0, 2))
    
    # 创建信赖等级标签
    trust_label = ctk.CTkLabel(
        middle_scroll,
        text=f"信赖等级：{trust_level}",
        font=small_font,
        text_color="#FF6B6B"
    )
    trust_label.grid(row=2, column=0, sticky="w", pady=(0, 2))
    
    # 显示技能等级（仅角色面板）
    skill_1_level = char_panel.get_skill_1_level()
    skill_2_level = char_panel.get_skill_2_level()
    skill_3_level = char_panel.get_skill_3_level()
    
    if skill_1_level > 0:
        skill_1_label = ctk.CTkLabel(
            middle_scroll,
            text=f"战技等级：{skill_1_level}",
            font=small_font,
            text_color="#4ECDC4"
        )
        skill_1_label.grid(row=3, column=0, sticky="w", pady=1)
    
    if skill_2_level > 0:
        skill_2_label = ctk.CTkLabel(
            middle_scroll,
            text=f"连携技等级：{skill_2_level}",
            font=small_font,
            text_color="#4ECDC4"
        )
        skill_2_label.grid(row=4, column=0, sticky="w", pady=1)
    
    if skill_3_level > 0:
        skill_3_label = ctk.CTkLabel(
            middle_scroll,
            text=f"终结技等级：{skill_3_level}",
            font=small_font,
            text_color="#4ECDC4"
        )
        skill_3_label.grid(row=5, column=0, sticky="w", pady=(1, 5))

    # 创建武器信息展示标签（始终显示）
    weapon_label_text = f"武器：{weapon_data.get('名称', '未选择')}" if weapon_data else "武器：未选择"
    weapon_label = ctk.CTkLabel(
        middle_scroll,
        text=weapon_label_text,
        font=big_font,
        text_color="#FFD700"
    )
    weapon_label.grid(row=6, column=0, sticky="w", pady=(2, 5))

    # 只有当有有效武器数据时才显示武器等级和特殊能力
    if weapon_data:
        # 创建武器等级标签
        weapon_level_label = ctk.CTkLabel(
            middle_scroll,
            text=f"武器等级：{weapon_level}",
            font=small_font,
            text_color="white"
        )
        weapon_level_label.grid(row=7, column=0, sticky="w", pady=(0, 2))

        # 获取并显示武器特殊能力等级选择
        special_ability_1_name = weapon_panel.get_special_ability_1_name()
        special_ability_1_level = weapon_panel.get_special_ability_1_level()
        special_ability_2_name = weapon_panel.get_special_ability_2_name()
        special_ability_2_level = weapon_panel.get_special_ability_2_level()
        special_ability_3_name = weapon_panel.get_special_ability_3_name()
        special_ability_3_level = weapon_panel.get_special_ability_3_level()

        # 显示特殊能力1等级
        if special_ability_1_name:
            sa1_label = ctk.CTkLabel(
                middle_scroll,
                text=f"  {special_ability_1_name}等级：{special_ability_1_level}",
                font=small_font,
                text_color="#4ECDC4"
            )
            sa1_label.grid(row=8, column=0, sticky="w", pady=1)
        
        # 显示特殊能力2等级
        if special_ability_2_name:
            sa2_label = ctk.CTkLabel(
                middle_scroll,
                text=f"  {special_ability_2_name}等级：{special_ability_2_level}",
                font=small_font,
                text_color="#4ECDC4"
            )
            sa2_label.grid(row=9, column=0, sticky="w", pady=1)
        
        weapon_special_name = weapon_panel.get_weapon_special_name()
        weapon_special_level = weapon_panel.get_weapon_special_level()

        if special_ability_3_name:
            sa3_label = ctk.CTkLabel(
                middle_scroll,
                text=f"  {special_ability_3_name}等级：{special_ability_3_level}",
                font=small_font,
                text_color="#4ECDC4"
            )
            sa3_label.grid(row=10, column=0, sticky="w", pady=1)

        if weapon_special_name:
            ws_status = "开启" if weapon_special_level > 0 else "关闭"
            ws_label = ctk.CTkLabel(
                middle_scroll,
                text=f"  {weapon_special_name}（特殊能力）等级：{weapon_special_level} ({ws_status})",
                font=small_font,
                text_color="#4ECDC4"
            )
            ws_label.grid(row=11, column=0, sticky="w", pady=(1, 5))

    # 添加分隔线（美化界面）
    separator = ctk.CTkFrame(
        middle_scroll,
        height=2,
        fg_color="gray"
    )
    separator.grid(row=11, column=0, sticky="ew", pady=5)

    # 如果有角色数据，展示等级对应的属性
    if char_data:
        char_title = ctk.CTkLabel(
            middle_scroll,
            text="=== 角色属性 ===",
            font=big_font,
            text_color="#00D4AA"
        )
        char_title.grid(row=12, column=0, sticky="w", pady=(5, 2))

        # 展示与等级相关的属性（力量、敏捷、智识、意志、基础攻击力）
        row_idx = 13
        for attr_name in LEVEL_ATTRIBUTES:
            value = _get_attribute_value(char_data, char_level, attr_name)
            if value:
                attr_label = ctk.CTkLabel(
                    middle_scroll,
                    text=f"  {attr_name}: {value}",
                    font=small_font,
                    text_color="#B8B8B8"
                )
                attr_label.grid(row=row_idx, column=0, sticky="w", pady=1)
                row_idx += 1

        # 添加额外分隔线
        separator2 = ctk.CTkFrame(
            middle_scroll,
            height=1,
            fg_color="#333333"
        )
        separator2.grid(row=row_idx, column=0, sticky="ew", pady=5)
        row_idx += 1

    # 如果有武器数据，展示等级对应的属性
    if weapon_data:
        # 重新获取武器特殊能力等级（解决变量作用域问题）
        special_ability_1_name = weapon_panel.get_special_ability_1_name()
        special_ability_1_level = weapon_panel.get_special_ability_1_level()
        special_ability_2_name = weapon_panel.get_special_ability_2_name()
        special_ability_2_level = weapon_panel.get_special_ability_2_level()
        special_ability_3_name = weapon_panel.get_special_ability_3_name()
        special_ability_3_level = weapon_panel.get_special_ability_3_level()
        
        weapon_title = ctk.CTkLabel(
            middle_scroll,
            text="=== 武器属性 ===",
            font=big_font,
            text_color="#FFD700"
        )
        # 初始化 row_idx，确保变量已绑定
        row_idx = 13
        if char_data:
            # 计算角色属性展示后的行索引（+1 是因为多了信赖等级显示）
            row_idx = 13 + len([attr for attr in LEVEL_ATTRIBUTES if _get_attribute_value(char_data, char_level, attr)]) + 2

        weapon_title.grid(row=row_idx, column=0, sticky="w", pady=(5, 2))
        row_idx += 1

        # 展示武器的基础属性（只显示武器实际拥有的属性）
        # 首先展示基础攻击力
        basic_attrs = ['基础攻击力']
        for attr_name in basic_attrs:
            value = _get_attribute_value(weapon_data, weapon_level, attr_name)
            if value:
                attr_label = ctk.CTkLabel(
                    middle_scroll,
                    text=f"  {attr_name}: {value}",
                    font=small_font,
                    text_color="#B8B8B8"
                )
                attr_label.grid(row=row_idx, column=0, sticky="w", pady=1)
                row_idx += 1

        # 获取用户选择的武器特殊能力等级（已在前面获取过，这里不再重复获取）

        # 展示武器的能力加成属性（所有以+结尾的属性）
        # 获取所有加成属性（以+结尾的字段）
        bonus_attrs = [key for key in weapon_data.keys() if key.endswith('+')]
        for attr_name in bonus_attrs:
            value = weapon_data[attr_name]
            if isinstance(value, list) and len(value) > 0:
                # 根据用户选择的特殊能力等级获取对应的值
                # 确定使用哪个等级
                if attr_name == special_ability_1_name:
                    level_index = special_ability_1_level - 1
                elif attr_name == special_ability_2_name:
                    level_index = special_ability_2_level - 1
                elif attr_name == special_ability_3_name:
                    level_index = special_ability_3_level - 1
                else:
                    # 默认取第一个潜能等级的值
                    level_index = 0
                
                # 确保索引有效
                if 0 <= level_index < len(value):
                    display_value = str(value[level_index])
                else:
                    display_value = str(value[0])
            else:
                display_value = str(value)
            attr_label = ctk.CTkLabel(
                middle_scroll,
                text=f"  {attr_name}: {display_value}",
                font=small_font,
                text_color="#4ECDC4"  # 使用不同颜色区分加成属性
            )
            attr_label.grid(row=row_idx, column=0, sticky="w", pady=1)
            row_idx += 1

        weapon_special_name = weapon_panel.get_weapon_special_name()
        weapon_special_level = weapon_panel.get_weapon_special_level()
        if weapon_special_name and weapon_special_name not in bonus_attrs:
            field = weapon_data.get('特殊能力', [])
            display_value = "0"
            if weapon_special_level > 0 and isinstance(field, list) and len(field) >= 3:
                values = field[2]
                if isinstance(values, list) and values:
                    idx = weapon_special_level - 1
                    display_value = str(values[idx]) if 0 <= idx < len(values) else str(values[0])
            attr_label = ctk.CTkLabel(
                middle_scroll,
                text=f"  {weapon_special_name}(特殊能力): {display_value}",
                font=small_font,
                text_color="#4ECDC4"
            )
            attr_label.grid(row=row_idx, column=0, sticky="w", pady=1)
            row_idx += 1

    special_ability_1_name = weapon_panel.get_special_ability_1_name()
    special_ability_1_level = weapon_panel.get_special_ability_1_level()
    special_ability_2_name = weapon_panel.get_special_ability_2_name()
    special_ability_2_level = weapon_panel.get_special_ability_2_level()
    special_ability_3_name = weapon_panel.get_special_ability_3_name()
    special_ability_3_level = weapon_panel.get_special_ability_3_level()
    weapon_special_name = weapon_panel.get_weapon_special_name()
    weapon_special_level = weapon_panel.get_weapon_special_level()

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
