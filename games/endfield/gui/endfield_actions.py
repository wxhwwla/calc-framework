# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""ActionsMixin — 终末地伤害计算主窗口事件处理与计算。

对话框/预设/工具方法见 ``ActionsDialogsMixin``（P2-07 拆分）。
P2 迁移目标：所有面板最终使用 ComputeSheet + layout.json。
"""

from __future__ import annotations

from typing import Any, cast

from calc_framework.ui.i18n import tr
from PySide6.QtWidgets import (
    QApplication,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)
from utils.path_utils import get_resource_path

from games.endfield.data_loading.web_loadout_bridge import build_adapter_context_from_loadout
from games.endfield.framework_bridge import AdapterPackage, ComputeSheet, Layout, get_logger, load_layout_json
from games.endfield.gui.app.compute_sheet_variables import (
    ENDFIELD_USER_CONTEXT_OVERRIDES,
    ENDFIELD_USER_INPUT_VARIABLES,
    apply_endfield_sheet_context,
)
from games.endfield.gui.app.loadout_evaluation import (
    refresh_damage_snapshot,
)
from games.endfield.gui.app.loadout_evaluation import (
    sync_evaluation_cache as _sync_eval_cache,
)
from games.endfield.gui.app.loadout_state import read_loadout_from_panels
from games.endfield.gui.endfield_actions_dialogs import ActionsDialogsMixin
from games.endfield.gui.presentation.damage_snapshot import get_snapshot_from_app
from games.endfield.gui.shared.calc_history import HistoryEntry, get_app_calculation_history

_FRAMEWORK_ADAPTER = get_resource_path("framework/adapters/endfield")

_adapter_pkg: AdapterPackage | None = None
_adapter_layout: Layout | None = None

_logger = get_logger("gui.endfield_actions")


def _ensure_adapter() -> tuple[AdapterPackage, Layout]:
    """确保适配器包和布局已加载（惰性初始化）。"""
    global _adapter_pkg, _adapter_layout
    if _adapter_pkg is None:
        _adapter_pkg = AdapterPackage(str(_FRAMEWORK_ADAPTER))
        layout_path = _FRAMEWORK_ADAPTER / "ui" / "layout.json"
        _adapter_layout = load_layout_json(layout_path.read_text(encoding="utf-8"))
    assert _adapter_pkg is not None and _adapter_layout is not None
    return _adapter_pkg, _adapter_layout


class ActionsMixin(ActionsDialogsMixin):
    """事件处理与计算混合类（非搜索部分）。

    提供敌方参数管理、确认计算、ComputeSheet 集成及信号连接；
    对话框/预设/工具方法由 ActionsDialogsMixin 提供。
    搜索相关方法见 ActionsSearchMixin。
    由 EndfieldApp 继承使用。"""

    # ── 敌方参数 ──────────────────────────────────

    def _apply_enemy_params(self, params: dict[str, Any]) -> None:
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

    def _on_enemy_params_changed(self, params: dict[str, Any]) -> None:
        self._apply_enemy_params(params)

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
            break_defense_stacks=self._break_defense_stacks,
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
            QMessageBox.warning(
                cast(QWidget, self),
                tr("desktop.endfield.cannotComputeTitle"),
                tr("desktop.endfield.needValidCharWeapon"),
            )
            return
        request = self._build_request()
        if request is None:
            QMessageBox.warning(
                cast(QWidget, self),
                tr("desktop.endfield.cannotComputeTitle"),
                tr("desktop.endfield.cannotReadLoadout"),
            )
            return
        self._confirm_in_progress = True
        self._set_confirm_ui_computing()
        QApplication.processEvents()
        try:
            self._sync_evaluation(request)
            self.columns.refresh(request)
            # 先恢复按钮：ComputeSheet 求值若卡住不应一直停在「计算中」
            self._set_confirm_ui_confirmed()
            QApplication.processEvents()
            compute_sheet_error: Exception | None = None
            try:
                self._refresh_compute_sheet(request.loadout)
            except Exception as exc:
                # 乘区表是文档声明的核心输出：失败必须可见，不能只写日志
                compute_sheet_error = exc
                _logger.exception("乘区表刷新失败: %s", exc)
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
            if compute_sheet_error is not None:
                self._set_confirm_ui_pending()
                QMessageBox.warning(
                    cast(QWidget, self),
                    tr("desktop.endfield.confirmFailedTitle"),
                    tr("desktop.endfield.confirmFailedMsg", error=str(compute_sheet_error)),
                )
        except Exception as exc:
            _logger.exception("确认选择失败: %s", exc)
            QMessageBox.warning(
                cast(QWidget, self),
                tr("desktop.endfield.confirmFailedTitle"),
                tr("desktop.endfield.confirmFailedMsg", error=str(exc)),
            )
            self._set_confirm_ui_pending()
        finally:
            self._confirm_in_progress = False
            try:
                self._refresh_search_estimate()
            except Exception as exc:
                _logger.warning("搜索预估刷新失败: %s", exc)

    def _sync_evaluation(self, request: Any) -> None:
        try:
            _sync_eval_cache(request.loadout)
        except Exception as exc:
            _logger.warning("求值缓存同步失败: %s", exc)

    def _refresh_compute_sheet(self, loadout: Any | None = None) -> None:
        """用已确认的配装刷新乘区表。

        Args:
            loadout: 本次确认的配装快照；缺省时重新读取面板（兼容旧调用）。
        """
        if loadout is None:
            request = self._build_request()
            if request is None:
                raise RuntimeError("无法读取当前配装")
            loadout = request.loadout

        pkg, layout = _ensure_adapter()
        dag_service = pkg.dag_service

        variables: dict[str, Any] = dict(dag_service.dag.variables)
        variables.update(ENDFIELD_USER_INPUT_VARIABLES)

        base_context = build_adapter_context_from_loadout(
            loadout,
            equipment_catalog=getattr(self, "_equipment_catalog", None),
        )
        base_context.setdefault("user_input", {})["敌人等阶"] = getattr(loadout, "enemy_tier", "普通")
        # enrich_adapter_context 已把额外暴击叠加进 character；这里先移除，
        # 由输入控件统一叠加一次，避免刷新时重复计算。
        character = base_context.setdefault("character", {})
        character["暴击率"] = float(character.get("暴击率", 0.05)) - float(
            getattr(loadout, "extra_crit_rate", 0.0) or 0.0
        )
        character["暴击伤害"] = float(character.get("暴击伤害", 0.5)) - float(
            getattr(loadout, "extra_crit_damage", 0.0) or 0.0
        )

        def _transform(context: dict[str, Any], user_values: dict[str, Any]) -> dict[str, Any]:
            return apply_endfield_sheet_context(
                context,
                user_values,
                skill_type=str(getattr(loadout, "skill_type", "") or ""),
                use_expected_crit=bool(getattr(loadout, "use_expected_crit", False)),
            )

        assert layout is not None
        compute_sheet = ComputeSheet(
            dag_service,
            layout,
            variables,
            base_context=base_context,
            user_context_overrides=ENDFIELD_USER_CONTEXT_OVERRIDES,
            context_transform=_transform,
        )
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

    def _on_compute_sheet_evaluated(self, _result: Any = None) -> None:
        self._update_total_damage_panel()

    def _update_total_damage_panel(self) -> None:
        snapshot = get_snapshot_from_app(self)
        self._total_damage_panel.update_from_snapshot(snapshot)

    # ── 信号连接 ──────────────────────────────

    def _connect_panel_extra_loadout_signals(self, panel: Any) -> None:
        """信赖/技能/武器特殊能力变更时也标记待确认。"""
        if panel.trust_panel is not None:
            panel.trust_panel._slider.valueChanged.connect(self._on_loadout_changed)
        if panel.skill_panel is not None:
            for slider in panel.skill_panel._sliders:
                slider.valueChanged.connect(self._on_loadout_changed)
        if panel.special_panel is not None:
            for rd in panel.special_panel._normal_rows:
                rd["slider"].valueChanged.connect(self._on_loadout_changed)
            for rd in panel.special_panel._special_rows:
                rd["lvl_slider"].valueChanged.connect(self._on_loadout_changed)
                rd["stk_slider"].valueChanged.connect(self._on_loadout_changed)

    def _connect_signals(self) -> None:
        self.char_panel.name_combo.currentTextChanged.connect(self._on_char_name_change)

        for panel in (self.char_panel, self.weapon_panel):
            panel.type_combo.currentIndexChanged.connect(self._on_loadout_changed)
            panel.star_combo.currentIndexChanged.connect(self._on_loadout_changed)
            panel.name_combo.currentIndexChanged.connect(self._on_loadout_changed)
            panel.level_slider.valueChanged.connect(self._on_loadout_changed)

        self._connect_panel_extra_loadout_signals(self.char_panel)
        self._connect_panel_extra_loadout_signals(self.weapon_panel)

        self.control_dock.calc_mode_changed.connect(self._on_calc_mode_changed)
        self.control_dock.loadout_pending.connect(self._on_loadout_changed)

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
