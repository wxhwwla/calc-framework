"""对话框/预设/工具回调(DialogMixin,混合入 QtDamageApp)。"""

from __future__ import annotations

import webbrowser
from pathlib import Path
from typing import Any

from PySide6.QtWidgets import QFileDialog, QMessageBox

from gui_design.legal.attribution_content import SUMMARY_TEXT
from gui_design.legal.donation_qt import open_donation_dialog


class DialogMixin:
    """手动 Buff、预设导入导出、方案对比、仪表盘、历史、捐赠等。"""

    def _on_manual_buff(self) -> None:
        from gui_design.controls.manual_buff.qt_window import QtManualBuffDialog

        def _read_counts():
            dock = self.control_dock
            return dock.read_skill_counts(), dock.read_physical_abnormal_counts(), dock.read_spell_abnormal_counts()

        dialog = QtManualBuffDialog(
            self.app, big_font=self.big_font, small_font=self.small_font,
            read_counts_callback=_read_counts,
        )
        dialog.exec()

    def _on_export_preset(self) -> None:
        from gui_design.app.loadout_preset import export_preset_json
        from gui_design.app.loadout_state import read_loadout_from_panels

        dock = self.control_dock
        loadout = read_loadout_from_panels(
            self.char_panel, self.weapon_panel,
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
            enemy_defense=self._enemy_defense, enemy_resistance=self._enemy_resistance,
            ignore_resistance=self._ignore_resistance,
            imbalance_vulnerability_coeff=self._imbalance_vulnerability_coeff,
            is_unbalanced=self._is_unbalanced,
        )
        if loadout is None:
            QMessageBox.warning(self.app, "导出预设", "无法读取配装数据。")
            return
        preset = loadout.to_loadout_preset()
        path, _ = QFileDialog.getSaveFileName(self.app, "导出配装预设", "preset.json", "JSON (*.json)")
        if not path:
            return
        Path(path).write_text(export_preset_json(preset), encoding="utf-8")
        self.status_label.setText("预设已导出")

    def _on_import_preset(self) -> None:
        from gui_design.app.loadout_preset import import_presets_from_json_text

        path, _ = QFileDialog.getOpenFileName(self.app, "导入配装预设", "", "JSON (*.json)")
        if not path:
            return
        try:
            text = Path(path).read_text(encoding="utf-8")
            preset = import_presets_from_json_text(text)
            self._apply_preset_to_qt_app(preset)
            self.status_label.setText("预设已导入")
        except Exception as exc:
            QMessageBox.warning(self.app, "导入预设失败", str(exc))

    def _apply_preset_to_qt_app(self, preset) -> None:
        from gui_design.app.loadout_preset import apply_preset_to_panels

        apply_preset_to_panels(
            preset=preset,
            char_panel=self.char_panel,
            weapon_panel=self.weapon_panel,
            control_dock=self.control_dock,
            enemy_defense=self._enemy_defense,
            equipment_catalog=self._equipment_catalog,
        )

    def _on_compare_presets(self) -> None:
        from gui_design.controls.enhancement.qt_dialogs import QtCompareDialog

        dialog = QtCompareDialog(
            parent=self.app, big_font=self.big_font, small_font=self.small_font,
            char_panel=self.char_panel, weapon_panel=self.weapon_panel,
        )
        dialog.exec()

    def _on_dashboard(self) -> None:
        from gui_design.controls.enhancement.qt_dialogs import QtDamageDashboard

        dialog = QtDamageDashboard(
            parent=self.app, big_font=self.big_font, small_font=self.small_font,
        )
        dialog.exec()

    def _on_history(self) -> None:
        from gui_design.shared.calc_history import QtCalculationHistoryDialog

        dialog = QtCalculationHistoryDialog(
            parent=self.app, big_font=self.big_font, small_font=self.small_font,
        )
        dialog.exec()

    def _on_attribution(self) -> None:
        QMessageBox.about(self.app, "数据来源与声明", SUMMARY_TEXT)

    def _on_donation(self) -> None:
        open_donation_dialog(self.app)

    def _on_github(self) -> None:
        webbrowser.open("https://github.com/your-repo/endfield-damage-calculator")
