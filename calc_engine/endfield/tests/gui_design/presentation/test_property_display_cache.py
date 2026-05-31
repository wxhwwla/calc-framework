#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""display_lines 预览缓存行为测试。"""

import unittest

from calc_engine.endfield.calc.core.result_cache import reset_global_result_cache
from games.endfield.gui_design.presentation.display_lines import build_single_hit_damage_lines


class TestPropertyDisplayCache(unittest.TestCase):
    def setUp(self) -> None:
        reset_global_result_cache()

    def _fixtures(self):
        char = {
            "名称": "测试",
            "战技倍率": [[150] * 3],
            "连携技倍率": [[100] * 3],
            "终结技倍率": [[50] * 3],
            "基础攻击力": [100] * 3,
        }
        weapon = {"名称": "武", "基础攻击力": [100] * 3}
        return char, weapon

    def test_single_hit_lines_cached_on_repeat(self) -> None:
        char, weapon = self._fixtures()
        kwargs = dict(
            char_data=char,
            weapon_data=weapon,
            char_level=1,
            weapon_level=1,
            skill_1_level=1,
        )
        first = build_single_hit_damage_lines(**kwargs)
        second = build_single_hit_damage_lines(**kwargs)
        self.assertEqual(first, second)
        self.assertTrue(any("最终伤害" in line for line in first))


if __name__ == "__main__":
    unittest.main()
