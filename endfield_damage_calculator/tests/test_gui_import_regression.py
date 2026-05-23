#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GUI 模块导入回归：防止确认刷新路径缺少关键符号。"""

from __future__ import annotations

import unittest


class TestGuiImportRegression(unittest.TestCase):
    def test_gui_reexports_build_weapon_candidates(self) -> None:
        from calculation.single_skill_search_job import build_weapon_candidates
        from gui_design import gui

        self.assertIs(gui.build_weapon_candidates, build_weapon_candidates)

    def test_platform_patch_applied_before_customtkinter(self) -> None:
        import platform

        from utils.platform_win32_patch import apply_platform_win32_patch

        apply_platform_win32_patch()
        self.assertTrue(getattr(platform.win32_ver, "_edc_no_wmi_patch", False))

    def test_ctk_gui_module_imports_do_not_require_manual_patch(self) -> None:
        """PyInstaller 会单独 import 各 GUI 子模块，模块内须自带补丁。"""
        import gui_design.search_controls  # noqa: F401
        import gui_design.selection_panel  # noqa: F401
