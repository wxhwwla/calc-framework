#!/usr/bin/env python3
"""搜索文案格式化（无 GUI 依赖）测试。"""

import importlib
import inspect
import unittest

from utils.search_format import format_duration_human, format_workload_estimate_line


class TestSearchFormat(unittest.TestCase):
    def test_format_duration_human_under_one_minute(self):
        self.assertEqual(format_duration_human(45.0), "约 45 秒")

    def test_search_estimate_does_not_import_gui_design(self):
        mod = importlib.import_module("adapters.endfield.calc.search.plan.estimate")
        source = inspect.getsource(mod)
        self.assertNotIn("gui_design", source)

    def test_format_workload_estimate_line(self):
        from adapters.endfield.calc.search.plan.estimate import SearchDurationEstimate, SearchWorkloadPreview

        line = format_workload_estimate_line(
            workload=SearchWorkloadPreview(
                total_combinations=1000,
                weapon_count=2,
                loadout_combinations=500,
                warnings=(),
            ),
            duration=SearchDurationEstimate(
                total_combinations=1000,
                max_workers=4,
                estimated_seconds=30.0,
                seconds_per_combo=0.004,
            ),
        )
        self.assertIn("1,000", line)
        self.assertIn(format_duration_human(30.0), line)


if __name__ == "__main__":
    unittest.main()
