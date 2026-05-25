#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""法术异常参数表测试。"""

import unittest

from calculation.spell_abnormal_params import SPELL_ABNORMAL_PARAM_ROWS


class TestSpellAbnormalParams(unittest.TestCase):
    def test_param_rows_are_unique_and_complete(self) -> None:
        keys = [row["key"] for row in SPELL_ABNORMAL_PARAM_ROWS]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertGreaterEqual(len(keys), 8)
        self.assertIn("灼热异常", keys)
        self.assertIn("灼热爆发", keys)

    def test_each_row_has_five_level_coeffs(self) -> None:
        for row in SPELL_ABNORMAL_PARAM_ROWS:
            coeffs = tuple(row["level_coeffs"])
            self.assertEqual(len(coeffs), 5)
            self.assertTrue(all(float(v) >= 0.0 for v in coeffs))


if __name__ == "__main__":
    unittest.main()
