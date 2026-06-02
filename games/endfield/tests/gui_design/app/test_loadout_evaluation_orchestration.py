#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""Loadout 求值编排层测试。"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QApplication


class TestSyncEvaluationCache(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not QApplication.instance():
            cls._app = QApplication([])

    def setUp(self) -> None:
        self.loadout = MagicMock()
        self.loadout.char_data = {"名称": "陈千语"}
        self.loadout.weapon_data = {"名称": "显锋"}
        self.loadout.char_level = 90
        self.loadout.weapon_level = 90
        self.loadout.trust_level = 4
        self.loadout.skill_levels = (10, 8, 6)
        self.loadout.calculation_mode = "single_skill_search"
        self.loadout.weapon_scope_label = "所有单手剑"
        self.loadout.equipment_scope_label = "所有装备"
        self.loadout.manual_counts = {}
        self.loadout.use_manual_multi_skill_counts = False
        self.loadout.physical_abnormal_counts = {}
        self.loadout.spell_abnormal_counts = {}
        self.loadout.damage_component_mode = "final"
        self.loadout.use_expected_crit = True
        self.loadout.include_conditional_equipment_crit = False
        self.loadout.extra_crit_rate = 0.0
        self.loadout.extra_crit_damage = 0.0
        self.loadout.enemy_defense = 100.0
        self.loadout.enemy_resistance = 0.0
        self.loadout.ignore_resistance = 0.0
        self.loadout.imbalance_vulnerability_coeff = 1.0
        self.loadout.is_unbalanced = False
        self.loadout.manual_buffs = None
        self.loadout.weapon_skill_kwargs.return_value = {}

    @patch("games.endfield.gui.app.loadout_evaluation.sync_confirm_dependencies")
    def test_sync_evaluation_cache(self, mock_sync) -> None:
        from games.endfield.gui.app.loadout_evaluation import sync_evaluation_cache

        sync_evaluation_cache(self.loadout)

        mock_sync.assert_called_once_with(
            char_data=self.loadout.char_data,
            weapon_data=self.loadout.weapon_data,
            char_level=self.loadout.char_level,
            weapon_level=self.loadout.weapon_level,
            trust_level=self.loadout.trust_level,
            skill_levels=self.loadout.skill_levels,
            calculation_mode=self.loadout.calculation_mode,
            weapon_scope=self.loadout.weapon_scope_label,
            equipment_scope=self.loadout.equipment_scope_label,
            multi_skill_counts=self.loadout.manual_counts,
            use_manual_multi_skill_counts=self.loadout.use_manual_multi_skill_counts,
            physical_abnormal_counts=self.loadout.physical_abnormal_counts,
            spell_abnormal_counts=self.loadout.spell_abnormal_counts,
            damage_component_mode=self.loadout.damage_component_mode,
            use_expected_crit=self.loadout.use_expected_crit,
            include_conditional_equipment_crit=self.loadout.include_conditional_equipment_crit,
            extra_crit_rate=self.loadout.extra_crit_rate,
            extra_crit_damage=self.loadout.extra_crit_damage,
            enemy_defense=self.loadout.enemy_defense,
        )

    @patch("games.endfield.gui.app.loadout_evaluation.sync_confirm_dependencies")
    def test_build_search_preview_lines_multi_skill(self, mock_sync) -> None:
        self.loadout.calculation_mode = "multi_skill_search"

        from games.endfield.gui.app.loadout_evaluation import build_search_preview_lines

        with patch(
            "games.endfield.gui.app.loadout_evaluation.build_multi_skill_search_preview_lines",
            return_value=["line1"],
        ) as mock_multi:
            result = build_search_preview_lines(self.loadout, equipment_catalog={})

        mock_multi.assert_called_once()
        self.assertEqual(result, ["line1"])

    @patch("games.endfield.gui.app.loadout_evaluation.sync_confirm_dependencies")
    def test_build_search_preview_lines_single_skill(self, mock_sync) -> None:
        from games.endfield.gui.app.loadout_evaluation import build_search_preview_lines

        with patch(
            "games.endfield.gui.app.loadout_evaluation.build_single_skill_search_preview_lines",
            return_value=["preview"],
        ) as mock_single:
            result = build_search_preview_lines(self.loadout, equipment_catalog={})

        mock_single.assert_called_once()
        self.assertEqual(result, ["preview"])

    @patch("games.endfield.gui.app.loadout_evaluation.sync_confirm_dependencies")
    def test_build_search_preview_lines_unknown_mode(self, mock_sync) -> None:
        self.loadout.calculation_mode = "unknown"

        from games.endfield.gui.app.loadout_evaluation import build_search_preview_lines

        result = build_search_preview_lines(self.loadout, equipment_catalog={})
        self.assertEqual(result, [])

    @patch("games.endfield.gui.app.loadout_evaluation.sync_confirm_dependencies")
    def test_build_snapshot_from_loadout(self, mock_sync) -> None:
        from games.endfield.gui.app.loadout_evaluation import build_snapshot_from_loadout

        with patch(
            "games.endfield.gui.app.loadout_evaluation.build_damage_snapshot",
            return_value={"snapshot": "data"},
        ) as mock_snap:
            result = build_snapshot_from_loadout(self.loadout)

        mock_snap.assert_called_once()
        self.assertEqual(result, {"snapshot": "data"})

    @patch("games.endfield.gui.app.loadout_evaluation.sync_confirm_dependencies")
    def test_refresh_damage_snapshot_with_loadout(self, mock_sync) -> None:
        from games.endfield.gui.app.loadout_evaluation import refresh_damage_snapshot

        mock_app = MagicMock()

        with patch(
            "games.endfield.gui.app.loadout_evaluation.build_snapshot_from_loadout",
            return_value={"snapshot": "fresh"},
        ) as mock_build:
            with patch(
                "games.endfield.gui.app.loadout_evaluation.store_snapshot_on_app",
            ) as mock_store:
                refresh_damage_snapshot(mock_app, loadout=self.loadout)

        mock_build.assert_called_once_with(self.loadout)
        mock_store.assert_called_once_with(mock_app, {"snapshot": "fresh"})


if __name__ == "__main__":
    unittest.main()
