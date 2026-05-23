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
