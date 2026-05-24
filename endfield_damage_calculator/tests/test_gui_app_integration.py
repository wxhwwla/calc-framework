#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DamageCalculatorApp 轻量集成测试（构造主窗口并调用关键辅助方法）。"""

from __future__ import annotations

import tkinter
import unittest
from unittest.mock import patch

import pytest

from gui_design.gui_layout import (
    PRIMARY_ACTION_BUTTON_HEIGHT,
    SECONDARY_ACTION_BUTTON_HEIGHT,
)
from tests.gui_fixtures import ctk_available

pytestmark = pytest.mark.integration


class TestDamageCalculatorAppIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not ctk_available():
            raise unittest.SkipTest("需要可用的 CustomTkinter / Tcl")
        from data.loader import preload_game_data

        preload_game_data()

    def test_construct_app_and_invoke_helpers(self) -> None:
        with patch("utils.gui_window.apply_startup_maximized"):
            from gui_design.gui import DamageCalculatorApp

            app = DamageCalculatorApp()
            try:
                app.app.withdraw()
                counts = app._manual_multi_skill_counts()
                self.assertIsInstance(counts, dict)
                # 段级次数默认全 0
                for value in counts.values():
                    self.assertGreaterEqual(value, 0)
                mode = app._current_calculation_mode()
                self.assertIn(mode, ("zone_snapshot", "single_hit", "single_skill_search", "multi_skill_search"))
                fixed = app._build_fixed_loadout_selection()
                self.assertEqual(fixed.fixed_count(), 0)
                self.assertIsNotNone(app.char_panel)
                self.assertIsNotNone(app.weapon_panel)
                from gui_design.confirm_orchestrator import confirm_signature_now

                sig = confirm_signature_now(app)
                self.assertIsInstance(sig, tuple)
            finally:
                app.app.destroy()

    def test_on_window_resize_no_crash(self) -> None:
        with patch("utils.gui_window.apply_startup_maximized"):
            from gui_design.gui import DamageCalculatorApp

            app = DamageCalculatorApp()
            try:
                app.app.withdraw()
                app._on_window_resize(type("E", (), {"widget": app.app, "width": 800, "height": 600})())
            finally:
                app.app.destroy()

    def test_switch_between_pages_preserves_user_inputs(self) -> None:
        """在计算页/高级页切换时，不应重置已填写的输入状态。"""
        with patch("utils.gui_window.apply_startup_maximized"):
            from gui_design.gui import DamageCalculatorApp

            try:
                app = DamageCalculatorApp()
            except tkinter.TclError as exc:
                raise unittest.SkipTest(f"Tcl 不可用，跳过切页状态测试：{exc}") from exc
            try:
                app.app.withdraw()
                self.assertIsNotNone(app.page_tabs)
                self.assertIsNotNone(app.char_panel)
                self.assertIsNotNone(app.weapon_panel)

                original_char = app.char_panel.selected_name.get()
                app.calc_mode_var.set("单技能全量遍历")

                segment_vars = getattr(app, "_segment_count_vars", {})
                first_segment_key = next(iter(segment_vars), None)
                if first_segment_key is not None:
                    segment_vars[first_segment_key].set("3")

                app._show_advanced_page()
                self.assertEqual(app.page_tabs.get(), "高级页")
                app._show_main_page()
                self.assertEqual(app.page_tabs.get(), "计算页")

                self.assertEqual(app.char_panel.selected_name.get(), original_char)
                self.assertEqual(app.calc_mode_var.get(), "单技能全量遍历")
                if first_segment_key is not None:
                    self.assertEqual(
                        app._segment_count_vars[first_segment_key].get(),  # type: ignore[index]
                        "3",
                    )
                self.assertEqual(app._ui_preferences.get("last_page"), "计算页")
            finally:
                app.app.destroy()

    def test_main_page_selection_uses_non_scroll_containers(self) -> None:
        """计算页角色/武器选择区默认使用普通容器，避免主流程依赖滚动。"""
        with patch("utils.gui_window.apply_startup_maximized"):
            from gui_design.gui import DamageCalculatorApp

            try:
                app = DamageCalculatorApp()
            except tkinter.TclError as exc:
                raise unittest.SkipTest(f"Tcl 不可用，跳过主页容器测试：{exc}") from exc
            try:
                app.app.withdraw()
                self.assertIsNotNone(app.char_frame)
                self.assertIsNotNone(app.weapon_frame)

                char_child_types = {
                    child.winfo_class() for child in app.char_frame.winfo_children()  # type: ignore[union-attr]
                }
                weapon_child_types = {
                    child.winfo_class() for child in app.weapon_frame.winfo_children()  # type: ignore[union-attr]
                }
                self.assertNotIn("ctk_scrollable_frame", char_child_types)
                self.assertNotIn("ctk_scrollable_frame", weapon_child_types)
            finally:
                app.app.destroy()

    def test_action_button_heights_follow_layout_contract(self) -> None:
        """主按钮与次按钮高度遵守统一尺寸约定。"""
        with patch("utils.gui_window.apply_startup_maximized"):
            from gui_design.gui import DamageCalculatorApp

            try:
                app = DamageCalculatorApp()
            except tkinter.TclError as exc:
                raise unittest.SkipTest(f"Tcl 不可用，跳过按钮尺寸测试：{exc}") from exc
            try:
                app.app.withdraw()
                self.assertIsNotNone(app.confirm_btn)
                self.assertIsNotNone(app.main_confirm_btn)
                self.assertIsNotNone(app.back_to_main_btn)
                self.assertIsNotNone(app.goto_advanced_btn)
                self.assertEqual(
                    int(float(app.confirm_btn.cget("height"))),  # type: ignore[union-attr]
                    PRIMARY_ACTION_BUTTON_HEIGHT,
                )
                self.assertEqual(
                    int(float(app.main_confirm_btn.cget("height"))),  # type: ignore[union-attr]
                    PRIMARY_ACTION_BUTTON_HEIGHT,
                )
                self.assertEqual(
                    int(float(app.back_to_main_btn.cget("height"))),  # type: ignore[union-attr]
                    SECONDARY_ACTION_BUTTON_HEIGHT,
                )
                self.assertEqual(
                    int(float(app.goto_advanced_btn.cget("height"))),  # type: ignore[union-attr]
                    SECONDARY_ACTION_BUTTON_HEIGHT,
                )
            finally:
                app.app.destroy()

    def test_main_page_has_quick_confirm_button(self) -> None:
        """计算页应提供快速确认按钮，避免必须跳转到高级页。"""
        with patch("utils.gui_window.apply_startup_maximized"):
            from gui_design.gui import DamageCalculatorApp

            try:
                app = DamageCalculatorApp()
            except tkinter.TclError as exc:
                raise unittest.SkipTest(f"Tcl 不可用，跳过快速确认测试：{exc}") from exc
            try:
                app.app.withdraw()
                self.assertIsNotNone(app.main_confirm_btn)
                self.assertEqual(app.main_confirm_btn.cget("text"), "确认选择")  # type: ignore[union-attr]
            finally:
                app.app.destroy()

    def test_selection_panels_have_collapsible_advanced_params(self) -> None:
        """角色/武器面板应提供默认收起的高级参数折叠区。"""
        with patch("utils.gui_window.apply_startup_maximized"):
            from gui_design.gui import DamageCalculatorApp

            try:
                app = DamageCalculatorApp()
            except tkinter.TclError as exc:
                raise unittest.SkipTest(f"Tcl 不可用，跳过高级参数折叠测试：{exc}") from exc
            try:
                app.app.withdraw()
                self.assertIsNotNone(app.char_panel)
                self.assertIsNotNone(app.weapon_panel)

                char_panel = app.char_panel
                weapon_panel = app.weapon_panel
                self.assertFalse(bool(char_panel._show_advanced_params_var.get()))
                self.assertFalse(bool(weapon_panel._show_advanced_params_var.get()))
                self.assertIsNotNone(char_panel._advanced_toggle_btn)
                self.assertIsNotNone(weapon_panel._advanced_toggle_btn)
                self.assertIn("展开", char_panel._advanced_toggle_btn.cget("text"))  # type: ignore[union-attr]
                self.assertIn("展开", weapon_panel._advanced_toggle_btn.cget("text"))  # type: ignore[union-attr]

                char_panel._advanced_toggle_btn.invoke()  # type: ignore[union-attr]
                weapon_panel._advanced_toggle_btn.invoke()  # type: ignore[union-attr]
                self.assertTrue(bool(char_panel._show_advanced_params_var.get()))
                self.assertTrue(bool(weapon_panel._show_advanced_params_var.get()))
            finally:
                app.app.destroy()

    def test_advanced_page_reflows_to_two_rows_on_narrow_width(self) -> None:
        """高级页在窄宽度下应切为两行布局，缓解横向挤压。"""
        with patch("utils.gui_window.apply_startup_maximized"):
            from gui_design.gui import DamageCalculatorApp

            try:
                app = DamageCalculatorApp()
            except tkinter.TclError as exc:
                raise unittest.SkipTest(f"Tcl 不可用，跳过重排测试：{exc}") from exc
            try:
                app.app.withdraw()
                self.assertIsNotNone(app._control_col_actions)
                self.assertIsNotNone(app._control_col_search)
                self.assertIsNotNone(app._control_col_multi)

                app._apply_control_dock_layout(1100)
                self.assertEqual(int(app._control_col_actions.grid_info()["row"]), 0)  # type: ignore[union-attr]
                self.assertEqual(int(app._control_col_actions.grid_info()["column"]), 0)  # type: ignore[union-attr]
                self.assertEqual(int(app._control_col_actions.grid_info()["columnspan"]), 2)  # type: ignore[union-attr]
                self.assertEqual(int(app._control_col_search.grid_info()["row"]), 1)  # type: ignore[union-attr]
                self.assertEqual(int(app._control_col_multi.grid_info()["row"]), 1)  # type: ignore[union-attr]

                app._apply_control_dock_layout(1800)
                self.assertEqual(int(app._control_col_actions.grid_info()["row"]), 0)  # type: ignore[union-attr]
                self.assertEqual(int(app._control_col_actions.grid_info()["column"]), 0)  # type: ignore[union-attr]
                self.assertEqual(int(app._control_col_actions.grid_info()["columnspan"]), 1)  # type: ignore[union-attr]
                self.assertEqual(int(app._control_col_search.grid_info()["column"]), 1)  # type: ignore[union-attr]
                self.assertEqual(int(app._control_col_multi.grid_info()["column"]), 2)  # type: ignore[union-attr]
            finally:
                app.app.destroy()

    def test_search_button_texts_shorten_on_compact_layout(self) -> None:
        """窄屏时搜索主按钮应使用短文案，宽屏恢复全文案。"""
        with patch("utils.gui_window.apply_startup_maximized"):
            from gui_design.gui import DamageCalculatorApp

            try:
                app = DamageCalculatorApp()
            except tkinter.TclError as exc:
                raise unittest.SkipTest(f"Tcl 不可用，跳过文案自适应测试：{exc}") from exc
            try:
                app.app.withdraw()
                self.assertIsNotNone(app.full_search_btn)
                self.assertIsNotNone(app.mvp_search_btn)

                app._apply_adaptive_button_texts(1100)
                self.assertEqual(app.full_search_btn.cget("text"), "全量遍历")  # type: ignore[union-attr]
                self.assertEqual(app.mvp_search_btn.cget("text"), "MVP导出")  # type: ignore[union-attr]

                app._apply_adaptive_button_texts(1800)
                self.assertEqual(app.full_search_btn.cget("text"), "全量遍历（弹窗）")  # type: ignore[union-attr]
                self.assertEqual(app.mvp_search_btn.cget("text"), "MVP搜索导出")  # type: ignore[union-attr]
            finally:
                app.app.destroy()


if __name__ == "__main__":
    unittest.main()
