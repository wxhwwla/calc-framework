#!/usr/bin/env python3
"""角色武器类型过滤与多技能段行重建。"""

from __future__ import annotations

from gui_design.controls.multi_skill import rebuild_multi_skill_segment_rows


class AppCharWeaponLinkMixin:
    def _on_char_name_change(self, *args: str) -> None:
        """
        角色名称变化时的回调函数

        功能：
        1. 获取当前选中角色的武器类型
        2. 根据武器类型过滤可用武器列表
        3. 如果没有对应类型的武器，显示提示
        4. 更新武器面板的可用武器列表（保持选中的武器不变）
        5. 启用/禁用武器面板

        参数：
            *args: trace_add 回调参数（忽略）
        """
        assert self.char_panel is not None, "char_panel 未初始化"
        assert self.weapon_panel is not None, "weapon_panel 未初始化"

        # 获取当前选中的角色数据
        char_data = self.char_panel.get_selected_data()

        if not char_data:
            # 未选择角色，禁用武器面板
            self.weapon_panel.disable_panel()
            # 直接设置空数据，不调用 update_data_list 避免滑块问题
            self.weapon_panel.list_c_w = []
            self.weapon_panel.selected_name.set("")
            return

        # 获取角色的武器类型
        char_weapon_type = char_data.get("武器", "")

        if not char_weapon_type:
            # 角色没有指定武器类型
            self.weapon_panel.disable_panel()
            self.weapon_panel.list_c_w = []
            self.weapon_panel.selected_name.set("")
            return

        # 根据角色武器类型过滤武器列表
        filtered_weapons = [weapon for weapon in self.all_weapons if weapon.get("类型", "") == char_weapon_type]

        if not filtered_weapons:
            # 没有对应类型的武器，显示提示
            self.weapon_panel.disable_panel()
            self.weapon_panel.list_c_w = [
                {
                    "名称": f"暂未收录{char_weapon_type}类型武器",
                    "类型": char_weapon_type,
                    "星级": 0,
                    "等级": [],  # 空数组，避免显示等级滑块
                }
            ]
            # 手动设置菜单值
            self.weapon_panel.type_menu.configure(values=[char_weapon_type])
            self.weapon_panel.selected_type.set(char_weapon_type)
            self.weapon_panel.star_menu.configure(values=["0"])
            self.weapon_panel.selected_star.set("0")
            self.weapon_panel.name_menu.configure(values=[f"暂未收录{char_weapon_type}类型武器"])
            self.weapon_panel.selected_name.set(f"暂未收录{char_weapon_type}类型武器")
            # 清空等级显示
            if self.weapon_panel.level_label:
                self.weapon_panel.level_label.configure(text="")
            self.weapon_panel.selected_level.set("")
        else:
            # 保存当前选中的武器名称
            current_weapon_name = self.weapon_panel.selected_name.get()

            # 有可用武器，先启用面板再更新列表
            self.weapon_panel.enable_panel()
            self.weapon_panel.update_data_list(filtered_weapons)

            # 尝试恢复之前选中的武器（如果它在新的武器列表中）
            if current_weapon_name:
                weapon_names = [w["名称"] for w in filtered_weapons]
                if current_weapon_name in weapon_names:
                    self.weapon_panel.selected_name.set(current_weapon_name)

        rebuild_multi_skill_segment_rows(self)
