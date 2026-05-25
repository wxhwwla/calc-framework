#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""乘区快照：确认选择后的展示行测试。"""

import json
import unittest
from pathlib import Path

from calculation.multiplicative_zones.zone_snapshot import (
    MultiplicativeZoneSelection,
    WeaponBonusSelection,
    compute_multiplicative_zone_snapshot,
)

_CHARACTERS_JSON = (
    Path(__file__).resolve().parent.parent
    / "character_weapon_equipment"
    / "character_data"
    / "characters.json"
)
_WEAPONS_JSON = (
    Path(__file__).resolve().parent.parent
    / "character_weapon_equipment"
    / "weapon_data"
    / "weapons.json"
)


def _load_by_name(path: Path, name: str) -> dict:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    for item in data:
        if item.get("名称") == name:
            return item
    raise KeyError(name)


class TestZoneSnapshot(unittest.TestCase):
    def test_snapshot_includes_defense_and_final_attack_lines(self):
        char = _load_by_name(_CHARACTERS_JSON, "秋栗")
        weapon = _load_by_name(_WEAPONS_JSON, "逐鳞3.0")
        lines = compute_multiplicative_zone_snapshot(
            MultiplicativeZoneSelection(
                character=char,
                weapon=weapon,
                char_level=1,
                weapon_level=1,
                bonuses=WeaponBonusSelection(),
            )
        )
        texts = [line.text for line in lines]
        self.assertTrue(any(t.startswith("敌方防御减伤:") for t in texts))
        self.assertTrue(any(t.startswith("最终攻击力:") for t in texts))
        self.assertTrue(any(t.startswith("力量:") for t in texts))

    def test_snapshot_accepts_new_bonus_selection_names(self):
        char = _load_by_name(_CHARACTERS_JSON, "秋栗")
        weapon = _load_by_name(_WEAPONS_JSON, "逐鳞3.0")
        lines = compute_multiplicative_zone_snapshot(
            MultiplicativeZoneSelection(
                character=char,
                weapon=weapon,
                char_level=1,
                weapon_level=1,
                bonuses=WeaponBonusSelection(
                    normal_skill_1_name="智识+",
                    normal_skill_1_level=9,
                    normal_skill_2_name="终结技充能效率+",
                    normal_skill_2_level=9,
                    special_skill_1_name="源石技艺强度+",
                    special_skill_1_level=9,
                    special_skill_1_stack=0,
                ),
            )
        )
        texts = [line.text for line in lines]
        self.assertTrue(any(t.startswith("最终攻击力:") for t in texts))


if __name__ == "__main__":
    unittest.main()
