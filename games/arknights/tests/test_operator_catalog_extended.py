#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""干员目录筛选扩展测试。"""

from __future__ import annotations

import unittest

from games.arknights.operator_catalog import (
    STAR_TIERS,
    build_operator_index,
    filter_operator_index,
)


def _make_ops() -> dict[str, dict[str, object]]:
    """创建一个小型干员数据集用于测试筛选。"""
    return {
        "能天使": {"名称": "能天使", "星级": 6, "职业": "狙击", "分支": "速射手"},
        "蓝毒": {"名称": "蓝毒", "星级": 5, "职业": "狙击", "分支": "速射手"},
        "杰西卡": {"名称": "杰西卡", "星级": 4, "职业": "狙击", "分支": "重射手"},
        "12F": {"名称": "12F", "星级": 2, "职业": "术师", "分支": "扩散术师"},
        "杜林": {"名称": "杜林", "星级": 2, "职业": "术师", "分支": "中坚术师"},
        "玫兰莎": {"名称": "玫兰莎", "星级": 3, "职业": "近卫", "分支": "无畏者"},
        "芬": {"名称": "芬", "星级": 3, "职业": "先锋", "分支": "尖兵"},
        "斑点": {"名称": "斑点", "星级": 3, "职业": "重装", "分支": "守护者"},
        "安赛尔": {"名称": "安赛尔", "星级": 3, "职业": "医疗", "分支": "医师"},
        "阿消": {"名称": "阿消", "星级": 4, "职业": "特种", "分支": "推击手"},
    }


class TestFilterByBranch(unittest.TestCase):
    """按分支筛选。"""

    def setUp(self) -> None:
        self.index = build_operator_index(_make_ops())

    def test_filter_by_branch_sniper(self) -> None:
        filtered = filter_operator_index(
            self.index,
            active_stars=set(range(1, 7)),
            branch="速射手",
        )
        names = [x["名称"] for x in filtered]
        self.assertIn("能天使", names)
        self.assertIn("蓝毒", names)
        self.assertNotIn("杰西卡", names)

    def test_filter_branch_and_profession(self) -> None:
        filtered = filter_operator_index(
            self.index,
            active_stars=set(range(1, 7)),
            profession="术师",
            branch="扩散术师",
        )
        names = [x["名称"] for x in filtered]
        self.assertEqual(names, ["12F"])

    def test_filter_branch_empty_string_returns_all(self) -> None:
        filtered = filter_operator_index(
            self.index,
            active_stars=set(range(1, 7)),
            branch="",
        )
        self.assertEqual(len(filtered), 10)

    def test_filter_branch_nonexistent_returns_empty(self) -> None:
        filtered = filter_operator_index(
            self.index,
            active_stars=set(range(1, 7)),
            branch="不存在的分支",
        )
        self.assertEqual(len(filtered), 0)


class TestFilterByMultipleStars(unittest.TestCase):
    """按多星级筛选。"""

    def setUp(self) -> None:
        self.index = build_operator_index(_make_ops())

    def test_active_stars_6_only(self) -> None:
        filtered = filter_operator_index(self.index, active_stars={6})
        names = [x["名称"] for x in filtered]
        self.assertEqual(names, ["能天使"])

    def test_active_stars_5_and_6(self) -> None:
        filtered = filter_operator_index(self.index, active_stars={5, 6})
        names = [x["名称"] for x in filtered]
        self.assertIn("能天使", names)
        self.assertIn("蓝毒", names)
        self.assertEqual(len(names), 2)

    def test_active_stars_all(self) -> None:
        filtered = filter_operator_index(self.index, active_stars=set(range(1, 7)))
        self.assertEqual(len(filtered), 10)

    def test_active_stars_empty_set(self) -> None:
        """空 active_stars，不匹配所有。"""
        filtered = filter_operator_index(self.index, active_stars=set())
        self.assertEqual(len(filtered), 0)

    def test_active_stars_nonexistent(self) -> None:
        """不存在的星级。"""
        filtered = filter_operator_index(self.index, active_stars={8})
        self.assertEqual(len(filtered), 0)


