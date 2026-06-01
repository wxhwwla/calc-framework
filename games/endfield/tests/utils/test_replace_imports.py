#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""_replace_imports.py 模块测试。"""

from __future__ import annotations

import os
import tempfile
import unittest

from games.endfield._replace_imports import main, replace_in_file


class TestReplaceInFile(unittest.TestCase):
    def setUp(self) -> None:
        self._fd, self._path = tempfile.mkstemp(suffix=".py", text=True)

    def tearDown(self) -> None:
        os.close(self._fd)
        if os.path.exists(self._path):
            os.unlink(self._path)

    def _write(self, content: str) -> str:
        with open(self._path, "w", encoding="utf-8") as f:
            f.write(content)
        return self._path

    def test_replace_in_file_no_change_returns_false(self) -> None:
        path = self._write("x = 1\n")
        result = replace_in_file(path)
        self.assertFalse(result)

    def test_main_returns_list(self) -> None:
        result = main()
        self.assertIsInstance(result, list)


if __name__ == "__main__":
    unittest.main()
