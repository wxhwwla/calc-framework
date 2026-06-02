#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""搜索 GUI 参数解析测试。"""



import unittest

from games.endfield.gui.controls.search.search_settings import (
    format_parallel_workers_help,
    format_search_progress_text,
    get_cpu_parallel_info,
    resolve_parallel_workers,
    resolve_top_n,
)


class TestSearchSettings(unittest.TestCase):

    def test_resolve_parallel_workers_auto_and_numeric(self):

        self.assertEqual(resolve_parallel_workers("自动 (7 线程)", cpu_count=8), 7)

        self.assertEqual(resolve_parallel_workers("4", cpu_count=8), 4)

        self.assertEqual(resolve_parallel_workers("99", cpu_count=8), 8)



    def test_cpu_parallel_info_and_help_text(self):

        info = get_cpu_parallel_info(cpu_count=8)

        self.assertEqual(info.logical_cores, 8)

        self.assertEqual(info.recommended_workers, 7)

        self.assertEqual(info.max_workers, 8)

        help_text = format_parallel_workers_help(info, selected_workers=4)

        self.assertIn("8", help_text)

        self.assertIn("4", help_text)

        self.assertIn("死机", help_text)



    def test_resolve_top_n(self):

        self.assertEqual(resolve_top_n("10"), 10)

        self.assertEqual(resolve_top_n("bad", default=5), 5)



    def test_format_search_progress_text_includes_eta(self):

        text = format_search_progress_text(

            prefix="全量遍历",

            processed=50,

            total=100,

            eta_seconds=12.4,

        )

        self.assertIn("50/100", text)



    def test_format_search_progress_text_shows_total_and_remaining(self):

        from gui.controls.search.search_settings import format_search_progress_text



        text = format_search_progress_text(

            prefix="全量遍历",

            processed=50,

            total=100,

            eta_seconds=30.0,

            estimated_total_seconds=120.0,

        )

        self.assertIn("50/100", text)

        self.assertIn("总预计", text)

        self.assertIn("\n", text)





if __name__ == "__main__":

    unittest.main()

