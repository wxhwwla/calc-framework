#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""干员目录筛选测试。"""

from __future__ import annotations

import unittest

from games.arknights.operator_catalog import (
    STAR_TIERS,
    build_operator_index,
    filter_operator_index,
    load_operators_map,
)


class TestOperatorCatalog(unittest.TestCase):
    def test_filter_by_star_and_profession(self) -> None:
        ops = {
            "能天使": {"名称": "能天使", "星级": 6, "职业": "狙击", "分支": "速射手"},
            "12F": {"名称": "12F", "星级": 2, "职业": "术师", "分支": "扩散术师"},
        }
        index = build_operator_index(ops)
        filtered = filter_operator_index(
            index,
            active_stars={6},
            profession="狙击",
            branch="",
        )
        self.assertEqual([x["名称"] for x in filtered], ["能天使"])

    def test_filter_all_profession_and_branch(self) -> None:
        ops = {
            "能天使": {"名称": "能天使", "星级": 6, "职业": "狙击", "分支": "速射手"},
            "12F": {"名称": "12F", "星级": 2, "职业": "术师", "分支": "扩散术师"},
        }
        index = build_operator_index(ops)
        filtered = filter_operator_index(
            index,
            active_stars=set(STAR_TIERS),
            profession="全部",
            branch="全部分支",
        )
        self.assertEqual(len(filtered), 2)

    def test_load_map_has_many_operators(self) -> None:
        m = load_operators_map()
        if len(m) < 100:
            self.skipTest("本地无完整干员库")
        index = build_operator_index(m)
        self.assertGreaterEqual(len(index), 100)
        self.assertEqual(len(STAR_TIERS), 6)


if __name__ == "__main__":
    unittest.main()
