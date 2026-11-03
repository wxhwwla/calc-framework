#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""QtControlDock 垂直切片测试：信号、回调、读取器与固定配装槽。"""

from __future__ import annotations

import unittest

from games.endfield.gui.shared.i18n_combos import FIXED_SLOT_NONE_LABEL
from games.endfield.gui.shell.qt_control_dock import QtControlDock
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

_CATALOG: dict[str, list[dict]] = {
    "chest": [{"名称": "测试胸甲"}],
    "gloves": [{"名称": "测试手套"}],
    "accessories": [{"名称": "测试饰品A"}, {"名称": "测试饰品B"}],
}


class TestQtControlDockVerticalSlice(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not QApplication.instance():
            cls._app = QApplication([])
        cls._font = QFont()

    def _dock(self, **kwargs) -> QtControlDock:
        return QtControlDock(big_font=self._font, small_font=self._font, **kwargs)

    # ── 计算模式 ──────────────────────────────

    def test_default_calc_mode_is_zone_snapshot(self) -> None:
        dock = self._dock()

        self.assertEqual(dock.current_calc_mode(), "zone_snapshot")

    def test_calc_mode_change_emits_internal_mode_id(self) -> None:
        dock = self._dock()
        emitted: list[str] = []
        dock.calc_mode_changed.connect(emitted.append)

        idx = dock.calc_mode_menu.findData("single_hit")
        self.assertGreaterEqual(idx, 0)
        dock.calc_mode_menu.setCurrentIndex(idx)

        self.assertEqual(emitted, ["single_hit"])
        self.assertEqual(dock.current_calc_mode(), "single_hit")

    # ── 操作回调 ──────────────────────────────

    def test_action_buttons_invoke_callbacks(self) -> None:
        calls: list[str] = []
        dock = self._dock(
            on_back_to_main=lambda: calls.append("back"),
            on_confirm=lambda: calls.append("confirm"),
            on_attribution=lambda: calls.append("attribution"),
            on_donation=lambda: calls.append("donation"),
            on_open_help=lambda: calls.append("help"),
            on_search_history=lambda: calls.append("history"),
            on_ocr_detect=lambda: calls.append("ocr"),
        )

        dock.back_to_main_btn.click()
        dock.confirm_btn.click()
        dock.attribution_btn.click()
        dock.donation_btn.click()
        dock.help_btn.click()
        dock.search_history_btn.click()
        dock._ocr_btn.click()

        self.assertEqual(calls, ["back", "confirm", "attribution", "donation", "help", "history", "ocr"])

    def test_more_settings_toggle_shows_body(self) -> None:
        dock = self._dock()

        self.assertFalse(dock._more_settings_body.isVisibleTo(dock))
        dock._more_settings_btn.click()

        self.assertTrue(dock._more_settings_body.isVisibleTo(dock))

    def test_tool_buttons_exist_in_more_settings(self) -> None:
        dock = self._dock()

        for name in ("_export_btn", "_import_btn", "_compare_btn", "_dashboard_btn", "_history_btn", "_export_log_btn"):
            self.assertIsNotNone(getattr(dock, name), name)

    # ── 待确认信号 ────────────────────────────

    def test_scope_change_emits_loadout_pending(self) -> None:
        dock = self._dock()
        emitted: list[bool] = []
        dock.loadout_pending.connect(lambda: emitted.append(True))

        dock.single_skill_scope_combo.setCurrentIndex(1)
        dock.equipment_scope_combo.setCurrentIndex(1)

        self.assertEqual(len(emitted), 2)

    def test_scope_readers_return_internal_values(self) -> None:
        dock = self._dock()

        self.assertEqual(dock.current_weapon_scope_label(), "当前武器")
        self.assertEqual(dock.current_equipment_scope_label(), "全部装备")

    # ── 搜索参数 ──────────────────────────────

    def test_workers_and_top_n_readers(self) -> None:
        dock = self._dock()

        self.assertEqual(dock.read_workers_choice(), dock.search_workers_combo.currentText())
        self.assertEqual(dock.read_top_n_choice(), "10")

    def test_workers_hint_mentions_selected_count(self) -> None:
        dock = self._dock()
        numeric_labels = [dock.search_workers_combo.itemText(i) for i in range(dock.search_workers_combo.count())]
        numeric_labels = [label for label in numeric_labels if label.isdigit()]
        self.assertTrue(numeric_labels)

        dock.search_workers_combo.setCurrentText(numeric_labels[0])

        self.assertIn(numeric_labels[0], dock.search_workers_hint_label.text())

    # ── 固定配装槽 ────────────────────────────

    def test_populate_slots_fills_names(self) -> None:
        dock = self._dock()

        dock.populate_fixed_loadout_slots(_CATALOG)

        self.assertEqual(dock.fixed_loadout_slots[0].count(), 2)
        self.assertEqual(dock.fixed_loadout_slots[1].count(), 2)
        self.assertEqual(dock.fixed_loadout_slots[2].count(), 3)
        self.assertEqual(dock.fixed_loadout_slots[3].count(), 3)
        self.assertEqual(dock.fixed_loadout_slots[0].currentData(), FIXED_SLOT_NONE_LABEL)

    def test_populate_slots_preserves_selection(self) -> None:
        dock = self._dock()
        dock.populate_fixed_loadout_slots(_CATALOG)
        dock.fixed_loadout_slots[0].setCurrentText("测试胸甲")

        dock.populate_fixed_loadout_slots(_CATALOG)

        self.assertEqual(dock.fixed_loadout_slots[0].currentText(), "测试胸甲")

    def test_populate_slots_preserves_item_data_selection(self) -> None:
        dock = self._dock()
        dock.populate_fixed_loadout_slots(_CATALOG)
        cb = dock.fixed_loadout_slots[0]
        cb.setItemData(0, "测试胸甲")

        dock.populate_fixed_loadout_slots(_CATALOG)

        self.assertEqual(cb.currentText(), "测试胸甲")

    def test_populate_slots_resets_unknown_name_to_none(self) -> None:
        dock = self._dock()
        dock.populate_fixed_loadout_slots(_CATALOG)
        dock.fixed_loadout_slots[0].setCurrentText("测试胸甲")

        dock.populate_fixed_loadout_slots({"chest": [{"名称": "另一件胸甲"}]})

        self.assertEqual(dock.fixed_loadout_slots[0].currentData(), FIXED_SLOT_NONE_LABEL)

    def test_read_selection_matches_catalog_rows(self) -> None:
        dock = self._dock()
        dock.populate_fixed_loadout_slots(_CATALOG)
        dock.fixed_loadout_slots[0].setCurrentText("测试胸甲")
        dock.fixed_loadout_slots[2].setCurrentText("测试饰品B")

        selection = dock.read_fixed_loadout_selection(_CATALOG)

        self.assertIs(selection.chest, _CATALOG["chest"][0])
        self.assertIsNone(selection.gloves)
        self.assertIs(selection.accessory_a, _CATALOG["accessories"][1])
        self.assertIsNone(selection.accessory_b)

    def test_read_selection_unknown_name_returns_none(self) -> None:
        dock = self._dock()

        dock.fixed_loadout_slots[0].setCurrentText("不存在")

        selection = dock.read_fixed_loadout_selection(_CATALOG)

        self.assertIsNone(selection.chest)

    # ── 段级次数 ──────────────────────────────

    def test_read_skill_counts_keeps_positive_values(self) -> None:
        dock = self._dock()
        edits = dock._segment_count_edits_dict
        self.assertEqual(list(edits), ["战技", "连携技", "终结技"])
        edits["战技"].setText("3")
        edits["连携技"].setText("0")
        edits["终结技"].setText("abc")

        self.assertEqual(dock.read_skill_counts(), {"战技": 3})

    def test_read_skill_counts_ignores_negative(self) -> None:
        dock = self._dock()
        dock._segment_count_edits_dict["战技"].setText("-2")

        self.assertEqual(dock.read_skill_counts(), {})

    def test_rebuild_segment_rows_falls_back_without_char_data(self) -> None:
        dock = self._dock()

        dock.rebuild_segment_rows(None, 1, 0, 0)

        self.assertEqual(list(dock._segment_count_edits_dict), ["战技", "连携技", "终结技"])

    def test_rebuild_segment_rows_falls_back_when_specs_empty(self) -> None:
        dock = self._dock()

        dock.rebuild_segment_rows({}, 0, 0, 0)

        self.assertEqual(list(dock._segment_count_edits_dict), ["战技", "连携技", "终结技"])

    # ── 异常矩阵 ──────────────────────────────

    def test_physical_abnormal_counts_use_type_and_ui_level(self) -> None:
        dock = self._dock()
        spec = dock._physical_abnormal_specs[0]
        dock._physical_abnormal_edits[spec.abnormal_key][0].setText("2")

        self.assertEqual(dock.read_physical_abnormal_counts(), {f"{spec.abnormal_key}:0": 2})

    def test_spell_abnormal_counts_use_type_and_ui_level(self) -> None:
        dock = self._dock()
        spec = dock._spell_abnormal_specs[0]
        dock._spell_abnormal_edits[spec.abnormal_key][1].setText("4")

        self.assertEqual(dock.read_spell_abnormal_counts(), {f"{spec.abnormal_key}:1": 4})

    def test_clear_abnormal_counts_resets_enabled_edits_and_marks_pending(self) -> None:
        dock = self._dock()
        phys = dock._physical_abnormal_specs[0]
        spell = dock._spell_abnormal_specs[0]
        phys_edit = dock._physical_abnormal_edits[phys.abnormal_key][0]
        spell_edit = dock._spell_abnormal_edits[spell.abnormal_key][0]
        phys_edit.setText("2")
        spell_edit.setText("1")
        emitted: list[bool] = []
        dock.loadout_pending.connect(lambda: emitted.append(True))

        dock._clear_abnormal_counts()

        self.assertEqual(phys_edit.text(), "0")
        self.assertEqual(spell_edit.text(), "0")
        self.assertEqual(emitted, [True])
        self.assertEqual(dock.read_physical_abnormal_counts(), {})
        self.assertEqual(dock.read_spell_abnormal_counts(), {})

    # ── 伤害口径 / 暴击微调 ────────────────────

    def test_damage_component_mode_reader(self) -> None:
        dock = self._dock()

        self.assertEqual(dock.read_damage_component_mode(), "skill_only")
        idx = dock.damage_component_combo.findData("skill_and_abnormal")
        self.assertGreaterEqual(idx, 0)
        dock.damage_component_combo.setCurrentIndex(idx)
        self.assertEqual(dock.read_damage_component_mode(), "skill_and_abnormal")

    def test_extra_crit_readers_parse_floats(self) -> None:
        dock = self._dock()
        dock.extra_crit_rate_edit.setText("12.5")
        dock.extra_crit_damage_edit.setText("50")

        self.assertEqual(dock.read_extra_crit_rate(), 12.5)
        self.assertEqual(dock.read_extra_crit_damage(), 50.0)

    def test_extra_crit_readers_fall_back_to_zero(self) -> None:
        dock = self._dock()
        dock.extra_crit_rate_edit.setText("abc")
        dock.extra_crit_damage_edit.setText("abc")

        self.assertEqual(dock.read_extra_crit_rate(), 0.0)
        self.assertEqual(dock.read_extra_crit_damage(), 0.0)


if __name__ == "__main__":
    unittest.main()
