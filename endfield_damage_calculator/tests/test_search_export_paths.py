#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""搜索导出目录测试。"""

import tempfile
import unittest
from pathlib import Path

from gui_design.search_export_paths import (
    allocate_search_run_directory,
    default_search_output_root,
)


class TestSearchExportPaths(unittest.TestCase):
    def test_default_root_is_under_given_base_not_system_temp(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "endfield_damage_calculator"
            base.mkdir()
            root = default_search_output_root(base_dir=base)
            self.assertEqual(root, base / "search_output")
            self.assertTrue(root.is_relative_to(base))

    def test_allocate_creates_unique_subdirectory(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            first = allocate_search_run_directory(purpose="full_search", base_dir=base)
            second = allocate_search_run_directory(purpose="full_search", base_dir=base)
            self.assertTrue(first.is_dir())
            self.assertTrue(second.is_dir())
            self.assertNotEqual(first, second)
            self.assertTrue(str(first).startswith(str(base)))


if __name__ == "__main__":
    unittest.main()
