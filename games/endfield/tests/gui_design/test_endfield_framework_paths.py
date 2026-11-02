#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""终末地 GUI 框架路径解析回归测试（P0-01）。

背景：``gui/endfield_actions.py`` / ``gui/endfield_app.py`` 曾用
``Path(__file__).parents[4]`` 推导仓库根，从 ``games/endfield/gui/`` 上溯会落到
盘符根（如 ``E:\\``），导致适配器目录缺少 ``meta.json``。
"""

from __future__ import annotations

import unittest


class TestEndfieldFrameworkPaths(unittest.TestCase):
    def test_adapter_path_points_to_real_endfield_adapter(self) -> None:
        from games.endfield.gui import endfield_actions

        adapter = endfield_actions._FRAMEWORK_ADAPTER

        self.assertTrue(adapter.is_dir(), f"适配器目录不存在: {adapter}")
        self.assertTrue((adapter / "meta.json").is_file(), f"缺少 meta.json: {adapter}")
        self.assertTrue((adapter / "ui" / "layout.json").is_file(), f"缺少 layout.json: {adapter}")

    def test_framework_src_path_points_to_real_source_tree(self) -> None:
        from games.endfield.gui import endfield_app

        src = endfield_app._FRAMEWORK_SRC

        self.assertTrue((src / "calc_framework").is_dir(), f"框架源码目录不存在: {src}")


if __name__ == "__main__":
    unittest.main()
