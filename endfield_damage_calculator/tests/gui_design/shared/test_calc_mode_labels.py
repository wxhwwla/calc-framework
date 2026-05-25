#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""计算模式文案与内部标识映射。"""

import unittest

from gui_design.shared.calc_mode_labels import (
    CALC_MODE_LABELS,
    DEFAULT_CALC_MODE_LABEL,
    calculation_mode_from_label,
)


class TestCalcModeLabels(unittest.TestCase):
    def test_default_label_is_chinese_not_internal_id(self):
        self.assertEqual(DEFAULT_CALC_MODE_LABEL, "单段伤害计算")
        self.assertNotIn("single_hit", CALC_MODE_LABELS)

    def test_maps_chinese_labels_to_internal_modes(self):
        self.assertEqual(calculation_mode_from_label("单段伤害计算"), "single_hit")
        self.assertEqual(calculation_mode_from_label("乘区快照"), "zone_snapshot")
        self.assertEqual(
            calculation_mode_from_label("单技能遍历(快速预览)"),
            "single_skill_search",
        )

    def test_maps_legacy_internal_id_for_compatibility(self):
        self.assertEqual(calculation_mode_from_label("single_hit"), "single_hit")


if __name__ == "__main__":
    unittest.main()
