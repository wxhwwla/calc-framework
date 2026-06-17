#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""
高级页控制栏（PySide6 版）。

与 CTk 版 ``app_control_dock.py`` 平行。
三列布局：操作/乘区展示 | 全量搜索 | 多技能次数。
包含固定配装槽、异常矩阵、搜索参数、增强工具按钮。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from calc_framework.ui.i18n import tr
from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from games.endfield.calc.manual_buff.abnormal_matrix import read_abnormal_matrix_counts
from games.endfield.gui.controls.enemy import QtEnemyPanel
from games.endfield.gui.controls.search.search_settings import (
    format_parallel_workers_help,
    get_cpu_parallel_info,
    resolve_parallel_workers,
)
from games.endfield.gui.shared.calc_mode_labels import (
    calculation_mode_from_combo,
    populate_calc_mode_combo,
)
from games.endfield.gui.shared.i18n_combos import (
    FIXED_SLOT_NONE_LABEL,
    combo_internal_value,
    read_damage_component_mode,
    set_combo_by_internal,
)
from games.endfield.gui.shell.qt_control_dock_builders import (
    _BTN_PRIMARY_STYLE,
    _BTN_SECONDARY_STYLE,
    _COMBO_STYLE,
    _FIXED_SLOT_SPECS,
    _PRIMARY_BTN_HEIGHT,
    _SECONDARY_BTN_HEIGHT,
    BuilderMixin,
)
from games.endfield.gui.shell.qt_control_dock_widgets import (
    SectionHeader,
    SmallLabel,
)

# 固定配装槽位配置：(catalog_key, 界面标签)

# ═══════════════════════════════════════════════════════
#  QtControlDock
# ═══════════════════════════════════════════════════════


