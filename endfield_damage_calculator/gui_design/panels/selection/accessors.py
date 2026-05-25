#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""选择面板：对外读取接口。"""

from __future__ import annotations

from typing import Any, Dict, Optional


class SelectionPanelAccessorsMixin:
    def get_selected_data(self) -> Optional[Dict[str, Any]]:
        """
        获取当前选中的角色/武器数据

        返回：
            当前选中的角色/武器数据字典，如果未选择或选中的是"暂未收录"提示则返回 None
        """
        name = self.selected_name.get()
        if not name:
            return None
        
        data = next((ch for ch in self.list_c_w if ch["名称"] == name), None)
        
        if data:
            # 检查是否是"暂未收录"提示（等级数组为空表示无效数据）
            levels = data.get("等级", [])
            if not levels:
                return None
        
        return data
    
    def get_level(self) -> int:
        """
        获取当前选中的等级

        返回：
            当前选中的等级（int），默认返回1
        """
        level_str = self.selected_level.get()
        return int(level_str) if level_str.isdigit() else 1
    
    def get_trust_level(self) -> int:
        """
        获取当前选中的信赖等级（仅角色面板有效）

        返回：
            当前选中的信赖等级（0-4），如果是武器面板则返回0
        """
        if self.trust_panel:
            trust_str = self.trust_panel.trust_level.get()
            return int(trust_str) if trust_str.isdigit() else 0
        return 0
    
    def get_normal_skill_1_name(self) -> str:
        """获取第一技能名称（仅武器面板有效）。"""
        if self.special_ability_panel:
            return self.special_ability_panel.current_special_ability_1_name
        return ""

    def get_special_ability_1_name(self) -> str:
        """兼容旧命名：第一技能名称。"""
        return self.get_normal_skill_1_name()

    def get_normal_skill_1_level(self) -> int:
        """获取第一技能等级（仅武器面板有效）。"""
        if self.special_ability_panel:
            level_str = self.special_ability_panel.special_ability_1_level.get()
            return int(level_str) if level_str.isdigit() else 0
        return 0

    def get_special_ability_1_level(self) -> int:
        """兼容旧命名：第一技能等级。"""
        return self.get_normal_skill_1_level()

    def get_normal_skill_2_name(self) -> str:
        """获取第二技能名称（仅武器面板有效）。"""
        if self.special_ability_panel:
            return self.special_ability_panel.current_special_ability_2_name
        return ""

    def get_special_ability_2_name(self) -> str:
        """兼容旧命名：第二技能名称。"""
        return self.get_normal_skill_2_name()

    def get_normal_skill_2_level(self) -> int:
        """获取第二技能等级（仅武器面板有效）。"""
        if self.special_ability_panel:
            level_str = self.special_ability_panel.special_ability_2_level.get()
            return int(level_str) if level_str.isdigit() else 0
        return 0

    def get_special_ability_2_level(self) -> int:
        """兼容旧命名：第二技能等级。"""
        return self.get_normal_skill_2_level()

    def get_normal_skill_3_name(self) -> str:
        """获取第三技能名称（仅武器面板有效）。"""
        if self.special_ability_panel:
            return self.special_ability_panel.current_special_ability_3_name
        return ""

    def get_special_ability_3_name(self) -> str:
        """兼容旧命名：第三技能名称。"""
        return self.get_normal_skill_3_name()

    def get_normal_skill_3_level(self) -> int:
        """获取第三技能等级（仅武器面板有效）。"""
        if self.special_ability_panel:
            level_str = self.special_ability_panel.special_ability_3_level.get()
            return int(level_str) if level_str.isdigit() else 0
        return 0

    def get_special_ability_3_level(self) -> int:
        """兼容旧命名：第三技能等级。"""
        return self.get_normal_skill_3_level()

    def get_special_skill_1_name(self) -> str:
        """获取特殊一名称（仅武器面板有效）。"""
        if self.special_ability_panel:
            return self.special_ability_panel.current_weapon_special_name
        return ""

    def get_weapon_special_name(self) -> str:
        """兼容旧命名：特殊一名称。"""
        return self.get_special_skill_1_name()

    def get_special_skill_1_level(self) -> int:
        """获取特殊一等级（1-9）。"""
        if self.special_ability_panel:
            level_str = self.special_ability_panel.weapon_special_level.get()
            return int(level_str) if level_str.isdigit() else 1
        return 1

    def get_weapon_special_level(self) -> int:
        """兼容旧命名：特殊一等级。"""
        return self.get_special_skill_1_level()

    def get_special_skill_1_stack(self) -> int:
        """获取特殊一叠加层数。"""
        if self.special_ability_panel:
            stack_str = self.special_ability_panel.weapon_special_stack.get()
            return int(stack_str) if stack_str.isdigit() else 0
        return 0

    def get_weapon_special_stack(self) -> int:
        """兼容旧命名：特殊一叠加层数。"""
        return self.get_special_skill_1_stack()

    def get_special_skill_2_name(self) -> str:
        """获取特殊二名称（仅武器面板有效）。"""
        if self.special_ability_panel:
            return self.special_ability_panel.current_weapon_special_2_name
        return ""

    def get_weapon_special_2_name(self) -> str:
        """兼容旧命名：特殊二名称。"""
        return self.get_special_skill_2_name()

    def get_special_skill_2_level(self) -> int:
        """获取特殊二等级（1-9）。"""
        if self.special_ability_panel:
            level_str = self.special_ability_panel.weapon_special_2_level.get()
            return int(level_str) if level_str.isdigit() else 1
        return 1

    def get_weapon_special_2_level(self) -> int:
        """兼容旧命名：特殊二等级。"""
        return self.get_special_skill_2_level()

    def get_special_skill_2_stack(self) -> int:
        """获取特殊二叠加层数。"""
        if self.special_ability_panel:
            stack_str = self.special_ability_panel.weapon_special_2_stack.get()
            return int(stack_str) if stack_str.isdigit() else 0
        return 0

    def get_weapon_special_2_stack(self) -> int:
        """兼容旧命名：特殊二叠加层数。"""
        return self.get_special_skill_2_stack()

    def get_skill_1_level(self) -> int:
        """
        获取战技等级（仅角色面板有效）

        返回：
            战技等级（1-12），如果不存在则返回0
        """
        if self.skill_level_panel:
            level_str = self.skill_level_panel.skill_1_level.get()
            return int(level_str) if level_str.isdigit() else 0
        return 0
    
    def get_skill_2_level(self) -> int:
        """
        获取连携技等级（仅角色面板有效）

        返回：
            连携技等级（1-12），如果不存在则返回0
        """
        if self.skill_level_panel:
            level_str = self.skill_level_panel.skill_2_level.get()
            return int(level_str) if level_str.isdigit() else 0
        return 0
    
    def get_skill_3_level(self) -> int:
        """
        获取终结技等级（仅角色面板有效）

        返回：
            终结技等级（1-12），如果不存在则返回0
        """
        if self.skill_level_panel:
            level_str = self.skill_level_panel.skill_3_level.get()
            return int(level_str) if level_str.isdigit() else 0
        return 0

