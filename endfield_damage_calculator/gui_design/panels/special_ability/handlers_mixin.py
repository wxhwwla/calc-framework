#!/usr/bin/env python3
"""特殊能力面板：滑块回调。"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .panel import SpecialAbilityPanel


class SpecialAbilityHandlersMixin:
    """附加属性与特殊能力滑块 value 变更处理。"""

    def _on_ability_1_change(self: SpecialAbilityPanel, value: float) -> None:
        level = int(value)
        if self._ability_1_label:
            self._ability_1_label.configure(text=str(level))
        self.special_ability_1_level.set(str(level))

    def _on_ability_2_change(self: SpecialAbilityPanel, value: float) -> None:
        level = int(value)
        if self._ability_2_label:
            self._ability_2_label.configure(text=str(level))
        self.special_ability_2_level.set(str(level))

    def _on_ability_3_change(self: SpecialAbilityPanel, value: float) -> None:
        if not self.current_special_ability_3_name:
            return
        level = int(value)
        if self._ability_3_label:
            self._ability_3_label.configure(text=str(level))
        self.special_ability_3_level.set(str(level))

    def _on_weapon_special_change(self: SpecialAbilityPanel, value: float) -> None:
        if not self._weapon_special_available:
            return
        level = int(value)
        if self._weapon_special_value_label:
            self._weapon_special_value_label.configure(text=str(level))
        self.weapon_special_level.set(str(level))

    def _on_weapon_special_stack_change(self: SpecialAbilityPanel, value: float) -> None:
        if not self._weapon_special_available or self._weapon_special_max_stack <= 1:
            return
        stack = int(value)
        if self._weapon_special_stack_value_label:
            self._weapon_special_stack_value_label.configure(text=str(stack))
        self.weapon_special_stack.set(str(stack))

    def _on_weapon_special_2_change(self: SpecialAbilityPanel, value: float) -> None:
        if not self._weapon_special_2_available:
            return
        level = int(value)
        if self._weapon_special_2_value_label:
            self._weapon_special_2_value_label.configure(text=str(level))
        self.weapon_special_2_level.set(str(level))

    def _on_weapon_special_2_stack_change(self: SpecialAbilityPanel, value: float) -> None:
        if not self._weapon_special_2_available or self._weapon_special_2_max_stack <= 1:
            return
        stack = int(value)
        if self._weapon_special_2_stack_value_label:
            self._weapon_special_2_stack_value_label.configure(text=str(stack))
        self.weapon_special_2_stack.set(str(stack))
