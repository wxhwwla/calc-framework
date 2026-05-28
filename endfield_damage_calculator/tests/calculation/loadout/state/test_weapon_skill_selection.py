#!/usr/bin/env python3
"""WeaponSkillSelection 接缝测试。"""

import unittest
from types import SimpleNamespace

from calculation.skills.weapon_selection import WeaponSkillSelection

_SAMPLE_WEAPON = {
    "名称": "示例武器",
    "normal_skills": [
        {"zone": 1, "effect": "敏捷+", "curve": [1.0] * 9},
        {"zone": 2, "effect": "攻击力+", "curve": [1.0] * 9},
    ],
    "special_skills": [
        {
            "zone": 3,
            "name": "施放战技后，攻击力+",
            "condition": "施放战技后",
            "effect": "攻击力+",
            "curve": [1.0] * 9,
            "max_stack": 2,
        },
    ],
}


class _StrVar:
    def __init__(self, value: str = "0") -> None:
        self._value = value

    def get(self) -> str:
        return self._value

    def set(self, value: str) -> None:
        self._value = str(value)


class TestWeaponSkillSelection(unittest.TestCase):
    def test_from_legacy_tuple_produces_preset_v2_view(self) -> None:
        selection = WeaponSkillSelection.from_legacy_tuple(
            ("敏捷+", 9, "攻击力+", 8, "", 0, "施放战技后，攻击力+", 7, 2, "", 1, 0)
        )
        view = selection.to_preset_view()
        self.assertEqual(view["weapon_normal_levels"], [9, 8])
        self.assertEqual(view["weapon_special_states"], [{"level": 7, "stack": 2}])

    def test_calculation_kwargs_uses_new_naming(self) -> None:
        selection = WeaponSkillSelection.from_legacy_tuple(("敏捷+", 9, "", 0, "", 0, "主能力+", 8, 1, "", 0, 0))
        kwargs = selection.calculation_kwargs()
        self.assertEqual(kwargs["normal_skill_1_name"], "敏捷+")
        self.assertEqual(kwargs["normal_skill_1_level"], 9)
        self.assertEqual(kwargs["special_skill_1_name"], "主能力+")
        self.assertEqual(kwargs["special_skill_1_level"], 8)
        self.assertEqual(kwargs["special_skill_1_stack"], 1)

    def test_from_preset_view_maps_levels_onto_weapon_schema_slots(self) -> None:
        selection = WeaponSkillSelection.from_preset_view(
            _SAMPLE_WEAPON,
            weapon_normal_levels=[9, 8],
            weapon_special_states=[{"level": 7, "stack": 2}],
        )
        kwargs = selection.calculation_kwargs()
        self.assertEqual(kwargs["normal_skill_1_name"], "敏捷+")
        self.assertEqual(kwargs["normal_skill_1_level"], 9)
        self.assertEqual(kwargs["normal_skill_2_name"], "攻击力+")
        self.assertEqual(kwargs["normal_skill_2_level"], 8)
        self.assertEqual(kwargs["special_skill_1_name"], "施放战技后，攻击力+")
        self.assertEqual(kwargs["special_skill_1_level"], 7)
        self.assertEqual(kwargs["special_skill_1_stack"], 2)

    def test_from_preset_view_roundtrips_with_to_preset_view(self) -> None:
        original = WeaponSkillSelection.from_legacy_tuple(
            ("敏捷+", 9, "攻击力+", 8, "", 0, "施放战技后，攻击力+", 7, 2, "", 0, 0)
        )
        view = original.to_preset_view()
        restored = WeaponSkillSelection.from_preset_view(
            _SAMPLE_WEAPON,
            weapon_normal_levels=view["weapon_normal_levels"],
            weapon_special_states=view["weapon_special_states"],
        )
        self.assertEqual(restored.to_preset_view(), view)
        self.assertEqual(
            restored.calculation_kwargs()["normal_skill_1_level"],
            original.calculation_kwargs()["normal_skill_1_level"],
        )

if __name__ == "__main__":
    unittest.main()
