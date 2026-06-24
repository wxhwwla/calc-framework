#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""可选依赖探测与提示文案。"""

from __future__ import annotations

import unittest

from utils.optional_deps import (
    GUI_OPTIONAL_DEPS,
    format_missing_gui_extras,
    format_missing_runtime_dependencies,
    is_matplotlib_available,
    matplotlib_install_hint,
    missing_dependencies,
    missing_runtime_packages,
)


class TestOptionalDeps(unittest.TestCase):
    def test_matplotlib_hint_non_empty(self) -> None:
        self.assertIn("matplotlib", matplotlib_install_hint())

    def test_is_matplotlib_available_is_bool(self) -> None:
        self.assertIsInstance(is_matplotlib_available(), bool)

    def test_format_missing_gui_extras_returns_str(self) -> None:
        text = format_missing_gui_extras()

        self.assertIsInstance(text, str)

    def test_missing_dependencies_subset(self) -> None:
        missing = missing_dependencies(GUI_OPTIONAL_DEPS)

        self.assertLessEqual(len(missing), len(GUI_OPTIONAL_DEPS))

    def test_missing_runtime_packages_returns_list(self) -> None:
        missing = missing_runtime_packages()

        self.assertIsInstance(missing, list)

        for item in missing:
            self.assertEqual(len(item), 2)

    def test_format_missing_runtime_dependencies(self) -> None:
        text = format_missing_runtime_dependencies()

        self.assertIsInstance(text, str)

        if not is_matplotlib_available():
            self.assertIn("matplotlib", text)

            self.assertIn("pip install -e .", text)

    def test_gui_optional_deps_contains_pyyaml(self) -> None:
        names = [dep.module for dep in GUI_OPTIONAL_DEPS]

        self.assertIn("yaml", names)

    def test_format_missing_runtime_dependencies_all_installed(self) -> None:
        text = format_missing_runtime_dependencies()

        self.assertNotIn("未知", text)


if __name__ == "__main__":
    unittest.main()
