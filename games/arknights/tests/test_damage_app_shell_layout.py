# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""明日方舟主窗口统一外壳：顶部工具条 + 2×2 页 + 底部确认/页签。"""

from __future__ import annotations

import unittest

from PySide6.QtWidgets import QApplication, QDoubleSpinBox, QSpinBox


class TestArknightsShellLayout(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not QApplication.instance():
            cls._qapp = QApplication([])

        from games.arknights.gui.ArknightsDamageApp import ArknightsDamageApp

        cls.window = ArknightsDamageApp(embedded=True)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.window.close()
        cls.window.deleteLater()

    def test_bottom_tabs_replace_standalone_calculate_button(self) -> None:
        self.assertEqual(self.window._shell.tab_texts(), ["计算", "乘区明细"])
        self.assertFalse(hasattr(self.window, "_calc_btn"))

    def test_toolbar_carries_non_calculation_entries(self) -> None:
        texts = [action.text() for action in self.window._shell.toolbar.actions() if action.text()]

        self.assertTrue(any("使用说明" in text for text in texts))
        self.assertTrue(any("捐赠" in text for text in texts))

    def test_confirm_button_lives_in_bottom_bar(self) -> None:
        self.assertIs(self.window.confirm_btn, self.window._shell.confirm_button)
        self.assertIs(self.window.status_label, self.window._shell.status_label)

    def test_calc_page_uses_four_zones(self) -> None:
        page = self.window._calc_page

        self.assertTrue(page.zone("top_left").isAncestorOf(self.window._op_combo))
        self.assertTrue(page.zone("top_right").isAncestorOf(self.window._skill_combo))
        self.assertTrue(page.zone("top_right").isAncestorOf(self.window._lvl_slider))
        self.assertTrue(page.zone("bottom_left").isAncestorOf(self.window._det_stat_tbl))
        self.assertTrue(page.zone("bottom_right").isAncestorOf(self.window._bonus_table))

    def test_breakdown_page_uses_four_zones(self) -> None:
        page = self.window._breakdown_page

        self.assertTrue(page.zone("top_left").isAncestorOf(self.window._enemy_section_widget))
        self.assertTrue(page.zone("top_right").isAncestorOf(self.window._extra_bonus_widget))
        self.assertTrue(page.zone("bottom_left").isAncestorOf(self.window._result_table))
        self.assertTrue(page.zone("bottom_right").isAncestorOf(self.window._result_cards["atk"]))

    def test_selection_marks_pending_without_touching_result_panels(self) -> None:
        self.window._bonus_table.setRowCount(0)
        self.window._on_op_selected(self.window._op_combo.currentText())

        self.assertIn("待更新", self.window._shell.confirm_button.text())
        self.assertEqual(self.window._shell.status_text(), "待确认")
        self.assertEqual(self.window._bonus_table.rowCount(), 0)

    def test_confirm_refreshes_data_panels(self) -> None:
        self.window._on_compute()

        self.assertGreater(self.window._det_stat_tbl.rowCount(), 0)
        self.assertGreater(self.window._bonus_table.rowCount(), 0)
        self.assertGreater(self.window._result_table.rowCount(), 0)
        self.assertNotEqual(self.window._result_cards["atk"].text(), "—")
        self.assertEqual(self.window._shell.status_text(), "已确认")

    def test_breakdown_enemy_zone_exposes_editable_inputs(self) -> None:
        enemy_zone = self.window._breakdown_page.zone("top_left")
        spins = enemy_zone.findChildren(QDoubleSpinBox) + enemy_zone.findChildren(QSpinBox)

        self.assertGreaterEqual(len(spins), 4)
        for path in (
            "user_input.敌人防御",
            "user_input.敌人法术抗性",
            "user_input.物理穿透",
            "user_input.法术穿透",
            "user_input.信赖攻击",
            "user_input.潜能攻击",
        ):
            self.assertIn(path, self.window._param_sheet._input_widgets)

    def test_enemy_defense_input_changes_confirmed_damage(self) -> None:
        from games.arknights.gui.arknights_compute_sheet import set_user_input_value

        set_user_input_value(self.window._param_sheet, "user_input.敌人防御", 200.0)
        self.window._on_compute()
        before = self.window._result_cards["phys"].text()

        set_user_input_value(self.window._param_sheet, "user_input.敌人防御", 0.0)
        self.window._on_compute()
        after = self.window._result_cards["phys"].text()

        self.assertNotEqual(before, after)

    def test_user_vars_have_chinese_descriptions(self) -> None:
        from games.arknights.gui.arknights_sheet_config import ARKNIGHTS_USER_VARS

        for path, spec in ARKNIGHTS_USER_VARS.items():
            description = spec.get("description", "")
            self.assertTrue(description, f"{path} 缺少 description")
            self.assertTrue(
                any("一" <= char <= "鿿" for char in description),
                f"{path} 的 description 不是中文：{description}",
            )


if __name__ == "__main__":
    unittest.main()
