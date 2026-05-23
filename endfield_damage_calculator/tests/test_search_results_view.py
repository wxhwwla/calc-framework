#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全量遍历结果弹窗文案测试。"""

import unittest

from calculation.loadout_optimizer import LoadoutScore
from gui_design.search_results_view import build_search_results_report_lines


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
        self.assertIn("Top1:", joined)
        self.assertIn("逐鳞3.0", joined)
        self.assertIn("5432.1", joined)
        self.assertIn("top_results.json", joined)


if __name__ == "__main__":
    unittest.main()
