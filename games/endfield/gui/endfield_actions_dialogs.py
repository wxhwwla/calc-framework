# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""ActionsDialogsMixin — 终末地主窗口的对话框、预设与工具方法。

从 ``endfield_actions.py`` 按符号边界拆出，保持
``ActionsMixin`` 的公共方法集合不变（P2-07 结构债清理）。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from calc_framework.ui.i18n import tr
from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget

from games.endfield.gui.app.loadout_state import read_loadout_from_panels
from games.endfield.gui.legal.attribution_content import SUMMARY_TEXT
from games.endfield.gui.legal.donation_qt import open_donation_dialog
from games.endfield.gui.presentation.damage_snapshot import get_snapshot_from_app
from games.endfield.gui.shared.calc_history import get_app_calculation_history


class ActionsDialogsMixin:
    """对话框 / 预设 / 工具操作混合类。

    由 ``ActionsMixin`` 继承，提供手动 buff、生存估算、预设导入导出、
    对比、历史、帮助与 OCR 等界面动作。
    """

    def _on_manual_buff(self) -> None:
        from games.endfield.gui.controls.manual_buff.qt_window import QtManualBuffDialog

        def _read_counts():
            dock = self.control_dock
            return dock.read_skill_counts(), dock.read_physical_abnormal_counts(), dock.read_spell_abnormal_counts()

        dialog = QtManualBuffDialog(
            cast(QWidget, self),
            big_font=self.big_font,
            small_font=self.small_font,
            read_counts_callback=_read_counts,
        )
        if not hasattr(self, "_manual_buff_store"):
            self._manual_buff_store = {}
        dialog.load_store(getattr(self, "_manual_buff_store", None))
        if dialog.exec():
            self._manual_buff_store = dialog.buff_store()

    def _on_survival_estimate(self) -> None:
        from games.endfield.gui.controls.survival import open_survival_estimate_dialog

        dock = self.control_dock
        loadout = read_loadout_from_panels(
            self.char_panel,
            self.weapon_panel,
            calculation_mode=self._current_calc_mode,
            weapon_scope_label=dock.single_skill_scope_combo.currentText(),
            equipment_scope_label=dock.equipment_scope_combo.currentText(),
            fixed_loadout=dock.read_fixed_loadout_selection(self._equipment_catalog),
            use_manual_multi_skill_counts=dock.use_manual_skill_counts_cb.isChecked(),
            manual_counts=dock.read_skill_counts(),
            physical_abnormal_counts=dock.read_physical_abnormal_counts(),
            spell_abnormal_counts=dock.read_spell_abnormal_counts(),
            damage_component_mode=dock.read_damage_component_mode(),
            use_expected_crit=dock.use_expected_crit_cb.isChecked(),
            include_conditional_equipment_crit=dock.include_conditional_crit_cb.isChecked(),
            extra_crit_rate=dock.read_extra_crit_rate(),
            extra_crit_damage=dock.read_extra_crit_damage(),
            enemy_defense=self._enemy_defense,
            enemy_resistance=self._enemy_resistance,
            ignore_resistance=self._ignore_resistance,
            imbalance_vulnerability_coeff=self._imbalance_vulnerability_coeff,
            is_unbalanced=self._is_unbalanced,
            is_true_damage=self._is_true_damage,
        )
        if loadout is None:
            QMessageBox.warning(
                cast(QWidget, self),
                tr("desktop.endfield.survivalEstimate"),
                tr("desktop.endfield.survivalNeedCharWeapon"),
            )
            return
        from games.endfield.data_loading.enemy_params import resolve_enemy_max_hp

        enemy_id = dock._enemy_panel.current_enemy_id()
        open_survival_estimate_dialog(
            self,
            char_data=loadout.char_data,
            weapon_data=loadout.weapon_data,
            char_level=loadout.char_level,
            weapon_level=loadout.weapon_level,
            trust_level=loadout.trust_level,
            enemy_tier=self._enemy_tier,
            imbalance_efficiency_bonus=self._imbalance_efficiency_bonus,
            enemy_max_hp=resolve_enemy_max_hp(enemy_id),
            weapon_skill_kwargs=loadout.weapon_skill_kwargs(),
            big_font=self.big_font,
        )

    def _on_export_preset(self) -> None:
        from games.endfield.gui.app.loadout_preset import export_preset_json

        dock = self.control_dock
        loadout = read_loadout_from_panels(
            self.char_panel,
            self.weapon_panel,
            calculation_mode=self._current_calc_mode,
            weapon_scope_label=dock.single_skill_scope_combo.currentText(),
            equipment_scope_label=dock.equipment_scope_combo.currentText(),
            fixed_loadout=dock.read_fixed_loadout_selection(self._equipment_catalog),
            use_manual_multi_skill_counts=dock.use_manual_skill_counts_cb.isChecked(),
            manual_counts=dock.read_skill_counts(),
            physical_abnormal_counts=dock.read_physical_abnormal_counts(),
            spell_abnormal_counts=dock.read_spell_abnormal_counts(),
            damage_component_mode=dock.read_damage_component_mode(),
            use_expected_crit=dock.use_expected_crit_cb.isChecked(),
            include_conditional_equipment_crit=dock.include_conditional_crit_cb.isChecked(),
            extra_crit_rate=dock.read_extra_crit_rate(),
            extra_crit_damage=dock.read_extra_crit_damage(),
            enemy_defense=self._enemy_defense,
            enemy_resistance=self._enemy_resistance,
            ignore_resistance=self._ignore_resistance,
            imbalance_vulnerability_coeff=self._imbalance_vulnerability_coeff,
            is_unbalanced=self._is_unbalanced,
            is_true_damage=self._is_true_damage,
        )
        if loadout is None:
            QMessageBox.warning(
                cast(QWidget, self),
                tr("desktop.endfield.exportPresetTitle"),
                tr("desktop.endfield.cannotReadLoadout"),
            )
            return
        preset = loadout.to_loadout_preset()
        path, _ = QFileDialog.getSaveFileName(
            cast(QWidget, self),
            tr("desktop.endfield.exportPresetDialog"),
            "preset.json",
            "JSON (*.json)",
        )
        if not path:
            return
        Path(path).write_text(export_preset_json(preset), encoding="utf-8")
        self.status_label.setText(tr("desktop.endfield.presetExported"))

    def _on_import_preset(self) -> None:
        from games.endfield.gui.app.loadout_preset import import_presets_from_json_text

        path, _ = QFileDialog.getOpenFileName(
            cast(QWidget, self),
            tr("desktop.endfield.importPresetDialog"),
            "",
            "JSON (*.json)",
        )
        if not path:
            return
        try:
            text = Path(path).read_text(encoding="utf-8")
            preset = import_presets_from_json_text(text)
            if not preset:
                raise ValueError(tr("desktop.endfield.presetFileEmpty"))
            self._apply_preset_to_qt_app(preset[0])
            self.status_label.setText(tr("desktop.endfield.presetImported"))
        except Exception as exc:
            QMessageBox.warning(
                cast(QWidget, self),
                tr("desktop.endfield.importPresetFailed"),
                str(exc),
            )

    def _apply_preset_to_qt_app(self, preset: Any) -> None:
        from games.endfield.gui.app.loadout_preset import apply_preset_to_panels

        apply_preset_to_panels(
            preset=preset,
            char_panel=self.char_panel,
            weapon_panel=self.weapon_panel,
            control_dock=self.control_dock,
            equipment_catalog=self._equipment_catalog,
            shell=self,
        )

    def _on_compare_presets(self) -> None:
        from games.endfield.gui.controls.enhancement.qt_dialogs import QtCompareDialog

        dialog = QtCompareDialog(
            parent=self,
            big_font=self.big_font,
            small_font=self.small_font,
            char_panel=self.char_panel,
            weapon_panel=self.weapon_panel,
        )
        dialog.exec()

    def _on_attribution(self) -> None:
        QMessageBox.about(
            cast(QWidget, self),
            tr("desktop.endfield.attributionAboutTitle"),
            SUMMARY_TEXT,
        )

    def _on_donation(self) -> None:
        open_donation_dialog(cast(QWidget, self))

    def _on_damage_dashboard(self) -> None:
        from games.endfield.gui.controls.enhancement.qt_dialogs import QtDamageDashboardDialog

        snapshot = get_snapshot_from_app(self)
        dialog = QtDamageDashboardDialog(
            cast(QWidget, self),
            big_font=self.big_font,
            small_font=self.small_font,
            snapshot=snapshot,
        )
        dialog.exec()

    def _on_calc_history(self) -> None:
        from games.endfield.gui.controls.enhancement.qt_dialogs import QtCalcHistoryDialog

        history = get_app_calculation_history(self)
        dialog = QtCalcHistoryDialog(
            cast(QWidget, self),
            big_font=self.big_font,
            small_font=self.small_font,
            history=history,
            apply_fn=self._apply_preset_to_qt_app,
        )
        dialog.exec()

    def _on_export_log(self) -> None:
        from utils.operation_log import get_session_operation_log

        path, _ = QFileDialog.getSaveFileName(
            cast(QWidget, self),
            tr("desktop.endfield.exportOpLog"),
            "operation_log.json",
            "JSON (*.json)",
        )
        if not path:
            return
        try:
            get_session_operation_log().export_to_file(Path(path))
            self.status_label.setText(tr("desktop.endfield.opLogExported"))
        except Exception as exc:
            QMessageBox.warning(
                cast(QWidget, self),
                tr("desktop.endfield.exportFailedTitle"),
                str(exc),
            )

    def _on_open_help(self) -> None:
        from utils.gui.help_calculator import build_calculator_help
        from utils.gui.help_dialog import HelpDialog

        dialog = HelpDialog(
            build_calculator_help,
            cast(QWidget, self),
            title=tr("desktop.endfield.helpCalculatorTitle"),
        )
        dialog.exec()

    def _on_ocr_detect(self) -> None:
        try:
            from games.endfield.gui.controls.ocr import open_ocr_detection_dialog

            def _apply_ocr(preset_dict: dict[str, Any]) -> None:
                char_name = preset_dict.get("char_name", "")
                weapon_name = preset_dict.get("weapon_name", "")
                char_level = int(preset_dict.get("char_level", 1))
                weapon_level = int(preset_dict.get("weapon_level", 1))
                trust_level = int(preset_dict.get("trust_level", 0))

                if char_name:
                    ok = self.char_panel.select_by_name(char_name)
                    if ok and weapon_name:
                        self.weapon_panel.select_by_name(weapon_name)
                    self.char_panel.level_slider.setValue(char_level)
                    self.weapon_panel.level_slider.setValue(weapon_level)
                    if trust_level and self.char_panel.trust_panel:
                        self.char_panel.trust_panel.set_level(min(trust_level, 4))
                    self._on_confirm()

            open_ocr_detection_dialog(cast(QWidget, self), on_apply=_apply_ocr)
        except Exception as exc:
            msg = tr("desktop.endfield.ocrLoadFailedMsg", error=str(exc))
            QMessageBox.warning(cast(QWidget, self), tr("desktop.endfield.ocrDetect"), msg)
