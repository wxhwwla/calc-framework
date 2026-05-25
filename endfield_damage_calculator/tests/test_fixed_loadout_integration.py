#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""固定配装控件集成测试。"""

from __future__ import annotations

import unittest

import pytest

from calculation.equipment_system import build_runtime_equipment_from_wiki_draft

pytestmark = pytest.mark.integration

from tests.gui_fixtures import ctk_available


def _sample_catalog() -> dict:
    chest = build_runtime_equipment_from_wiki_draft(
        {
            "名称": "测试胸甲",
            "_wiki_params": {"装备种类": "护甲", "所属套组": "测试套"},
        }
    )
    loose = build_runtime_equipment_from_wiki_draft(
        {
            "名称": "散件护手",
            "_wiki_params": {"装备种类": "护手", "所属套组": ""},
        }
    )
    return {
        "chest": [chest],
        "gloves": [loose],
        "accessories": [
            build_runtime_equipment_from_wiki_draft(
                {
                    "名称": "测试配件",
                    "_wiki_params": {"装备种类": "配件", "所属套组": "测试套"},
                }
            )
        ],
    }


class TestFixedLoadoutIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not ctk_available():
            raise unittest.SkipTest("需要可用的 CustomTkinter / Tcl")
        import customtkinter as ctk

        cls._root = ctk.CTk()
        cls._root.withdraw()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._root.destroy()

    def setUp(self) -> None:
        import customtkinter as ctk
        from gui_design.fixed_loadout_controls import (
            create_fixed_loadout_controls,
            refresh_all_fixed_slot_menus,
            refresh_slot_equipment_menu,
            resolve_fixed_loadout_selection,
        )

        self._refresh_all_fixed_slot_menus = refresh_all_fixed_slot_menus
        self._refresh_slot_equipment_menu = refresh_slot_equipment_menu
        self._resolve_fixed_loadout_selection = resolve_fixed_loadout_selection

        self.frame = ctk.CTkFrame(self._root)
        self.changes: list[str] = []

        def on_change() -> None:
            self.changes.append("changed")

        self.slots = create_fixed_loadout_controls(
            self.frame,
            small_font=ctk.CTkFont(size=12),
            on_change=on_change,
        )
        self.catalog = _sample_catalog()

    def tearDown(self) -> None:
        self.frame.destroy()

    def test_create_four_slots(self) -> None:
        self.assertEqual(set(self.slots.keys()), {"chest", "gloves", "accessory_a", "accessory_b"})

    def test_resolve_fixed_chest_when_enabled(self) -> None:
        self._refresh_all_fixed_slot_menus(self.catalog, self.slots)
        binding = self.slots["chest"]
        binding.enabled_var.set(True)
        binding.equipment_var.set("测试胸甲")
        selection = self._resolve_fixed_loadout_selection(self.catalog, self.slots)
        self.assertIsNotNone(selection.chest)
        assert selection.chest is not None
        self.assertEqual(selection.chest.get("名称"), "测试胸甲")
        self.assertIsNone(selection.gloves)

    def test_refresh_slot_picks_first_when_current_invalid(self) -> None:
        binding = self.slots["gloves"]
        binding.enabled_var.set(True)
        self._refresh_slot_equipment_menu(binding, self.catalog)
        self.assertIn(binding.equipment_var.get(), ["散件护手"])

    def test_refresh_all_disables_menus_when_slot_off(self) -> None:
        self._refresh_all_fixed_slot_menus(self.catalog, self.slots)
        binding = self.slots["accessory_a"]
        self.assertEqual(str(binding.set_menu.cget("state")), "disabled")


if __name__ == "__main__":
    unittest.main()
