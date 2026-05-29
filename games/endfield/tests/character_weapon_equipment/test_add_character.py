#!/usr/bin/env python3
"""add_character 无副作用测试"""

import copy
import tempfile
import unittest
from pathlib import Path

from character_weapon_equipment.character_data.add_character import add_character


class TestAddCharacterNoMutation(unittest.TestCase):
    def test_skill_params_not_mutated(self):
        sk1 = [
            {"base": 100, "growth": 10, "divisor": 5, "offset": 0, "special": [200, 220, 240]},
        ]
        before = copy.deepcopy(sk1)
        growth = {"base": 10, "growth": 10, "divisor": 5, "offset": 0}
        with tempfile.TemporaryDirectory() as tmp:
            json_path = Path(tmp) / "characters.json"
            json_path.write_text("[]", encoding="utf-8")
            add_character(
                name="测试角色",
                char_type="近卫",
                star=4,
                primary="力量",
                secondary="敏捷",
                weapon="单手剑",
                strength=growth,
                agility=growth,
                intellect=growth,
                will=growth,
                base_atk=growth,
                sk1=sk1,
                sk2=[{"base": 50, "growth": 5, "divisor": 5, "offset": 0, "special": [80, 90, 100]}],
                sk3=[
                    {"base": 200, "growth": 20, "divisor": 5, "offset": 0, "special": [400, 450, 500]},
                    {"base": 150, "growth": 15, "divisor": 5, "offset": 0, "special": [300, 330, 360]},
                ],
                json_path=json_path,
            )
        self.assertEqual(sk1, before)
        self.assertIn("special", sk1[0])


if __name__ == "__main__":
    unittest.main()
