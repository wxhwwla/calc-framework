#!/usr/bin/env python3
"""选择面板读取接口 Mixin（从 QtSelectionPanel 抽离以控制文件长度）。"""

from __future__ import annotations

from typing import Any


class PanelGettersMixin:
    """对外读取接口（混合入 QtSelectionPanel）。"""

    # ── 对外读取接口 ──────────────────────────────────

    def get_selected_data(self) -> dict[str, Any] | None:
        name = self.name_combo.currentText()
        if not name:
            return None
        return next((ch for ch in self.data_list if ch.get("名称") == name), None)

    def get_level(self) -> int:
        return self.level_slider.value()

    def get_skill_1_level(self) -> int:
        if self.skill_panel:
            return self.skill_panel.skill_1_level
        return 0

    def get_skill_2_level(self) -> int:
        if self.skill_panel:
            return self.skill_panel.skill_2_level
        return 0

    def get_skill_3_level(self) -> int:
        if self.skill_panel:
            return self.skill_panel.skill_3_level
        return 0

    def get_trust_level(self) -> int:
        if self.trust_panel:
            return self.trust_panel.trust_level
        return 0

    def get_normal_skill_1_name(self) -> str:
        if self.special_panel:
            return self.special_panel.current_special_ability_1_name
        return ""

    def get_normal_skill_1_level(self) -> int:
        if self.special_panel:
            return self.special_panel.get_normal_skill_level(0)
        return 0

    def get_normal_skill_2_name(self) -> str:
        if self.special_panel:
            return self.special_panel.current_special_ability_2_name
        return ""

    def get_normal_skill_2_level(self) -> int:
        if self.special_panel:
            return self.special_panel.get_normal_skill_level(1)
        return 0

    def get_normal_skill_3_name(self) -> str:
        if self.special_panel:
            return self.special_panel.current_special_ability_3_name
        return ""

    def get_normal_skill_3_level(self) -> int:
        if self.special_panel:
            return self.special_panel.get_normal_skill_level(2)
        return 0

    def get_special_skill_1_name(self) -> str:
        if self.special_panel:
            return self.special_panel.current_weapon_special_name
        return ""

    def get_special_skill_1_level(self) -> int:
        if self.special_panel:
            return self.special_panel.get_special_skill_level(0)
        return 1

    def get_special_skill_1_stack(self) -> int:
        if self.special_panel:
            return self.special_panel.get_special_skill_stack(0)
        return 0

    def get_special_skill_2_name(self) -> str:
        if self.special_panel:
            return self.special_panel.current_weapon_special_2_name
        return ""

    def get_special_skill_2_level(self) -> int:
        if self.special_panel:
            return self.special_panel.get_special_skill_level(1)
        return 1

    def get_special_skill_2_stack(self) -> int:
        if self.special_panel:
            return self.special_panel.get_special_skill_stack(1)
        return 0

    # ── 兼容旧命名 ──────────────────────────────────

    def get_special_ability_1_name(self) -> str:
        return self.get_normal_skill_1_name()

    def get_special_ability_1_level(self) -> int:
        return self.get_normal_skill_1_level()

    def get_special_ability_2_name(self) -> str:
        return self.get_normal_skill_2_name()

    def get_special_ability_2_level(self) -> int:
        return self.get_normal_skill_2_level()

    def get_special_ability_3_name(self) -> str:
        return self.get_normal_skill_3_name()

    def get_special_ability_3_level(self) -> int:
        return self.get_normal_skill_3_level()

    def get_weapon_special_name(self) -> str:
        return self.get_special_skill_1_name()

    def get_weapon_special_level(self) -> int:
        return self.get_special_skill_1_level()

    def get_weapon_special_stack(self) -> int:
        return self.get_special_skill_1_stack()

    def get_weapon_special_2_name(self) -> str:
        return self.get_special_skill_2_name()

    def get_weapon_special_2_level(self) -> int:
        return self.get_special_skill_2_level()

    def get_weapon_special_2_stack(self) -> int:
        return self.get_special_skill_2_stack()
