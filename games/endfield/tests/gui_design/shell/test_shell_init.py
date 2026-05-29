#!/usr/bin/env python3
"""GUI 壳层 __init__ 测试。"""

from __future__ import annotations

import unittest

from gui_design.shell import current_backend, is_qt


class TestShellInit(unittest.TestCase):
    def test_current_backend_is_qt(self) -> None:
        self.assertEqual(current_backend(), "qt")

    def test_is_qt_returns_true(self) -> None:
        self.assertTrue(is_qt())


if __name__ == "__main__":
    unittest.main()
