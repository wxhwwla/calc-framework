# SPDX-License-Identifier: AGPL-3.0
from __future__ import annotations

import unittest

from games.endfield.calc.loadout.optimizer import LoadoutScore
from games.endfield.gui_design.presentation.search_results_lines import (
    _format_top_result_line,
    build_search_results_report_lines,
    export_paths_to_strings,
    loadout_scores_from_payload,
)
from pathlib import Path


class TestFormatTopResultLine(unittest.TestCase):
    def test_basic_no_breakdown(self) -> None:
        score = LoadoutScore(
            weapon_name="测试剑",
            final_damage=5000.0,
            loadout_names={"chest": "甲", "gloves": "手", "accessory_a": "A", "accessory_b": "B"},
        )
        lines = _format_top_result_line(1, score, damage_metric="伤害")
        text = "\n".join(lines)
        self.assertIn("第1名", text)
        self.assertIn("测试剑", text)
        self.assertIn("5000.0", text)

    def test_with_segment_breakdown(self) -> None:
        score = LoadoutScore(
            weapon_name="多段剑",
            final_damage=6000.0,
            loadout_names={"chest": "甲", "gloves": "手", "accessory_a": "A", "accessory_b": "B"},
            segment_breakdown={"战技:1": 2000.0, "连携技:1": 4000.0},
        )
        lines = _format_top_result_line(
            1, score,
            damage_metric="加权总伤",
            segment_counts={"战技:1": 1, "连携技:1": 1},
        )
        text = "\n".join(lines)
        self.assertIn("加权总伤", text)
        self.assertIn("第1段", text)

    def test_empty_loadout_names(self) -> None:
        score = LoadoutScore(
            weapon_name="剑", final_damage=100.0, loadout_names={}
        )
        lines = _format_top_result_line(1, score)
        self.assertTrue(any("剑" in l for l in lines))

    def test_abnormal_breakdown(self) -> None:
        score = LoadoutScore(
            weapon_name="剑",
            final_damage=5000.0,
            loadout_names={},
            segment_breakdown={"战技:1": 3000.0, "猛击:3": 1000.0, "倒地:1": 1000.0},
        )
        lines = _format_top_result_line(
            1, score,
            damage_metric="加权总伤",
            segment_counts={"战技:1": 1},
            abnormal_counts={"猛击:3": 1, "倒地:1": 1},
        )
        text = "\n".join(lines)
        self.assertIn("猛击", text)
        self.assertIn("倒地", text)


class TestBuildSearchResultsReportLines(unittest.TestCase):
    def test_empty_results(self) -> None:
        lines = build_search_results_report_lines(
            mode_label="全量遍历",
            skill_label="战技",
            processed_combinations=0,
            total_combinations=100,
            top_results=[],
        )
        self.assertTrue(any("无可用前列" in l for l in lines))

    def test_cancelled_flag(self) -> None:
        score = LoadoutScore(weapon_name="剑", final_damage=100.0, loadout_names={})
        lines = build_search_results_report_lines(
            mode_label="全量遍历",
            skill_label="战技",
            processed_combinations=50,
            total_combinations=100,
            top_results=[score],
            cancelled=True,
        )
        text = "\n".join(lines)
        self.assertIn("已取消", text)
        self.assertIn("前列配装", text)

    def test_with_export_paths(self) -> None:
        score = LoadoutScore(weapon_name="剑", final_damage=100.0, loadout_names={})
        lines = build_search_results_report_lines(
            mode_label="全量遍历",
            skill_label="战技",
            processed_combinations=100,
            total_combinations=100,
            top_results=[score],
            export_paths={"CSV": "/tmp/result.csv"},
        )
        text = "\n".join(lines)
        self.assertIn("导出文件", text)
        self.assertIn("result.csv", text)

    def test_scope_labels(self) -> None:
        score = LoadoutScore(weapon_name="剑", final_damage=100.0, loadout_names={})
        lines = build_search_results_report_lines(
            mode_label="全量遍历",
            skill_label="战技",
            scope_labels=("5★武器", "全装备"),
            processed_combinations=100,
            total_combinations=100,
            top_results=[score],
        )
        text = "\n".join(lines)
        self.assertIn("5★武器", text)
        self.assertIn("全装备", text)


class TestLoadoutScoresFromPayload(unittest.TestCase):
    def test_empty(self) -> None:
        scores = loadout_scores_from_payload([])
        self.assertEqual(len(scores), 0)

    def test_single_row(self) -> None:
        rows = [
            {
                "weapon_name": "剑",
                "final_damage": 5000.0,
                "loadout_names": {"chest": "甲"},
                "segment_breakdown": {"战技:1": 5000.0},
            }
        ]
        scores = loadout_scores_from_payload(rows)
        self.assertEqual(len(scores), 1)
        self.assertEqual(scores[0].weapon_name, "剑")
        self.assertEqual(scores[0].final_damage, 5000.0)
        self.assertIsNotNone(scores[0].segment_breakdown)

    def test_missing_fields(self) -> None:
        rows = [{"weapon_name": "剑"}]
        scores = loadout_scores_from_payload(rows)
        self.assertEqual(len(scores), 1)
        self.assertEqual(scores[0].final_damage, 0.0)


class TestExportPathsToStrings(unittest.TestCase):
    def test_with_none_values(self) -> None:
        result = export_paths_to_strings({"csv": None, "json": "/tmp/a.json"})
        self.assertNotIn("csv", result)
        self.assertEqual(result["json"], str(Path("/tmp/a.json")))

    def test_empty(self) -> None:
        self.assertEqual(export_paths_to_strings({}), {})
