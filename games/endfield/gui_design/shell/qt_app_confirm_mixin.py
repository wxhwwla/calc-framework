# SPDX-License-Identifier: AGPL-3.0
"""确认计算/求值 ComputeSheet 相关回调(ConfirmMixin,混合入 QtDamageApp)。"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QMessageBox, QScrollArea, QVBoxLayout

from games.endfield.framework_bridge import ComputeSheet
from gui_design.app.loadout_evaluation import refresh_damage_snapshot, sync_evaluation_cache
from gui_design.shared.calc_history import HistoryEntry, get_app_calculation_history


class ConfirmMixin:
    """确认计算、ComputeSheet 刷新、总伤面板、快照。"""

    def _build_request(self) -> Any:
        from gui_design.app.display_request import DisplayRequest
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
            enemy_defense=self._enemy_defense,
            enemy_resistance=self._enemy_resistance,
            ignore_resistance=self._ignore_resistance,
            imbalance_vulnerability_coeff=self._imbalance_vulnerability_coeff,
            is_unbalanced=self._is_unbalanced,
            enemy_tier=self._enemy_tier,
            combo_stacks=self._combo_stacks,
            attached_effect_multiplier=self._attached_effect_multiplier,
            corrosion_duration_seconds=self._corrosion_duration_seconds,
            imbalance_efficiency_bonus=self._imbalance_efficiency_bonus,
        )
        if loadout is None:
            return None
        return DisplayRequest(loadout=loadout, equipment_catalog={}, preview_weapon_candidates=())

    def _apply_enemy_params(self, params: dict) -> None:
        self._enemy_defense = float(params.get("enemy_defense", 100.0))
        self._enemy_resistance = float(params.get("enemy_resistance", 0.0))
        self._ignore_resistance = float(params.get("ignore_resistance", 0.0))
        self._imbalance_vulnerability_coeff = float(params.get("imbalance_vulnerability_coeff", 1.3))
        self._is_unbalanced = bool(params.get("is_unbalanced", False))
        self._enemy_tier = str(params.get("enemy_tier", "普通"))
        self._combo_stacks = max(0, min(4, int(params.get("combo_stacks", 0))))
        self._attached_effect_multiplier = float(params.get("attached_effect_multiplier", 1.0))
        self._corrosion_duration_seconds = float(params.get("corrosion_duration_seconds", 15.0))
        self._imbalance_efficiency_bonus = float(params.get("imbalance_efficiency_bonus", 0.0))

    def _on_enemy_params_changed(self, params: dict) -> None:
        self._apply_enemy_params(params)

    def _on_confirm(self) -> None:
        if getattr(self, "_confirm_in_progress", False):
            return
        char_data = self.char_panel.get_selected_data()
        weapon_data = self.weapon_panel.get_selected_data()
        if not char_data or not weapon_data:
            QMessageBox.warning(self.app, "无法计算", "请选择有效的角色和武器。")
            return
        request = self._build_request()
        if request is None:
            QMessageBox.warning(self.app, "无法计算", "无法读取配装数据。")
            return
        self._confirm_in_progress = True
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.setText("计算中...")
        self.status_label.setText("计算中...")
        QApplication.processEvents()
        try:
            self._sync_evaluation(request)
            self.columns.refresh(request)
            self._refresh_compute_sheet()
            try:
                preset = request.loadout.to_loadout_preset()
                label = f"{preset.char_name} / {preset.weapon_name}"
                get_app_calculation_history(self).push(
                    HistoryEntry(label=label, summary=label, preset_snapshot=preset.to_dict())
                )
            except Exception as exc:
                self._qt_logger.warning("历史记录失败: %s", exc)
            try:
                refresh_damage_snapshot(self, loadout=request.loadout)
            except Exception as exc:
                self._qt_logger.warning("快照刷新失败: %s", exc)
            self._update_total_damage_panel()
        finally:
            self._confirm_in_progress = False
        self.status_label.setText("就绪")
        self.confirm_btn.setEnabled(True)
        self.confirm_btn.setText("确认选择")
        self.confirm_btn.setStyleSheet(self._confirm_btn_default_style)
        self._refresh_search_estimate()

    def _sync_evaluation(self, request: Any) -> None:
        sync_evaluation_cache(request)

    def _refresh_compute_sheet(self) -> None:
        from gui_design.shell.qt_app import _ensure_adapter

        _pkg, layout = _ensure_adapter()
        compute_sheet = ComputeSheet(layout)
        self._populate_sheet(compute_sheet)
        html = compute_sheet.render_html()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        label = QLabel(html)
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setWordWrap(True)
        scroll.setWidget(label)
        layout_outer = QVBoxLayout()
        layout_outer.addWidget(scroll)
        if hasattr(self, "_compute_sheet_widget") and self._compute_sheet_widget is not None:
            self._compute_sheet_widget.setLayout(layout_outer)

    def _populate_sheet(self, sheet: ComputeSheet) -> None:
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
            enemy_tier=self._enemy_tier,
            combo_stacks=self._combo_stacks,
            attached_effect_multiplier=self._attached_effect_multiplier,
            corrosion_duration_seconds=self._corrosion_duration_seconds,
            imbalance_efficiency_bonus=self._imbalance_efficiency_bonus,
        )
        if loadout is None:
            return
        for key, value in loadout.to_compute_sheet_inputs().items():
            sheet.set(key, value)

    def _update_total_damage_panel(self) -> None:
        """更新总伤面板（从 evaluation cache 读取）。"""
        from gui_design.app.loadout_evaluation import compute_total_damage
        from gui_design.presentation.display.character import build_total_damage_report_lines


        total = compute_total_damage()
        if total is None:
            return
        lines = build_total_damage_report_lines(total)
        text = "\n".join(lines)
        if hasattr(self, "_total_damage_label") and self._total_damage_label is not None:
            self._total_damage_label.setText(text)

    def _refresh_search_estimate(self) -> None:
        dock = self.control_dock
        if dock.estimate_output_label is None or not hasattr(self, "_search_estimated_total_seconds"):
            dock.estimate_output_label.setText("")
            return
        secs = getattr(self, "_search_estimated_total_seconds", 0)
        if secs > 0:
            mins = secs / 60
            if mins >= 60:
                dock.estimate_output_label.setText(f"{mins/60:.1f}h")
            elif mins >= 1:
                dock.estimate_output_label.setText(f"{mins:.0f}min")
            else:
                dock.estimate_output_label.setText(f"{secs:.0f}s")
        else:
            dock.estimate_output_label.setText("N/A")
