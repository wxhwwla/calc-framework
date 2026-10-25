#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""成长参数物化测试。"""

import unittest

from games.endfield.calc.core.data_generator import generate_character_attributes
from games.endfield.data_loading.curve_materialize import (
    GROWTH_PARAM_KEY,
    materialize_character_entity,
)


class TestCurveMaterialize(unittest.TestCase):
    def test_materialize_from_growth_params(self):
        params = {
            "力量": {"base": 10, "growth": 20, "divisor": 98, "offset": 0},
        }
        baked = generate_character_attributes(params)
        char = {"名称": "测试", GROWTH_PARAM_KEY: params}
        out = materialize_character_entity(char)
        self.assertEqual(out["力量"][:5], baked["力量"][:5])

    def test_passthrough_without_params(self):
        char = {"名称": "测试", "力量": [1, 2, 3]}
        out = materialize_character_entity(char)
        self.assertEqual(out["力量"], [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
