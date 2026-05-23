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

from gui_design.enhancement_controls import (
    apply_preset_to_app,
    build_preset_from_app,
    get_app_calculation_history,
    place_enhancement_section,
    record_calculation_history,
    refresh_damage_snapshot,
    show_calculation_history_dialog,
    show_damage_dashboard_dialog,
    show_preset_compare_dialog,
)
from gui_design.loadout_preset import export_preset_json
from tests.gui_fixtures import (
    build_mock_app,
    ctk_available,
    destroy_mock_app_root,
    load_character_by_name,
)

pytestmark = pytest.mark.integration


@unittest.skipUnless(ctk_available(), "需要可用的 CustomTkinter / Tcl")
class TestEnhancementIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        import customtkinter as ctk

        cls._root = ctk.CTk()
        cls._root.withdraw()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._root.destroy()

    def setUp(self) -> None:
        self.app = build_mock_app(root=self._root)

    def tearDown(self) -> None:
        destroy_mock_app_root(self.app)

    def test_build_preset_from_app_roundtrip_fields(self) -> None:
        preset = build_preset_from_app(self.app)
        self.assertEqual(preset.char_name, "秋栗")
        self.assertEqual(preset.weapon_name, "坚城铸造者")
        self.assertEqual(preset.skill_levels[0], 1)

    def test_record_and_restore_history(self) -> None:
        record_calculation_history(self.app, summary="集成测试")
        history = get_app_calculation_history(self.app)
        self.assertEqual(len(history.list_entries()), 1)
        snap = history.get_snapshot(0)
        self.assertIsNotNone(snap)
        assert snap is not None
        self.assertEqual(snap["char_name"], "秋栗")

    def test_refresh_damage_snapshot_stores_on_app(self) -> None:
        refresh_damage_snapshot(self.app)
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
        preset_dict = json.loads(export_preset_json(build_preset_from_app(self.app)))
        preset_dict["char_name"] = "陈千语"
        apply_preset_to_app(self.app, LoadoutPreset.from_dict(preset_dict))
        self.assertEqual(self.app.char_panel.get_selected_data()["名称"], "陈千语")
        self.assertGreater(self.app._schedule_confirm_calls, 0)

    def test_place_enhancement_section_adds_buttons(self) -> None:
        import customtkinter as ctk

        parent = ctk.CTkFrame(self.app.app)
        buttons: list[str] = []

        def place_fn(frame, row, widget, **kwargs):
            if isinstance(widget, ctk.CTkButton):
                buttons.append(widget.cget("text"))
            widget.grid(row=row, column=0)
            return row + 1

        place_enhancement_section(self.app, parent, start_row=0, place_fn=place_fn)
        self.assertIn("多方案对比", buttons)
        self.assertIn("伤害仪表盘", buttons)

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
                            show_damage_dashboard_dialog(self.app)
        mock_mb.showinfo.assert_not_called()

    @patch("gui_design.enhancement_controls.filedialog.askopenfilenames", return_value=())
    def test_preset_compare_cancelled_on_empty_paths(self, _mock_fd: MagicMock) -> None:
        show_preset_compare_dialog(self.app)

    def test_preset_compare_with_two_json_files(self) -> None:
        preset_a = build_preset_from_app(self.app)
        preset_b = build_preset_from_app(self.app)
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
                            show_preset_compare_dialog(self.app)

    def test_history_dialog_empty(self) -> None:
        with patch("gui_design.enhancement_controls.ctk.CTkToplevel") as mock_top:
            dialog = MagicMock()
            mock_top.return_value = dialog
            with patch("gui_design.enhancement_controls.ctk.CTkScrollableFrame"):
                with patch("gui_design.enhancement_controls.ctk.CTkLabel") as mock_label:
                    show_calculation_history_dialog(self.app)
                    mock_label.assert_called()


if __name__ == "__main__":
    unittest.main()
