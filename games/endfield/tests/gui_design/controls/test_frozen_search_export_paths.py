#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""打包模式下搜索导出目录应落在 exe 同级，而非系统临时目录。"""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from utils.app_paths import allocate_search_run_directory, default_search_output_root


class TestFrozenSearchExportPaths(unittest.TestCase):
    def test_default_output_root_is_next_to_exe_when_frozen(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            fake_exe = root / "终末地伤害计算器.exe"

            fake_exe.write_bytes(b"MZ")

            with patch.object(sys, "frozen", True, create=True), patch.object(sys, "executable", str(fake_exe)):
                output_root = default_search_output_root()

            self.assertEqual(output_root, root / "search_output")

    def test_allocate_run_directory_under_exe_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            fake_exe = root / "终末地伤害计算器.exe"

            fake_exe.write_bytes(b"MZ")

            with patch.object(sys, "frozen", True, create=True), patch.object(sys, "executable", str(fake_exe)):
                run_dir = allocate_search_run_directory(purpose="full_search")

            self.assertTrue(run_dir.is_relative_to(root))

            self.assertTrue(str(run_dir).startswith(str(root / "search_output")))


if __name__ == "__main__":
    unittest.main()
