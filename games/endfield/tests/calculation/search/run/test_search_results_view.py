#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""全量遍历结果弹窗文案测试。"""

import unittest

from games.endfield.calc.loadout.optimizer import LoadoutScore
from games.endfield.gui.presentation.search_results_lines import build_search_results_report_lines


class TestSearchResultsReportLines(unittest.TestCase):
    def test_report_lists_progress_and_top_loadouts(self):
        lines = build_search_results_report_lines(
            mode_label="单技能全量遍历",
            skill_label="战技 Lv5",
            scope_labels=("当前武器", "全部装备"),
            processed_combinations=12,
            total_combinations=100,
            top_results=(
                LoadoutScore(
                    weapon_name="逐鳞3.0",
                    final_damage=5432.1,
                    loadout_names={
                        "chest": "矿场轻甲",
                        "gloves": "矿场护手",
                        "accessory_a": "配件A",
                        "accessory_b": "配件B",
                    },
                ),
            ),
            export_paths={"json": "D:/out/top_results.json"},
        )

        joined = "\n".join(lines)

        self.assertIn("单技能全量遍历", joined)

        self.assertIn("12/100", joined)

        self.assertIn("第1名:", joined)

        self.assertIn("逐鳞3.0", joined)

        self.assertIn("5432.1", joined)

        self.assertIn("top_results.json", joined)

    def test_report_lists_physical_and_spell_abnormal_breakdown(self):
        lines = build_search_results_report_lines(
            mode_label="多技能全量遍历",
            skill_label="战技+异常",
            scope_labels=("当前武器", "全部装备"),
            processed_combinations=5,
            total_combinations=20,
            top_results=(
                LoadoutScore(
                    weapon_name="逐鳞3.0",
                    final_damage=9999.0,
                    loadout_names={
                        "chest": "矿场轻甲",
                        "gloves": "矿场护手",
                        "accessory_a": "配件A",
                        "accessory_b": "配件B",
                    },
                    segment_breakdown={
                        "战技:1": 1000.0,
                        "猛击:2": 200.0,
                        "灼热爆发:1": 300.0,
                    },
                ),
            ),
            damage_metric="加权总伤",
            segment_counts={"战技:1": 2},
            abnormal_counts={"猛击:2": 3},
            spell_abnormal_counts={"灼热爆发:1": 1},
        )

        joined = "\n".join(lines)

        self.assertIn("物理异常合计", joined)

        self.assertIn("法术异常合计", joined)

        self.assertIn("灼热爆发(爆发)", joined)


if __name__ == "__main__":
    unittest.main()
