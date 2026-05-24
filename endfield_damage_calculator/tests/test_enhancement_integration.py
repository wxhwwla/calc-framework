#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""增强功能 GUI 集成测试（模拟 app + 可选 CTk）。"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from gui_design.loadout_preset import export_preset_json
from tests.gui_fixtures import (
    build_mock_app,
    ctk_available,
    destroy_mock_app_root,
    load_character_by_name,
)

pytestmark = pytest.mark.integration


class TestEnhancementIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not ctk_available():
            raise unittest.SkipTest("需要可用的 CustomTkinter / Tcl")
        import customtkinter as ctk

        cls._root = ctk.CTk()
        cls._root.withdraw()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._root.destroy()

    def setUp(self) -> None:
        from gui_design import enhancement_controls as ec

        self._ec = ec
        self.app = build_mock_app(root=self._root)

    def tearDown(self) -> None:
        destroy_mock_app_root(self.app)

    def test_build_preset_from_app_roundtrip_fields(self) -> None:
        self.app.char_panel._show_advanced_params_var.set(True)
        self.app.weapon_panel._show_advanced_params_var.set(False)
        self.app._show_more_settings_var.set(True)
        self.app.page_tabs.set("高级页")
        preset = self._ec.build_preset_from_app(self.app)
        self.assertEqual(preset.char_name, "秋栗")
        self.assertEqual(preset.weapon_name, "坚城铸造者")
        self.assertEqual(preset.skill_levels[0], 1)
        self.assertTrue(bool((preset.ui_state or {}).get("char_advanced_expanded")))
        self.assertFalse(bool((preset.ui_state or {}).get("weapon_advanced_expanded")))
        self.assertTrue(bool((preset.ui_state or {}).get("more_settings_expanded")))
        self.assertEqual((preset.ui_state or {}).get("current_page"), "高级页")

    def test_record_and_restore_history(self) -> None:
        self._ec.record_calculation_history(self.app, summary="集成测试")
        history = self._ec.get_app_calculation_history(self.app)
        self.assertEqual(len(history.list_entries()), 1)
        snap = history.get_snapshot(0)
        self.assertIsNotNone(snap)
        assert snap is not None
        self.assertEqual(snap["char_name"], "秋栗")

    def test_refresh_damage_snapshot_stores_on_app(self) -> None:
        self._ec.refresh_damage_snapshot(self.app)
        self.assertIsNotNone(getattr(self.app, "_last_damage_snapshot", None))
        self.assertGreater(self.app._last_damage_snapshot.weighted_total_damage, 0)

    def test_apply_preset_updates_vars(self) -> None:
        from gui_design.loadout_preset import LoadoutPreset
        from tests.gui_fixtures import MockSelectionPanel

        chen = load_character_by_name("陈千语")
        weapon = self.app.weapon_panel.get_selected_data()
        assert weapon is not None
        self.app.char_panel = MockSelectionPanel(
            self.app.char_panel.get_selected_data() or {},
            skills=(1, 0, 0),
        )
        self.app.char_panel.list_c_w = [self.app.char_panel._data, chen]
        preset_dict = json.loads(export_preset_json(self._ec.build_preset_from_app(self.app)))
        preset_dict["char_name"] = "陈千语"
        preset_dict["ui_state"] = {
            "char_advanced_expanded": True,
            "weapon_advanced_expanded": True,
            "more_settings_expanded": True,
            "current_page": "高级页",
        }
        self._ec.apply_preset_to_app(self.app, LoadoutPreset.from_dict(preset_dict))
        self.assertEqual(self.app.char_panel.get_selected_data()["名称"], "陈千语")
        self.assertTrue(bool(self.app.char_panel._show_advanced_params_var.get()))
        self.assertTrue(bool(self.app.weapon_panel._show_advanced_params_var.get()))
        self.assertTrue(bool(self.app._show_more_settings_var.get()))
        self.assertEqual(self.app.page_tabs.get(), "高级页")
        self.assertGreater(self.app._schedule_confirm_calls, 0)

    def test_place_enhancement_section_collapsible_more_settings(self) -> None:
        import customtkinter as ctk

        parent = ctk.CTkFrame(self.app.app)

        def place_fn(frame, row, widget, **kwargs):
            widget.grid(row=row, column=0)
            return row + 1

        self._ec.place_enhancement_section(self.app, parent, start_row=0, place_fn=place_fn)
        self.assertIsNotNone(getattr(self.app, "_more_settings_toggle_btn", None))
        self.assertIsNotNone(getattr(self.app, "_more_settings_body", None))

        toggle_btn = self.app._more_settings_toggle_btn
        body = self.app._more_settings_body
        self.assertFalse(bool(self.app._show_more_settings_var.get()))
        self.assertIn("展开", toggle_btn.cget("text"))

        toggle_btn.invoke()
        self.assertTrue(bool(self.app._show_more_settings_var.get()))
        self.assertIn("收起", toggle_btn.cget("text"))

        labels = [
            child.cget("text")
            for child in body.winfo_children()
            if isinstance(child, ctk.CTkButton)
        ]
        self.assertIn("多方案对比", labels)
        self.assertIn("伤害仪表盘", labels)

    def test_more_settings_state_persists_after_rebuild(self) -> None:
        import customtkinter as ctk

        parent_1 = ctk.CTkFrame(self.app.app)
        parent_2 = ctk.CTkFrame(self.app.app)

        def place_fn(frame, row, widget, **kwargs):
            widget.grid(row=row, column=0)
            return row + 1

        self._ec.place_enhancement_section(self.app, parent_1, start_row=0, place_fn=place_fn)
        self.app._more_settings_toggle_btn.invoke()
        self.assertTrue(bool(self.app._show_more_settings_var.get()))
        self.assertIn("收起", self.app._more_settings_toggle_btn.cget("text"))

        self._ec.place_enhancement_section(self.app, parent_2, start_row=0, place_fn=place_fn)
        self.assertTrue(bool(self.app._show_more_settings_var.get()))
        self.assertIn("收起", self.app._more_settings_toggle_btn.cget("text"))

    def test_more_settings_contains_group_titles(self) -> None:
        import customtkinter as ctk

        parent = ctk.CTkFrame(self.app.app)

        def place_fn(frame, row, widget, **kwargs):
            widget.grid(row=row, column=0)
            return row + 1

        self._ec.place_enhancement_section(self.app, parent, start_row=0, place_fn=place_fn)
        self.app._more_settings_toggle_btn.invoke()
        body = self.app._more_settings_body
        titles = [
            child.cget("text")
            for child in body.winfo_children()
            if isinstance(child, ctk.CTkLabel)
        ]
        self.assertIn("导入导出", titles)
        self.assertIn("分析工具", titles)

    def test_startup_page_mode_selector_updates_preferences(self) -> None:
        import customtkinter as ctk

        parent = ctk.CTkFrame(self.app.app)

        def place_fn(frame, row, widget, **kwargs):
            widget.grid(row=row, column=0)
            return row + 1

        with patch("gui_design.enhancement_controls.save_ui_preferences") as mock_save:
            self._ec.place_enhancement_section(self.app, parent, start_row=0, place_fn=place_fn)
            self.app._more_settings_toggle_btn.invoke()
            self.assertIsNotNone(getattr(self.app, "_startup_page_mode_menu", None))
            self.assertIsNotNone(getattr(self.app, "_on_startup_page_mode_change", None))
            self.assertIsNotNone(getattr(self.app, "_startup_page_mode_hint_label", None))
            self.assertIn(
                "下次启动",
                self.app._startup_page_mode_hint_label.cget("text"),
            )

            self.app._on_startup_page_mode_change("启动记住上次页面")
            self.assertEqual(
                self.app._ui_preferences.get("startup_page_mode"),
                "remember_last",
            )
            mock_save.assert_called()

    @patch("gui_design.enhancement_controls.messagebox")
    def test_dashboard_without_snapshot_refreshes(self, mock_mb: MagicMock) -> None:
        with patch("gui_design.enhancement_controls.is_matplotlib_available", return_value=True):
            with patch("matplotlib.use"):
                with patch(
                    "gui_design.enhancement_controls.build_damage_pie_figure",
                    return_value=MagicMock(),
                ):
                    with patch(
                        "gui_design.enhancement_controls.build_improvement_bar_figure",
                        return_value=MagicMock(),
                    ):
                        with patch(
                            "matplotlib.backends.backend_tkagg.FigureCanvasTkAgg",
                            MagicMock(),
                        ):
                            self._ec.show_damage_dashboard_dialog(self.app)
        mock_mb.showinfo.assert_not_called()

    @patch("gui_design.enhancement_controls.filedialog.askopenfilenames", return_value=())
    def test_preset_compare_cancelled_on_empty_paths(self, _mock_fd: MagicMock) -> None:
        self._ec.show_preset_compare_dialog(self.app)

    def test_preset_compare_with_two_json_files(self) -> None:
        preset_a = self._ec.build_preset_from_app(self.app)
        preset_b = self._ec.build_preset_from_app(self.app)
        preset_b_dict = json.loads(export_preset_json(preset_b))
        preset_b_dict["note"] = "方案B"
        from gui_design.loadout_preset import LoadoutPreset

        preset_b = LoadoutPreset.from_dict(preset_b_dict)
        with tempfile.TemporaryDirectory() as tmp:
            p1 = Path(tmp) / "a.json"
            p2 = Path(tmp) / "b.json"
            p1.write_text(export_preset_json(preset_a), encoding="utf-8")
            p2.write_text(export_preset_json(preset_b), encoding="utf-8")
            with patch(
                "gui_design.enhancement_controls.filedialog.askopenfilenames",
                return_value=(str(p1), str(p2)),
            ):
                with patch("gui_design.enhancement_controls.ctk.CTkToplevel") as mock_top:
                    mock_top.return_value = MagicMock()
                    with patch("gui_design.enhancement_controls.ctk.CTkScrollableFrame"):
                        with patch("gui_design.enhancement_controls.ctk.CTkLabel"):
                            self._ec.show_preset_compare_dialog(self.app)

    def test_history_dialog_empty(self) -> None:
        with patch("gui_design.enhancement_controls.ctk.CTkToplevel") as mock_top:
            dialog = MagicMock()
            mock_top.return_value = dialog
            with patch("gui_design.enhancement_controls.ctk.CTkScrollableFrame"):
                with patch("gui_design.enhancement_controls.ctk.CTkLabel") as mock_label:
                    self._ec.show_calculation_history_dialog(self.app)
                    mock_label.assert_called()


if __name__ == "__main__":
    unittest.main()