class TestSearchByName(unittest.TestCase):
    """按名称搜索。"""

    def setUp(self) -> None:
        self.index = build_operator_index(_make_ops())

    def test_search_full_name(self) -> None:
        filtered = filter_operator_index(
            self.index,
            active_stars=set(range(1, 7)),
            search="能天使",
        )
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["名称"], "能天使")

    def test_search_partial_match(self) -> None:
        filtered = filter_operator_index(
            self.index,
            active_stars=set(range(1, 7)),
            search="12",
        )
        names = [x["名称"] for x in filtered]
        self.assertIn("12F", names)

    def test_search_no_match(self) -> None:
        filtered = filter_operator_index(
            self.index,
            active_stars=set(range(1, 7)),
            search="银灰",
        )
        self.assertEqual(len(filtered), 0)

    def test_search_empty_string(self) -> None:
        filtered = filter_operator_index(
            self.index,
            active_stars=set(range(1, 7)),
            search="",
        )
        self.assertEqual(len(filtered), 10)

    def test_search_whitespace_only(self) -> None:
        filtered = filter_operator_index(
            self.index,
            active_stars=set(range(1, 7)),
            search="   ",
        )
        self.assertEqual(len(filtered), 10)


class TestEmptyIndex(unittest.TestCase):
    """空索引边界测试。"""

    def test_build_index_with_empty_dict(self) -> None:
        index = build_operator_index({})
        self.assertEqual(index, [])

    def test_filter_empty_index(self) -> None:
        filtered = filter_operator_index([], active_stars={6})
        self.assertEqual(filtered, [])


class TestBuildIndexEdgeCases(unittest.TestCase):
    """索引构建边界。"""

    def test_missing_fields_default_profession(self) -> None:
        ops = {"X": {"名称": "X"}}
        index = build_operator_index(ops)
        self.assertEqual(len(index), 1)
        self.assertEqual(index[0]["星级"], 0)
        self.assertEqual(index[0]["职业"], "")

    def test_missing_fields_default_branch(self) -> None:
        ops = {"X": {"名称": "X", "星级": 4, "职业": "狙击"}}
        index = build_operator_index(ops)
        self.assertEqual(index[0]["分支"], "")

    def test_single_operator(self) -> None:
        ops = {"A": {"名称": "A", "星级": 3, "职业": "先锋", "分支": "尖兵"}}
        index = build_operator_index(ops)
        self.assertEqual(len(index), 1)
        self.assertEqual(index[0]["名称"], "A")

    def test_sort_order_descending_star(self) -> None:
        """索引应按星级降序排列。"""
        ops = {
            "Low": {"名称": "Low", "星级": 1, "职业": "先锋"},
            "Mid": {"名称": "Mid", "星级": 3, "职业": "先锋"},
            "High": {"名称": "High", "星级": 6, "职业": "先锋"},
        }
        index = build_operator_index(ops)
        stars = [x["星级"] for x in index]
        self.assertEqual(stars, [6, 3, 1])


class TestStarTiersStructure(unittest.TestCase):
    """STAR_TIERS 常量验证。"""

    def test_star_tiers_has_6_elements(self) -> None:
        self.assertEqual(len(STAR_TIERS), 6)

    def test_star_tiers_contains_all_levels(self) -> None:
        self.assertEqual(set(STAR_TIERS), {6, 5, 4, 3, 2, 1})

    def test_star_tiers_is_tuple(self) -> None:
        self.assertIsInstance(STAR_TIERS, tuple)

    def test_star_tiers_descending(self) -> None:
        self.assertEqual(STAR_TIERS[0], 6)
        self.assertEqual(STAR_TIERS[1], 5)
        self.assertEqual(STAR_TIERS[5], 1)


class TestFilterCombinations(unittest.TestCase):
    """多条件组合筛选。"""

    def setUp(self) -> None:
        self.index = build_operator_index(_make_ops())

    def test_star_and_profession_and_search(self) -> None:
        """星级 + 职业 + 名称搜索三合一。"""
        filtered = filter_operator_index(
            self.index,
            active_stars={5},
            profession="狙击",
            search="蓝毒",
        )
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["名称"], "蓝毒")

    def test_star_and_branch(self) -> None:
        filtered = filter_operator_index(
            self.index,
            active_stars={2},
            branch="扩散术师",
        )
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["名称"], "12F")


if __name__ == "__main__":
    unittest.main()
