# SPDX-License-Identifier: AGPL-3.0
"""ActionsMixin — 终末地伤害计算主窗口事件处理、计算、搜索与对话框。

P2 迁移目标：所有面板最终使用 ComputeSheet + layout.json。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from games.endfield.framework_bridge import AdapterPackage, ComputeSheet, get_logger, load_layout_json
from games.endfield.gui.app.loadout_evaluation import (
    refresh_damage_snapshot,
)
from games.endfield.gui.app.loadout_evaluation import (
    sync_evaluation_cache as _sync_eval_cache,
)
from games.endfield.gui.app.loadout_state import read_loadout_from_panels
from games.endfield.gui.legal.attribution_content import SUMMARY_TEXT
from games.endfield.gui.legal.donation_qt import open_donation_dialog
from games.endfield.gui.presentation.damage_snapshot import get_snapshot_from_app
from games.endfield.gui.shared.calc_history import HistoryEntry, get_app_calculation_history

_CUR_FILE = Path(__file__).resolve()
_FRAMEWORK_ADAPTER = _CUR_FILE.parents[4] / "framework" / "adapters" / "endfield"

_adapter_pkg: AdapterPackage | None = None
_adapter_layout = None

_logger = get_logger("gui.endfield_actions")


def _ensure_adapter():
    global _adapter_pkg, _adapter_layout
    if _adapter_pkg is None:
        _adapter_pkg = AdapterPackage(str(_FRAMEWORK_ADAPTER))
        layout_path = _FRAMEWORK_ADAPTER / "ui" / "layout.json"
        _adapter_layout = load_layout_json(layout_path.read_text(encoding="utf-8"))
    """ensure adapter。"""
    return _adapter_pkg, _adapter_layout


class ActionsMixin:
    """事件处理与计算混合类（非搜索部分）。

    提供敌方参数管理、确认计算、ComputeSheet 集成、
    对话框处理（预设、手动 buff、生存估算、帮助等）及信号连接。
    搜索相关方法见 ActionsSearchMixin。
    由 EndfieldApp 继承使用。"""

    # ── 敌方参数 ──────────────────────────────────

    def _apply_enemy_params(self, params: dict) -> None:
        self._enemy_defense = float(params.get("enemy_defense", 100.0))
        self._enemy_resistance = float(params.get("enemy_resistance", 0.0))
        self._ignore_resistance = float(params.get("ignore_resistance", 0.0))
        self._imbalance_vulnerability_coeff = float(params.get("imbalance_vulnerability_coeff", 1.3))
        self._is_unbalanced = bool(params.get("is_unbalanced", False))
        self._is_true_damage = bool(params.get("is_true_damage", False))
        self._enemy_tier = str(params.get("enemy_tier", "普通"))
        self._combo_stacks = max(0, min(4, int(params.get("combo_stacks", 0))))
        self._attached_effect_multiplier = float(params.get("attached_effect_multiplier", 1.0))
        self._corrosion_duration_seconds = float(params.get("corrosion_duration_seconds", 15.0))
        self._imbalance_efficiency_bonus = float(params.get("imbalance_efficiency_bonus", 0.0))
        self._break_defense_stacks = max(0, min(4, int(params.get("break_defense_stacks", 0))))
        """apply enemy params。"""

    def _on_enemy_params_changed(self, params: dict) -> None:
        self._apply_enemy_params(params)
        """on enemy params changed。"""

    # ── 确认计算 / ComputeSheet ──────────────────

    def _build_request(self) -> Any:
        from games.endfield.gui.app.display_request import DisplayRequest

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
            enemy_tier=self._enemy_tier,
            combo_stacks=self._combo_stacks,
            attached_effect_multiplier=self._attached_effect_multiplier,
            corrosion_duration_seconds=self._corrosion_duration_seconds,
            imbalance_efficiency_bonus=self._imbalance_efficiency_bonus,
        )
        if loadout is None:
            return None
        return DisplayRequest(loadout=loadout, equipment_catalog={}, preview_weapon_candidates=())

    def _on_confirm(self) -> None:
        if getattr(self, "_confirm_in_progress", False):
            return
        char_data = self.char_panel.get_selected_data()
        weapon_data = self.weapon_panel.get_selected_data()
        if not char_data or not weapon_data:
            QMessageBox.warning(cast(QWidget, self), "无法计算", "请选择有效的角色和武器。")
            return
        request = self._build_request()
        if request is None:
            QMessageBox.warning(cast(QWidget, self), "无法计算", "无法读取配装数据。")
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
                _logger.warning("历史记录失败: %s", exc)
            try:
                refresh_damage_snapshot(self, loadout=request.loadout)
            except Exception as exc:
                _logger.warning("快照刷新失败: %s", exc)
            self._update_total_damage_panel()
        finally:
            self._confirm_in_progress = False
        self.status_label.setText("就绪")
        self.confirm_btn.setEnabled(True)
        self.confirm_btn.setText("确认选择")
        self.confirm_btn.setStyleSheet(self._confirm_btn_default_style)
        self._refresh_search_estimate()
        """on confirm。"""

    def _sync_evaluation(self, request: Any) -> None:
        try:
            _sync_eval_cache(request.loadout)
        except Exception as exc:
            _logger.warning("求值缓存同步失败: %s", exc)
        """sync evaluation。"""

    def _refresh_compute_sheet(self) -> None:
        pkg, layout = _ensure_adapter()
        dag_service = pkg.dag_service

        variables = dict(dag_service.dag.variables)
        user_vars: dict[str, Any] = {
            "user_input.敌人防御": {
                "source": "user_input",
                "type": "float",
                "default": 100.0,
                "min": 0,
                "max": 99999,
                "step": 10.0,
            },
            "user_input.敌人等阶": {"source": "user_input", "type": "str", "default": "普通"},
            "user_input.敌人抗性": {
                "source": "user_input",
                "type": "float",
                "default": 0.0,
                "min": -100,
                "max": 100,
                "step": 1.0,
            },
            "user_input.无视抗性": {
                "source": "user_input",
                "type": "float",
                "default": 0.0,
                "min": -100,
                "max": 100,
                "step": 1.0,
            },
            "user_input.失衡易伤系数": {
                "source": "user_input",
                "type": "float",
                "default": 1.3,
                "min": 0.1,
                "max": 10.0,
                "step": 0.05,
            },
            "user_input.是否失衡": {"source": "user_input", "type": "bool", "default": False},
            "user_input.是否真实伤害": {"source": "user_input", "type": "bool", "default": False},
            "user_input.连击层数": {"source": "user_input", "type": "int", "default": 0, "min": 0, "max": 4, "step": 1},
            "user_input.额外暴击率": {
                "source": "user_input",
                "type": "float",
                "default": 0.0,
                "min": 0,
                "max": 1.0,
                "step": 0.01,
            },
            "user_input.额外暴击伤害": {
                "source": "user_input",
                "type": "float",
                "default": 0.0,
                "min": 0,
                "max": 5.0,
                "step": 0.01,
            },
            "user_input.额外伤害加成": {
                "source": "user_input",
                "type": "float",
                "default": 0.0,
                "min": 0,
                "max": 5.0,
                "step": 0.01,
            },
            "user_input.附带效果倍率": {
                "source": "user_input",
                "type": "float",
                "default": 1.0,
                "min": 0.1,
                "max": 3.0,
                "step": 0.05,
            },
            "user_input.破防层数": {"source": "user_input", "type": "int", "default": 0, "min": 0, "max": 4, "step": 1},
            "user_input.失衡效率加成": {
                "source": "user_input",
                "type": "float",
                "default": 0.0,
                "min": 0,
                "max": 1.0,
                "step": 0.05,
            },
            "user_input.腐蚀计时(秒)": {
                "source": "user_input",
                "type": "float",
                "default": 15.0,
                "min": 0.0,
                "max": 15.0,
                "step": 0.5,
            },
        }
        variables.update(user_vars)

        user_context_overrides = {
            "user_input.敌人防御": ("enemy.防御", ["override"]),
            "user_input.敌人抗性": ("computed.抗性", ["add"]),
            "user_input.无视抗性": ("computed.无视抗性", ["override"]),
            "user_input.失衡易伤系数": ("computed.失衡易伤", ["override"]),
            "user_input.是否失衡": ("computed.失衡状态", ["override"]),
            "user_input.是否真实伤害": ("computed.真实伤害", ["override"]),
            "user_input.连击层数": ("computed.连击层数", ["override"]),
            "user_input.额外暴击率": ("character.暴击率", ["add"]),
            "user_input.额外暴击伤害": ("character.暴击伤害", ["add"]),
            "user_input.额外伤害加成": ("computed.伤害加成", ["add"]),
        }

        assert layout is not None
        compute_sheet = ComputeSheet(
            dag_service,
            layout,
            variables,
            base_context={},
            user_context_overrides=user_context_overrides,
        )
        self._populate_sheet(compute_sheet)
        compute_sheet.evaluated.connect(self._on_compute_sheet_evaluated)
        compute_sheet.evaluate()

        if self._compute_sheet_widget is not None:
            old_layout = self._compute_sheet_widget.layout()
            if old_layout is not None:
                while old_layout.count():
                    item = old_layout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()
                old_layout.deleteLater()
            new_layout = QVBoxLayout()
            new_layout.setContentsMargins(0, 0, 0, 0)
            new_layout.addWidget(compute_sheet.widget, stretch=1)
            new_layout.addWidget(self._total_damage_panel)
            self._compute_sheet_widget.setLayout(new_layout)
        """refresh compute sheet。"""

    def _populate_sheet(self, sheet: ComputeSheet) -> None:
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
        """populate sheet。"""

    def _on_compute_sheet_evaluated(self, result: Any = None) -> None:
        self._update_total_damage_panel()
        """on compute sheet evaluated。"""

    def _update_total_damage_panel(self) -> None:
        snapshot = get_snapshot_from_app(self)
        self._total_damage_panel.update_from_snapshot(snapshot)
        """update total damage panel。"""

    # ── 对话框 / 工具 / 信号 ─────────────────────

    def _on_manual_buff(self) -> None:
        from games.endfield.gui.controls.manual_buff.qt_window import QtManualBuffDialog

        def _read_counts():
            dock = self.control_dock
            """read counts。"""
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
        """on manual buff。"""

    def _on_survival_estimate(self) -> None:
        from games.endfield.gui.app.loadout_state import read_loadout_from_panels
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
            QMessageBox.warning(cast(QWidget, self), "处决/治疗估算", "请先选择角色与武器。")
            return
        from games.endfield.data_loading.enemy_params import resolve_enemy_max_hp

        dock = self.control_dock
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
        """on survival estimate。"""

    def _on_export_preset(self) -> None:
        from games.endfield.gui.app.loadout_preset import export_preset_json
        from games.endfield.gui.app.loadout_state import read_loadout_from_panels

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
            QMessageBox.warning(cast(QWidget, self), "导出预设", "无法读取配装数据。")
            return
        preset = loadout.to_loadout_preset()
        path, _ = QFileDialog.getSaveFileName(cast(QWidget, self), "导出配装预设", "preset.json", "JSON (*.json)")
        if not path:
            return
        Path(path).write_text(export_preset_json(preset), encoding="utf-8")
        self.status_label.setText("预设已导出")
        """on export preset。"""

    def _on_import_preset(self) -> None:
        from games.endfield.gui.app.loadout_preset import import_presets_from_json_text

        path, _ = QFileDialog.getOpenFileName(cast(QWidget, self), "导入配装预设", "", "JSON (*.json)")
        if not path:
            return
        try:
            text = Path(path).read_text(encoding="utf-8")
            preset = import_presets_from_json_text(text)
            if not preset:
                raise ValueError("预设文件为空")
            self._apply_preset_to_qt_app(preset[0])
            self.status_label.setText("预设已导入")
        except Exception as exc:
            QMessageBox.warning(cast(QWidget, self), "导入预设失败", str(exc))
        """on import preset。"""

    def _apply_preset_to_qt_app(self, preset) -> None:
        from games.endfield.gui.app.loadout_preset import apply_preset_to_panels

        apply_preset_to_panels(
            preset=preset,
            char_panel=self.char_panel,
            weapon_panel=self.weapon_panel,
            control_dock=self.control_dock,
            equipment_catalog=self._equipment_catalog,
            shell=self,
        )
        """apply preset to qt app。"""

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
        """on compare presets。"""

    def _on_attribution(self) -> None:
        QMessageBox.about(cast(QWidget, self), "数据来源与声明", SUMMARY_TEXT)
        """on attribution。"""

    def _on_donation(self) -> None:
        open_donation_dialog(cast(QWidget, self))
        """on donation。"""

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
        """on damage dashboard。"""

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
        """on calc history。"""

    def _on_export_log(self) -> None:
        from utils.operation_log import get_session_operation_log

        path, _ = QFileDialog.getSaveFileName(
            cast(QWidget, self), "导出操作日志", "operation_log.json", "JSON (*.json)"
        )
        if not path:
            return
        try:
            get_session_operation_log().export_to_file(Path(path))
            self.status_label.setText("操作日志已导出")
        except Exception as exc:
            QMessageBox.warning(cast(QWidget, self), "导出失败", str(exc))
        """on export log。"""

    def _on_open_help(self) -> None:
        from utils.gui.help_calculator import build_calculator_help
        from utils.gui.help_dialog import HelpDialog

        dialog = HelpDialog(build_calculator_help, cast(QWidget, self), title="终末地伤害计算器 使用说明")
        dialog.exec()
        """on open help。"""

    def _on_ocr_detect(self) -> None:
        try:
            from games.endfield.gui.controls.ocr import open_ocr_detection_dialog

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
                """apply ocr。"""

            open_ocr_detection_dialog(cast(QWidget, self), on_apply=_apply_ocr)
        except Exception as exc:
            msg = f"无法加载 OCR 模块：\n{exc}\n\n请安装: pip install torchvision easyocr"
            QMessageBox.warning(cast(QWidget, self), "截图识装", msg)
        """on ocr detect。"""

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
        """connect signals。"""

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
        """connect more settings btns。"""
