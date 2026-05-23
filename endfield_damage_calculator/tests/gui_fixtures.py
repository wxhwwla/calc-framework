#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GUI 集成测试共用夹具（模拟面板 + 可选 CTk 根窗口）。"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Optional

_PKG = Path(__file__).resolve().parent.parent
_CHARACTERS_JSON = _PKG / "character_weapon_equipment" / "character_data" / "characters.json"
_WEAPONS_JSON = _PKG / "character_weapon_equipment" / "weapon_data" / "weapons.json"


def load_character_by_name(name: str) -> dict[str, Any]:
    with _CHARACTERS_JSON.open(encoding="utf-8") as f:
        for row in json.load(f):
            if row.get("名称") == name:
                return row
    raise KeyError(name)


def load_weapon_by_name(name: str) -> dict[str, Any]:
    with _WEAPONS_JSON.open(encoding="utf-8") as f:
        for row in json.load(f):
            if row.get("名称") == name:
                return row
    raise KeyError(name)


class MockSelectionPanel:
    """模拟 ChooseTypesStarsNamesLevels 的最小接口。"""

    def __init__(
        self,
        data: dict[str, Any],
        *,
        level: int = 1,
        trust: int = 0,
        skills: tuple[int, int, int] = (1, 0, 0),
    ) -> None:
        self._data = data
        self.selected_level = _StrVar(str(level))
        self.selected_type = _StrVar(str(data.get("类型", "")))
        self.selected_star = _StrVar(str(data.get("星级", "")))
        self.selected_name = _StrVar(str(data.get("名称", "")))
        self.trust_panel = SimpleNamespace(trust_level=_StrVar(str(trust)))
        self.skill_level_panel = SimpleNamespace(
            skill_1_level=_StrVar(str(skills[0])),
            skill_2_level=_StrVar(str(skills[1])),
            skill_3_level=_StrVar(str(skills[2])),
        )
        self.list_c_w = [data]

    def get_selected_data(self) -> Optional[dict[str, Any]]:
        name = (self.selected_name.get() or "").strip()
        for row in self.list_c_w:
            if str(row.get("名称", "")) == name:
                return row
        return self._data

    def get_level(self) -> int:
        return int(self.selected_level.get())

    def get_trust_level(self) -> int:
        return int(self.trust_panel.trust_level.get())

    def get_skill_1_level(self) -> int:
        return int(self.skill_level_panel.skill_1_level.get())

    def get_skill_2_level(self) -> int:
        return int(self.skill_level_panel.skill_2_level.get())

    def get_skill_3_level(self) -> int:
        return int(self.skill_level_panel.skill_3_level.get())

    def get_special_ability_1_name(self) -> str:
        return ""

    def get_special_ability_1_level(self) -> int:
        return 0

    def get_special_ability_2_name(self) -> str:
        return ""

    def get_special_ability_2_level(self) -> int:
        return 0

    def get_special_ability_3_name(self) -> str:
        return ""

    def get_special_ability_3_level(self) -> int:
        return 0

    def get_weapon_special_name(self) -> str:
        return ""

    def get_weapon_special_level(self) -> int:
        return 0

    def get_weapon_special_2_name(self) -> str:
        return ""

    def get_weapon_special_2_level(self) -> int:
        return 0


class _StrVar:
    def __init__(self, value: str) -> None:
        self._value = value

    def get(self) -> str:
        return self._value

    def set(self, value: str) -> None:
        self._value = value


def build_mock_app(
    *,
    char_name: str = "秋栗",
    weapon_name: str = "坚城铸造者",
    root: Any = None,
) -> SimpleNamespace:
    """组装 enhancement_controls / gui 辅助方法测试用的 app 替身。"""
    import customtkinter as ctk

    char = load_character_by_name(char_name)
    weapon = load_weapon_by_name(weapon_name)
    if root is None:
        root = ctk.CTk()
        root.withdraw()
        root._gui_fixture_owns_root = True  # type: ignore[attr-defined]
    else:
        root._gui_fixture_owns_root = False  # type: ignore[attr-defined]

    app = SimpleNamespace(
        app=root,
        char_panel=MockSelectionPanel(char, skills=(1, 0, 0)),
        weapon_panel=MockSelectionPanel(weapon),
        small_font=ctk.CTkFont(size=12),
        big_font=ctk.CTkFont(size=14, weight="bold"),
        calc_mode_var=ctk.StringVar(value="乘区快照"),
        single_skill_scope_var=ctk.StringVar(value="当前武器"),
        single_skill_equipment_scope_var=ctk.StringVar(value="全部装备"),
        use_manual_skill_counts_var=ctk.BooleanVar(value=False),
        skill_count_1_var=ctk.StringVar(value="1"),
        skill_count_2_var=ctk.StringVar(value="0"),
        skill_count_3_var=ctk.StringVar(value="0"),
        search_workers_var=ctk.StringVar(value="1"),
        _fixed_loadout_slots={},
        _enemy_defense=100.0,
        _plugin_enemy_id="",
        _schedule_confirm_calls=0,
    )

    def _manual_multi_skill_counts() -> dict[str, int]:
        return {
            "战技": int(app.skill_count_1_var.get()),
            "连携技": int(app.skill_count_2_var.get()),
            "终结技": int(app.skill_count_3_var.get()),
        }

    def _build_fixed_loadout_selection():
        from calculation.loadout_slot_search import FixedLoadoutSelection

        return FixedLoadoutSelection()

    def _current_calculation_mode() -> str:
        from gui_design.calc_mode_labels import calculation_mode_from_label

        return calculation_mode_from_label(str(app.calc_mode_var.get()))

    def _single_skill_preview_equipment_catalog():
        from data.equipment_catalog import get_equipment_catalog

        return get_equipment_catalog(scope_label=app.single_skill_equipment_scope_var.get())

    def _on_char_name_change() -> None:
        pass

    def _refresh_fixed_loadout_menus() -> None:
        pass

    def _schedule_confirm(*, force: bool = False) -> None:
        app._schedule_confirm_calls += 1

    app._manual_multi_skill_counts = _manual_multi_skill_counts
    app._build_fixed_loadout_selection = _build_fixed_loadout_selection
    app._current_calculation_mode = _current_calculation_mode
    app._single_skill_preview_equipment_catalog = _single_skill_preview_equipment_catalog
    app._on_char_name_change = _on_char_name_change
    app._refresh_fixed_loadout_menus = _refresh_fixed_loadout_menus
    app._schedule_confirm = _schedule_confirm
    return app


def destroy_mock_app_root(app: SimpleNamespace) -> None:
    """仅销毁由 build_mock_app 自行创建的根窗口。"""
    if getattr(app.app, "_gui_fixture_owns_root", False):
        app.app.destroy()


_CTK_AVAILABLE: bool | None = None


def ctk_available() -> bool:
    """探测 Tcl/CTk 是否可用（结果缓存，避免每个集成文件重复初始化）。"""
    global _CTK_AVAILABLE
    if _CTK_AVAILABLE is not None:
        return _CTK_AVAILABLE
    try:
        import customtkinter as ctk

        root = ctk.CTk()
        root.withdraw()
        root.destroy()
        _CTK_AVAILABLE = True
    except Exception:
        _CTK_AVAILABLE = False
    return _CTK_AVAILABLE
