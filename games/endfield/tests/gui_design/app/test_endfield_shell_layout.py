# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""终末地主窗口统一外壳：顶部工具条 + 2×2 页 + 底部确认/页签。"""

from __future__ import annotations

import unittest

from PySide6.QtWidgets import QApplication


class TestEndfieldShellLayout(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not QApplication.instance():
            cls._qapp = QApplication([])

        from games.endfield.gui.endfield_app import EndfieldApp

        cls.window = EndfieldApp()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.window.close()
        cls.window.deleteLater()

    def test_bottom_tabs_replace_top_tab_widget(self) -> None:
        self.assertEqual(self.window._shell.tab_texts(), ["计算", "高级"])
        self.assertFalse(hasattr(self.window, "tabs"))

    def test_toolbar_carries_non_calculation_entries(self) -> None:
        texts = [action.text() for action in self.window._shell.toolbar.actions() if action.text()]

        self.assertTrue(any("使用说明" in text for text in texts))
        self.assertTrue(any("捐赠" in text for text in texts))
        self.assertTrue(any("数据来源" in text for text in texts))

    def test_confirm_button_lives_in_bottom_bar(self) -> None:
        self.assertIs(self.window.confirm_btn, self.window._shell.confirm_button)
        self.assertIs(self.window.status_label, self.window._shell.status_label)

    def test_calc_page_uses_four_zones(self) -> None:
        page = self.window._calc_page

        self.assertTrue(page.zone("top_left").isAncestorOf(self.window.char_panel))
        self.assertTrue(page.zone("top_right").isAncestorOf(self.window.weapon_panel))
        self.assertTrue(page.zone("bottom_left").isAncestorOf(self.window.columns.char_table))
        self.assertTrue(page.zone("bottom_right").isAncestorOf(self.window.columns.weapon_table))

    def test_advanced_page_uses_four_zones(self) -> None:
        page = self.window._adv_page

        self.assertTrue(page.zone("top_left").isAncestorOf(self.window.control_dock._enemy_panel))
        self.assertTrue(page.zone("top_right").isAncestorOf(self.window.control_dock._col_multi))
        self.assertTrue(page.zone("bottom_left").isAncestorOf(self.window.columns.zone_table))
        self.assertTrue(page.zone("bottom_right").isAncestorOf(self.window._total_damage_panel))

    def test_pending_state_is_rendered_in_shell(self) -> None:
        self.window._on_loadout_changed()

        self.assertEqual(self.window._shell.confirm_button.text(), "确认选择（待更新）")
        self.assertEqual(self.window._shell.status_text(), "待确认")


if __name__ == "__main__":
    unittest.main()