class QtControlDock(BuilderMixin, QWidget):
    """高级页三列控制栏。

    包含操作按钮（确认/返回/许可）、计算模式选择、全量搜索参数、
    固定配装槽、多技能次数段行、物理/法术异常矩阵、暴击微调。
    """

    calc_mode_changed = Signal(str)
    confirm_requested = Signal()
    loadout_pending = Signal()

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        big_font: QFont | None = None,
        small_font: QFont | None = None,
        on_back_to_main: Callable[[], None] | None = None,
        on_confirm: Callable[[], None] | None = None,
        on_attribution: Callable[[], None] | None = None,
        on_donation: Callable[[], None] | None = None,
        on_open_help: Callable[[], None] | None = None,
        on_ocr_detect: Callable[[], None] | None = None,
        on_search_history: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(parent)  # pyright: ignore[reportCallIssue]
        self._big = big_font or QFont()
        self._small = small_font or QFont()
        self._on_back_to_main = on_back_to_main
        self._on_confirm = on_confirm
        self._on_attribution = on_attribution
        self._on_donation = on_donation
        self._on_open_help = on_open_help
        self._on_ocr_detect = on_ocr_detect
        self._on_search_history = on_search_history

        # 暴露给外部的控件引用
        self.back_to_main_btn: QPushButton
        self.confirm_btn: QPushButton
        self.attribution_btn: QPushButton
        self.donation_btn: QPushButton
        self.help_btn: QPushButton
        self.calc_mode_menu: QComboBox
        self.single_skill_scope_combo: QComboBox
        self.equipment_scope_combo: QComboBox
        self.fixed_loadout_slots: list[QComboBox] = []
        self.use_manual_skill_counts_cb: QCheckBox
        self.damage_component_combo: QComboBox
        self.use_expected_crit_cb: QCheckBox
        self.include_conditional_crit_cb: QCheckBox
        self.extra_crit_rate_edit: QLineEdit
        self.extra_crit_damage_edit: QLineEdit

        self._build_ui()
        """初始化实例。"""

    def _make_btn(self, text: str, height: int, *, primary: bool = False, style: str | None = None) -> QPushButton:
        """创建一个统一样式的 QPushButton。"""
        btn = QPushButton(text)
        btn.setMinimumHeight(height)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn.setStyleSheet(style or (_BTN_PRIMARY_STYLE if primary else _BTN_SECONDARY_STYLE))
        return btn

    def _build_ui(self) -> None:
        """构建三列布局。"""
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(6)

        outer.addWidget(self._build_col_actions(), stretch=1)
        outer.addWidget(self._build_col_search(), stretch=2)
        outer.addWidget(self._build_col_multi(), stretch=3)

    # ── 列 1：操作 / 乘区展示 ──────────────────────

    def _build_col_actions(self) -> QWidget:
        """构建第一列：操作按钮、计算模式、更多设置。"""
        col = QWidget()
        col.setMinimumWidth(200)
        lay = QVBoxLayout(col)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(4)

        lay.addWidget(SectionHeader(tr("desktop.endfield.sectionActions"), self._big))

        self.back_to_main_btn = self._make_btn(tr("desktop.endfield.backToCalc"), _SECONDARY_BTN_HEIGHT)
        if self._on_back_to_main:
            self.back_to_main_btn.clicked.connect(self._on_back_to_main)
        lay.addWidget(self.back_to_main_btn)

        self.confirm_btn = self._make_btn(tr("desktop.endfield.confirmSelection"), _PRIMARY_BTN_HEIGHT, primary=True)
        if self._on_confirm:
            self.confirm_btn.clicked.connect(self._on_confirm)
        lay.addWidget(self.confirm_btn)

        self.attribution_btn = self._make_btn(tr("desktop.endfield.dataAttribution"), _SECONDARY_BTN_HEIGHT)
        if self._on_attribution:
            self.attribution_btn.clicked.connect(self._on_attribution)
        lay.addWidget(self.attribution_btn)

        self.donation_btn = self._make_btn(tr("desktop.endfield.donate"), _SECONDARY_BTN_HEIGHT)
        if self._on_donation:
            self.donation_btn.clicked.connect(self._on_donation)
        else:
            from utils.gui.donation import open_donation_dialog

            self.donation_btn.clicked.connect(lambda: open_donation_dialog(self))
        lay.addWidget(self.donation_btn)

        self.help_btn = self._make_btn(tr("desktop.endfield.helpUsage"), _SECONDARY_BTN_HEIGHT)
        if self._on_open_help:
            self.help_btn.clicked.connect(self._on_open_help)
        lay.addWidget(self.help_btn)

        self.search_history_btn = self._make_btn(tr("desktop.endfield.searchHistory"), _SECONDARY_BTN_HEIGHT)
        if self._on_search_history:
            self.search_history_btn.clicked.connect(self._on_search_history)
        lay.addWidget(self.search_history_btn)

        lay.addSpacing(8)
        lay.addWidget(SectionHeader(tr("desktop.endfield.sectionZones"), self._big))
        lay.addWidget(SmallLabel(tr("desktop.endfield.calcModeLabel"), self._small))

        self.calc_mode_menu = QComboBox()
        populate_calc_mode_combo(self.calc_mode_menu)
        idx = self.calc_mode_menu.findData("zone_snapshot")
        if idx >= 0:
            self.calc_mode_menu.setCurrentIndex(idx)
        self.calc_mode_menu.currentTextChanged.connect(self._on_calc_mode_changed)
        self.calc_mode_menu.setStyleSheet(_COMBO_STYLE)
        lay.addWidget(self.calc_mode_menu)

        # 增强操作区域
        lay.addSpacing(8)
        lay.addWidget(SectionHeader(tr("desktop.endfield.sectionTools"), self._big))

        self._more_settings_btn = self._make_btn(tr("desktop.endfield.moreSettingsExpand"), _SECONDARY_BTN_HEIGHT)
        self._more_settings_btn.clicked.connect(self._toggle_more_settings)
        lay.addWidget(self._more_settings_btn)

        self._more_settings_body = QWidget()
        self._more_settings_body.setVisible(False)
        ms_lay = QVBoxLayout(self._more_settings_body)
        ms_lay.setContentsMargins(0, 0, 0, 0)
        ms_lay.setSpacing(4)

        self._enemy_panel = QtEnemyPanel(self._small)
        ms_lay.addWidget(self._enemy_panel)

        def _make_tool_btn(text: str) -> QPushButton:
            b = self._make_btn(text, _SECONDARY_BTN_HEIGHT)
            ms_lay.addWidget(b)
            """make tool btn。"""
            return b

        self._export_btn = _make_tool_btn(tr("desktop.endfield.exportPreset"))
        self._import_btn = _make_tool_btn(tr("desktop.endfield.importPreset"))
        self._compare_btn = _make_tool_btn(tr("desktop.endfield.comparePresets"))
        self._dashboard_btn = _make_tool_btn(tr("desktop.endfield.damageDashboard"))
        self._history_btn = _make_tool_btn(tr("desktop.endfield.calcHistory"))
        self._export_log_btn = _make_tool_btn(tr("desktop.endfield.exportOpLog"))
        self._ocr_btn = _make_tool_btn(tr("desktop.endfield.ocrDetect"))
        if self._on_ocr_detect:
            self._ocr_btn.clicked.connect(self._on_ocr_detect)

        ms_lay.addStretch()
        lay.addWidget(self._more_settings_body)
        lay.addStretch()
        return col

    def _toggle_more_settings(self) -> None:
        """展开/折叠「更多设置」面板。"""
        visible = not self._more_settings_body.isVisible()
        self._more_settings_body.setVisible(visible)
        self._more_settings_btn.setText(
            tr("desktop.endfield.moreSettingsCollapse") if visible else tr("desktop.endfield.moreSettingsExpand")
        )

    def _on_calc_mode_changed(self, _text: str) -> None:
        """计算模式下拉变更：发射内部 mode_id。"""
        self.calc_mode_changed.emit(calculation_mode_from_combo(self.calc_mode_menu))

    def current_calc_mode(self) -> str:
        """获取当前计算模式内部标识。"""
        return calculation_mode_from_combo(self.calc_mode_menu)

    def current_weapon_scope_label(self) -> str:
        """武器候选范围（中文 canonical，供搜索/预设）。"""
        return combo_internal_value(self.single_skill_scope_combo)

    def current_equipment_scope_label(self) -> str:
        """装备范围（中文 canonical）。"""
        return combo_internal_value(self.equipment_scope_combo)

    # ── 列 2：全量搜索 ─────────────────────────────

    def _mark_pending(self) -> None:
        """标记配装待确认（发射 loadout_pending 信号）。"""
        self.loadout_pending.emit()

    # ── 段级次数动态行 ──────────────────────────

    def _update_workers_hint(self) -> None:
        """刷新并行线程提示文字（基于 CPU 核心数）。"""
        info = get_cpu_parallel_info()
        workers = resolve_parallel_workers(self.search_workers_combo.currentText())
        self.search_workers_hint_label.setText(format_parallel_workers_help(info, selected_workers=workers))

    def read_workers_choice(self) -> str:
        """读取并行线程选择标签。"""
        return self.search_workers_combo.currentText()

    def read_top_n_choice(self) -> str:
        """读取 Top N 条数选择标签。"""
        return self.search_top_n_combo.currentText()

    # ── 控制值读取 ──────────────────────────────

    def populate_fixed_loadout_slots(
        self,
        catalog: dict[str, list[dict[str, Any]]],
    ) -> None:
        """从装备 catalog 填充四槽装备名称下拉。"""
        from games.endfield.data_loading.equipment_filters import equipment_names_from_rows

        for i, (slot_key, _) in enumerate(_FIXED_SLOT_SPECS):
            cb = self.fixed_loadout_slots[i]
            catalog_key = "accessories" if slot_key in ("accessory_a", "accessory_b") else slot_key
            rows = list(catalog.get(catalog_key) or [])
            names = equipment_names_from_rows(rows)

            prev_data = cb.currentData()
            prev_text = cb.currentText()
            if prev_data is not None and str(prev_data) != FIXED_SLOT_NONE_LABEL:
                current = str(prev_data)
            elif prev_text in names:
                current = prev_text
            elif prev_text in (FIXED_SLOT_NONE_LABEL, tr("desktop.endfield.fixedSlotNone")):
                current = FIXED_SLOT_NONE_LABEL
            else:
                current = prev_text if prev_text in names else FIXED_SLOT_NONE_LABEL

            cb.blockSignals(True)
            cb.clear()
            cb.addItem(tr("desktop.endfield.fixedSlotNone"), FIXED_SLOT_NONE_LABEL)
            for name in names:
                cb.addItem(name)
            if current in names:
                cb.setCurrentText(current)
            else:
                set_combo_by_internal(cb, FIXED_SLOT_NONE_LABEL)
            cb.blockSignals(False)

    def read_fixed_loadout_selection(
        self,
        catalog: dict[str, list[dict[str, Any]]],
    ) -> Any:
        """从四槽下拉读取 FixedLoadoutSelection。"""
        from games.endfield.calc.loadout.slot_search import FixedLoadoutSelection

        def _pick(i: int, catalog_key: str):
            name_raw = self.fixed_loadout_slots[i].currentData()
            name = str(name_raw) if name_raw is not None else self.fixed_loadout_slots[i].currentText()
            if name == FIXED_SLOT_NONE_LABEL:
                return None
            for row in catalog.get(catalog_key) or []:
                if str(row.get("名称") or "") == name:
                    return row
            """pick。"""
            return None

        return FixedLoadoutSelection(
            chest=_pick(0, "chest"),
            gloves=_pick(1, "gloves"),
            accessory_a=_pick(2, "accessories"),
            accessory_b=_pick(3, "accessories"),
        )

    def read_skill_counts(self) -> dict[str, int]:
        """读取段级手动次数（仅正值）。"""
        result: dict[str, int] = {}
        edits = getattr(self, "_segment_count_edits_dict", None)
        if edits:
            for key, edit in edits.items():
                try:
                    val = max(0, int(edit.text() or "0"))
                except ValueError:
                    val = 0
                if val > 0:
                    result[key] = val
        return result

    def read_physical_abnormal_counts(self) -> dict[str, int]:
        """读取物理异常次数 ``{类型:ui_level: 次数}``。"""
        specs = getattr(self, "_physical_abnormal_specs", ())
        return read_abnormal_matrix_counts(self._physical_abnormal_edits, specs)

    def read_spell_abnormal_counts(self) -> dict[str, int]:
        """读取法术异常次数 ``{类型:ui_level: 次数}``。"""
        specs = getattr(self, "_spell_abnormal_specs", ())
        return read_abnormal_matrix_counts(self._spell_abnormal_edits, specs)

    def read_damage_component_mode(self) -> str:
        """读取伤害口径模式（skill_only / abnormal_only / skill_and_abnormal）。"""
        return read_damage_component_mode(self.damage_component_combo)

    def read_extra_crit_rate(self) -> float:
        """读取额外暴击率百分比。"""
        try:
            return float(self.extra_crit_rate_edit.text() or "0")
        except ValueError:
            return 0.0

    def read_extra_crit_damage(self) -> float:
        """读取额外暴击伤害百分比。"""
        try:
            return float(self.extra_crit_damage_edit.text() or "0")
        except ValueError:
            return 0.0

    def _clear_abnormal_counts(self) -> None:
        """清空所有异常次数输入（物理+法术）。"""
        for edits in self._physical_abnormal_edits.values():
            for e in edits:
                if e.isEnabled():
                    e.setText("0")
        for edits in self._spell_abnormal_edits.values():
            for e in edits:
                if e.isEnabled():
                    e.setText("0")
        self._mark_pending()
