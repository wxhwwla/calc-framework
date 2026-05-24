#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""配装预设导入导出测试。"""

import json
import unittest

from gui_design.loadout_preset import (
    LoadoutPreset,
    export_preset_json,
    import_preset_json,
)


class TestLoadoutPreset(unittest.TestCase):
    def test_roundtrip_preserves_core_fields(self) -> None:
        preset = LoadoutPreset(
            char_name="测试干员",
            weapon_name="测试武器",
            char_level=80,
            weapon_level=90,
            trust_level=2,
            skill_levels=(10, 8, 0),
            calculation_mode="single_hit",
            weapon_scope="当前武器",
            equipment_scope="全部装备",
            fixed_equipment_names={
                "chest": "胸甲A",
                "gloves": None,
                "accessory_a": "配件1",
                "accessory_b": "配件2",
            },
            multi_skill_counts={"战技": 2, "连携技": 1, "终结技": 0},
            use_manual_multi_skill_counts=True,
            ui_state={
                "char_advanced_expanded": True,
                "weapon_advanced_expanded": False,
                "more_settings_expanded": True,
                "current_page": "高级页",
            },
        )
        text = export_preset_json(preset)
        restored = import_preset_json(text)
        self.assertEqual(restored.char_name, preset.char_name)
        self.assertEqual(restored.fixed_equipment_names["chest"], "胸甲A")
        self.assertTrue(restored.use_manual_multi_skill_counts)
        self.assertTrue(bool((restored.ui_state or {}).get("char_advanced_expanded")))
        self.assertFalse(bool((restored.ui_state or {}).get("weapon_advanced_expanded")))
        self.assertEqual((restored.ui_state or {}).get("current_page"), "高级页")

    def test_rejects_unknown_schema(self) -> None:
        with self.assertRaises(ValueError):
            import_preset_json(json.dumps({"schema": "other_v9"}))


if __name__ == "__main__":
    unittest.main()
