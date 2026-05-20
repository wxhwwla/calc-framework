#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""add_weapon 无副作用测试"""

import copy
import tempfile
import unittest
from pathlib import Path

from character_weapon_equipment.weapon_data.add_weapon import add_weapon


class TestAddWeaponNoMutation(unittest.TestCase):
    def test_bonus_attrs_not_mutated(self):
        bonus = {
            "意志+": {"base": 12, "growth": 48, "divisor": 5, "offset": 0, "special": [93]},
        }
        before = copy.deepcopy(bonus)
        with tempfile.TemporaryDirectory() as tmp:
            json_path = Path(tmp) / "weapons.json"
            json_path.write_text("[]", encoding="utf-8")
            add_weapon(
                name="测试武器",
                weapon_type="单手剑",
                star=3,
                base_atk={"base": 10, "growth": 10, "divisor": 5, "offset": 0},
                bonus_attrs=bonus,
                json_path=json_path,
            )
        self.assertEqual(bonus, before)
        self.assertIn("special", bonus["意志+"])


if __name__ == "__main__":
    unittest.main()
