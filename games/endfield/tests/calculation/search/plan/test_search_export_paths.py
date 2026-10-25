#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""搜索导出目录测试。"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from utils.app_paths import (
    allocate_search_run_directory,
    default_search_output_root,
)


class TestSearchExportPaths(unittest.TestCase):
    def test_default_root_is_under_given_base_not_system_temp(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "calc-framework-endfield"

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

    @patch("utils.app_paths.time.time_ns", return_value=1779529790739543600)
    def test_allocate_unique_when_time_ns_collides(self, _mock_ns):
        """Windows CI 上连续调用可能得到相同 time_ns，仍须分配不同目录。"""

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)

            first = allocate_search_run_directory(purpose="full_search", base_dir=base)

            second = allocate_search_run_directory(purpose="full_search", base_dir=base)

            self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
