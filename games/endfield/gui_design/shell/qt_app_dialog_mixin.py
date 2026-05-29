"""对话框/预设/工具/信号回调（DialogMixin，混合入 QtDamageApp）。"""

from __future__ import annotations

import webbrowser
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, QThread
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from gui_design.legal.attribution_content import SUMMARY_TEXT
from gui_design.legal.donation_qt import open_donation_dialog


class DialogMixin:
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

    def _on_attribution(self) -> None:
        QMessageBox.about(self.app, "数据来源与声明", SUMMARY_TEXT)

    def _on_donation(self) -> None:
        open_donation_dialog(self.app)

    # ── 信号连接 ──────────────────────────────

    def _connect_signals(self) -> None:
        self.char_panel.name_combo.currentTextChanged.connect(self._on_char_name_change)

        for panel in (self.char_panel, self.weapon_panel):
            panel.type_combo.currentIndexChanged.connect(self._on_loadout_changed)
            panel.star_combo.currentIndexChanged.connect(self._on_loadout_changed)
            panel.name_combo.currentIndexChanged.connect(self._on_loadout_changed)
            panel.level_slider.valueChanged.connect(self._on_loadout_changed)

        self.control_dock.calc_mode_changed.connect(self._on_calc_mode_changed)

        self.control_dock.mvp_search_btn.clicked.connect(self._on_mvp_search)
        self.control_dock.full_search_btn.clicked.connect(self._on_full_search)
        self.control_dock.search_cancel_btn.clicked.connect(self._on_cancel_search)
        self._connect_more_settings_btns()
        self._connect_search_estimate_triggers()

    def _connect_more_settings_btns(self) -> None:
        dock = self.control_dock
        if hasattr(dock, "_export_btn") and dock._export_btn:
            dock._export_btn.clicked.connect(self._on_export_preset)
        if hasattr(dock, "_import_btn") and dock._import_btn:
            dock._import_btn.clicked.connect(self._on_import_preset)
        if hasattr(dock, "_compare_btn") and dock._compare_btn:
            dock._compare_btn.clicked.connect(self._on_compare_presets)
        if hasattr(dock, "_dashboard_btn") and dock._dashboard_btn:
            dock._dashboard_btn.clicked.connect(self._on_damage_dashboard)
        if hasattr(dock, "_history_btn") and dock._history_btn:
            dock._history_btn.clicked.connect(self._on_calc_history)
        if hasattr(dock, "_export_log_btn") and dock._export_log_btn:
            dock._export_log_btn.clicked.connect(self._on_export_log)

    def _connect_search_estimate_triggers(self) -> None:
        dock = self.control_dock
        dock.single_skill_scope_combo.currentTextChanged.connect(self._refresh_search_estimate)
        dock.equipment_scope_combo.currentTextChanged.connect(self._refresh_search_estimate)
        dock.search_workers_combo.currentTextChanged.connect(self._refresh_search_estimate)
        dock.search_top_n_combo.currentTextChanged.connect(self._refresh_search_estimate)

    # ── 伤害仪表盘 / 计算历史 / 操作日志 ──────────

    def _on_damage_dashboard(self) -> None:
        from gui_design.controls.enhancement.qt_dialogs import QtDamageDashboardDialog
        from gui_design.presentation.damage_snapshot import get_snapshot_from_app

        snapshot = get_snapshot_from_app(self)
        dialog = QtDamageDashboardDialog(
            self.app,
            big_font=self.big_font,
            small_font=self.small_font,
            snapshot=snapshot,
        )
        dialog.exec()

    def _on_calc_history(self) -> None:
        from gui_design.controls.enhancement.qt_dialogs import QtCalcHistoryDialog
        from gui_design.shared.calc_history import get_app_calculation_history

        history = get_app_calculation_history(self)
        dialog = QtCalcHistoryDialog(
            self.app,
            big_font=self.big_font,
            small_font=self.small_font,
            history=history,
            apply_fn=self._apply_preset_to_qt_app,
        )
        dialog.exec()

    def _on_export_log(self) -> None:
        from utils.operation_log import get_session_operation_log

        path, _ = QFileDialog.getSaveFileName(
            self.app, "导出操作日志", "operation_log.json", "JSON (*.json)",
        )
        if not path:
            return
        try:
            get_session_operation_log().export_to_file(Path(path))
            self.status_label.setText("操作日志已导出")
        except Exception as exc:
            QMessageBox.warning(self.app, "导出失败", str(exc))

    def _on_open_help(self) -> None:
        import webbrowser

        doc_path = Path(__file__).resolve().parents[4] / "docs" / "GUI使用说明.md"
        if doc_path.is_file():
            webbrowser.open(doc_path.as_uri())
        else:
            QMessageBox.warning(self.app, "找不到文档", f"使用说明文件不存在：\n{doc_path}")

    def _on_ocr_detect(self) -> None:
        """打开截图识装检测对话框。"""
        try:
            from gui_design.controls.ocr import open_ocr_detection_dialog

            def _apply_ocr(preset_dict: dict) -> None:
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

            open_ocr_detection_dialog(self.app, on_apply=_apply_ocr)
        except Exception as exc:
            QMessageBox.warning(self.app, "截图识装", f"无法加载 OCR 模块：\n{exc}\n\n请安装: pip install ultralytics easyocr")
