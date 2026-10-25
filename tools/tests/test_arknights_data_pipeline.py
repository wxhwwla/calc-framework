#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""明日方舟 arknights_scout → EntitySchema 转换器测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from tools.data_pipeline.transformers.from_arknights_scout import (
    _build_skills,
    _convert_operator,
    convert_all,
)


class TestBuildSkills(unittest.TestCase):
    """技能转换测试。"""

    def test_empty_skills_returns_empty_list(self) -> None:
        result = _build_skills({})
        self.assertEqual(result, [])

    def test_skills_with_no_name_but_sp_type_creates_entry(self) -> None:
        """没有名称但有 sp_type 的技能仍会创建条目。"""
        raw = {"技能": [{"sp_type": "自动回复"}]}
        result = _build_skills(raw)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["名称"], "")  # 名称留空

    def test_single_skill_with_sp_data(self) -> None:
        raw = {
            "技能": [
                {
                    "name": "战术咏唱",
                    "sp_type": "自动回复",
                    "trigger": "手动触发",
                    "levels": [
                        {"sp_cost": 40, "init_sp": 0, "duration": "30"},
                        {"sp_cost": 35, "init_sp": 5, "duration": "30"},
                    ],
                }
            ]
        }
        result = _build_skills(raw)
        self.assertEqual(len(result), 1)
        skill = result[0]
        self.assertEqual(skill["名称"], "战术咏唱")
        self.assertEqual(skill["标签"], "主动")
        self.assertFalse(skill["百分比"])
        self.assertEqual(skill["技能类型"], "自动回复")
        self.assertEqual(skill.get("备注"), "手动触发")
        self.assertIn("SP消耗", skill)
        self.assertEqual(skill["SP消耗"], [40, 35])

    def test_skill_with_invalid_sp_cost_skipped(self) -> None:
        raw = {
            "技能": [
                {
                    "name": "测试技能",
                    "levels": [
                        {"sp_cost": "auto"},  # 非数字
                        {"sp_cost": 10},
                    ],
                }
            ]
        }
        result = _build_skills(raw)
        self.assertEqual(len(result), 1)
        skill = result[0]
        # auto 不是有效数字，只有 10 被计入
        self.assertEqual(skill.get("SP消耗"), [10])


class TestConvertOperator(unittest.TestCase):
    """干员转换测试。"""

    def test_minimal_operator(self) -> None:
        raw = {"名称": "阿米娅", "_entity_type": "character"}
        result = _convert_operator(raw)
        self.assertEqual(result["名称"], "阿米娅")
        self.assertEqual(result["_entity_type"], "operator")
        self.assertEqual(result["技能"], [])

    def test_full_operator_passthrough_fields(self) -> None:
        raw = {
            "名称": "能天使",
            "_entity_type": "character",
            "星级": 6,
            "职业": "狙击",
            "分支": "速射手",
            "标签": "远程位",
            "特性": "优先攻击空中目标",
            "潜能": ["攻击力+30", "部署费用-1"],
        }
        result = _convert_operator(raw)
        self.assertEqual(result["星级"], 6)
        self.assertEqual(result["职业"], "狙击")
        self.assertEqual(result["分支"], "速射手")
        self.assertEqual(result["标签"], "远程位")
        self.assertEqual(result["特性"], "优先攻击空中目标")
        self.assertEqual(result["潜能"], ["攻击力+30", "部署费用-1"])

    def test_base_stats_are_flattened(self) -> None:
        raw = {
            "名称": "银灰",
            "基础属性": {"hp": 2580, "atk": 410, "def": 200, "res": 15},
        }
        result = _convert_operator(raw)
        self.assertEqual(result["生命上限"], 2580)
        self.assertEqual(result["攻击力"], 410)
        self.assertEqual(result["防御力"], 200)
        self.assertEqual(result["法术抗性"], 15)

    def test_trust_bonus_preserved(self) -> None:
        raw = {"名称": "闪灵", "信赖加成": {"攻击": 70, "生命": 200}}
        result = _convert_operator(raw)
        self.assertIn("信赖加成", result)
        self.assertEqual(result["信赖加成"]["攻击"], 70)

    def test_growth_params_preserved(self) -> None:
        raw = {
            "名称": "能天使",
            "成长参数": {"segments": [{"key": "e0.hp", "length": 50, "base": 711}]},
        }
        result = _convert_operator(raw)
        self.assertEqual(result["成长参数"]["segments"][0]["key"], "e0.hp")

    def test_talents_preserved(self) -> None:
        raw = {
            "名称": "塞雷娅",
            "天赋": [
                {"name": "药物配置", "description": "恢复友方生命"},
            ],
        }
        result = _convert_operator(raw)
        self.assertEqual(len(result["天赋"]), 1)
        self.assertEqual(result["天赋"][0]["name"], "药物配置")


class TestConvertAll(unittest.TestCase):
    """全量转换测试。"""

    def setUp(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp())
        self.parsed = self.tmpdir / "parsed"
        self.parsed.mkdir(parents=True)
        self.output = self.tmpdir / "output.json"

        # 创建两个示例干员
        amiya = {
            "名称": "阿米娅",
            "_entity_type": "character",
            "星级": 5,
            "职业": "术师",
            "技能": [{"name": "战术咏唱", "levels": [{"sp_cost": 40}]}],
            "基础属性": {"hp": 1500, "atk": 390, "def": 80, "res": 10},
        }
        texas = {
            "名称": "德克萨斯",
            "_entity_type": "character",
            "星级": 5,
            "职业": "先锋",
            "技能": [],
            "基础属性": {"hp": 1700, "atk": 330, "def": 130, "res": 0},
        }
        for name, data in [("阿米娅", amiya), ("德克萨斯", texas)]:
            (self.parsed / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

        # 创建一个非 dict 的文件（应被跳过）
        (self.parsed / "invalid.json").write_text("not json", encoding="utf-8")

    def tearDown(self) -> None:
        import shutil

        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_convert_all_success(self) -> None:
        stats = convert_all(self.parsed, self.output)
        self.assertTrue(stats["success"])
        self.assertEqual(stats["converted"], 2)
        self.assertEqual(stats["total_files"], 3)  # 2 valid + 1 invalid

        data = json.loads(self.output.read_text(encoding="utf-8"))
        self.assertEqual(len(data), 2)
        names = [d["名称"] for d in data]
        self.assertIn("阿米娅", names)
        self.assertIn("德克萨斯", names)

    def test_convert_all_missing_dir(self) -> None:
        stats = convert_all(self.tmpdir / "nonexistent", self.output)
        self.assertFalse(stats["success"])
        self.assertIn("error", stats)

    def test_output_contains_standard_entity_types(self) -> None:
        stats = convert_all(self.parsed, self.output)
        self.assertTrue(stats["success"])
        data = json.loads(self.output.read_text(encoding="utf-8"))
        for d in data:
            self.assertEqual(d["_entity_type"], "operator")


if __name__ == "__main__":
    unittest.main()
