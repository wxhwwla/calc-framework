#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PySide6 主应用（阶段 11 — 高级页控件全连通）。

双页签（计算页 / 高级页），信号路由、面板联动、确认刷新、全部高级页控件连通。
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from gui_design.shared.gui_settings import gui_settings
from gui_design.shell.qt_control_dock import QtControlDock
from gui_design.shared.display_view.qt_columns import QtAttributeColumns
from gui_design.panels.selection.qt_panel import QtSelectionPanel
from gui_design.shared.calc_mode_labels import calculation_mode_from_label, DEFAULT_CALC_MODE_LABEL
from data.loader import get_characters, get_weapons
from please_read_me import get_exe_version


class QtDamageApp:
    """PySide6 主应用。

    属性：
        app: QMainWindow
        big_font / small_font: 字体
        tabs: 双页签
        char_panel / weapon_panel: 角色/武器选择面板
        columns: 三列属性展示
        control_dock: 高级页控制栏
        status_label: 底部状态文案
        all_weapons: 全量武器列表
        _enemy_defense: 当前敌人防御值
    """

    def __init__(self) -> None:
        gui_settings()

        self._qapp: QApplication = QApplication(sys.argv)
        self._qapp.setStyle("Fusion")
        self._apply_dark_style()

        self.big_font: QFont = QFont()
        self.big_font.setPointSize(14)
        self.big_font.setBold(True)

        self.small_font: QFont = QFont()
        self.small_font.setPointSize(12)

        self._current_calc_mode: str = calculation_mode_from_label(DEFAULT_CALC_MODE_LABEL)
        self._enemy_defense: float = 100.0

        self.app: QMainWindow = QMainWindow()
        self.app.setWindowTitle(f"终末地伤害计算小工具 v{get_exe_version()}")
        self.app.setMinimumSize(1024, 600)
        self.app.resize(1280, 720)

        central = QWidget()
        self.app.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(0)

        self.tabs: QTabWidget = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self._style_tabs()
        main_layout.addWidget(self.tabs, stretch=1)

        # ── 计算页 ────────────────────────────────
        calc_page = QWidget()
        calc_layout = QVBoxLayout(calc_page)
        calc_layout.setContentsMargins(0, 0, 0, 0)
        calc_layout.setSpacing(4)

        characters = get_characters()
        weapons = get_weapons()
        self.all_weapons: List[Dict[str, Any]] = list(weapons)

        panels_frame = QFrame()
        panels_frame.setStyleSheet("QFrame { background-color: #1E1E1E; border-radius: 8px; }")
        panels_row = QHBoxLayout(panels_frame)
        panels_row.setContentsMargins(8, 8, 8, 8)
        panels_row.setSpacing(12)

        self.char_panel = QtSelectionPanel(
            characters, self.big_font, parent=None,
        )
        self.weapon_panel = QtSelectionPanel(
            weapons, self.big_font, is_weapon_panel=True, parent=None,
        )

        panels_row.addWidget(self.char_panel, stretch=1)
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setStyleSheet("color: #333333;")
        panels_row.addWidget(line)
        panels_row.addWidget(self.weapon_panel, stretch=1)

        calc_layout.addWidget(panels_frame)

        self.columns: QtAttributeColumns = QtAttributeColumns(
            big_font=self.big_font,
            small_font=self.small_font,
        )
        self.columns.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        calc_layout.addWidget(self.columns, stretch=1)

        self.tabs.addTab(calc_page, "计算页")

        # ── 高级页 ────────────────────────────────
        self.control_dock: QtControlDock = QtControlDock(
            big_font=self.big_font,
            small_font=self.small_font,
            on_back_to_main=self._show_main_page,
            on_confirm=self._on_confirm,
            on_attribution=self._on_attribution,
        )

        adv_page = QWidget()
        adv_layout = QVBoxLayout(adv_page)
        adv_layout.setContentsMargins(0, 0, 0, 0)

        self.control_dock.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        adv_layout.addWidget(self.control_dock, stretch=1)

        self.status_label = QLabel("就绪")
        self.status_label.setFont(self.small_font)
        self.status_label.setStyleSheet("color: #828282; padding: 4px 12px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        adv_layout.addWidget(self.status_label)

        self.tabs.addTab(adv_page, "高级页")

        # ── 初始化控制栏 ──────────────────────────
        self._init_control_dock()

        # ── 信号连线 ──────────────────────────────
        self._connect_signals()

        self._on_char_name_change()

    # ── 初始化控制栏 ──────────────────────────────

    def _init_control_dock(self) -> None:
        dock = self.control_dock

        # 敌人下拉
        from data.enemy_params import list_plugin_enemy_choices, resolve_enemy_defense

        enemy_choices = list_plugin_enemy_choices()
        if enemy_choices and len(enemy_choices) > 1:
            dock._enemy_combo.clear()
            labels: list[str] = []
            id_by_label: dict[str, str] = {}
            for label, eid in enemy_choices:
                labels.append(label)
                id_by_label[label] = eid
            dock._enemy_combo.addItems(labels)

            def _on_enemy_change(text: str) -> None:
                eid = id_by_label.get(text, "")
                self._enemy_defense = resolve_enemy_defense(eid)

            dock._enemy_combo.currentTextChanged.connect(_on_enemy_change)
            dock._enemy_combo.setCurrentIndex(0)
            initial_label = dock._enemy_combo.currentText()
            if initial_label:
                eid = id_by_label.get(initial_label, "")
                self._enemy_defense = resolve_enemy_defense(eid)

        # 装备 catalog + 固定配装槽
        from data.equipment_catalog import get_equipment_catalog

        self._equipment_catalog: dict[str, list[dict[str, Any]]] = get_equipment_catalog()
        dock.populate_fixed_loadout_slots(self._equipment_catalog)

        # 装备范围变更时刷新固定配装槽
        dock.equipment_scope_combo.currentTextChanged.connect(
            self._on_equipment_scope_changed
        )

        # 手动 Buff 按钮
        dock._manual_buff_btn.clicked.connect(self._on_manual_buff)

    def _on_equipment_scope_changed(self, scope_label: str) -> None:
        from data.equipment_catalog import get_equipment_catalog

        self._equipment_catalog = get_equipment_catalog(scope_label=scope_label)
        self.control_dock.populate_fixed_loadout_slots(self._equipment_catalog)
        self._on_loadout_changed()

    # ── 信号连线 ──────────────────────────────

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

    def _connect_more_settings_btns(self) -> None:
        dock = self.control_dock
        if hasattr(dock, '_export_btn') and dock._export_btn:
            dock._export_btn.clicked.connect(self._on_export_preset)
        if hasattr(dock, '_import_btn') and dock._import_btn:
            dock._import_btn.clicked.connect(self._on_import_preset)
        if hasattr(dock, '_compare_btn') and dock._compare_btn:
            dock._compare_btn.clicked.connect(self._on_compare_presets)
        if hasattr(dock, '_dashboard_btn') and dock._dashboard_btn:
            dock._dashboard_btn.clicked.connect(self._on_damage_dashboard)
        if hasattr(dock, '_history_btn') and dock._history_btn:
            dock._history_btn.clicked.connect(self._on_calc_history)
        if hasattr(dock, '_export_log_btn') and dock._export_log_btn:
            dock._export_log_btn.clicked.connect(self._on_export_log)

    def run(self) -> None:
        """启动主事件循环。"""
        self.app.show()
        sys.exit(self._qapp.exec())

    # ── 样式 ──────────────────────────────────

    def _apply_dark_style(self) -> None:
        self._qapp.setStyleSheet("""
            QMainWindow { background-color: #1A1A1A; }
            QWidget { background-color: #1A1A1A; }
            QLabel { color: #D1D1D1; }
        """)

    def _style_tabs(self) -> None:
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #464646;
                border-radius: 16px;
                background-color: #1A1A1A;
                top: -1px;
            }
            QTabBar::tab {
                background-color: #2B2B2B;
                color: #D1D1D1;
                border: 1px solid #464646;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 6px 16px;
                margin-right: 2px;
                font-size: 13px;
            }
            QTabBar::tab:selected {
                background-color: #2B6CB6;
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #333333;
            }
        """)

    # ── 页面导航 ──────────────────────────────────

    def _show_main_page(self) -> None:
        self.tabs.setCurrentIndex(0)

    # ── 角色 → 武器联动 ──────────────────────────

    def _on_char_name_change(self) -> None:
        char_data = self.char_panel.get_selected_data()
        if not char_data:
            self.weapon_panel.update_data_list(list(self.all_weapons))
            return
        char_weapon_type = char_data.get("武器", "")
        if not char_weapon_type:
            self.weapon_panel.update_data_list(list(self.all_weapons))
            return
        filtered = [w for w in self.all_weapons if w.get("类型") == char_weapon_type]
        if not filtered:
            self.weapon_panel.update_data_list(list(self.all_weapons))
            return
        self.weapon_panel.update_data_list(filtered)

    # ── 计算模式 ──────────────────────────────────

    def _on_calc_mode_changed(self, label: str) -> None:
        self._current_calc_mode = calculation_mode_from_label(label)
        self._on_loadout_changed()

    # ── 配装变更 ──────────────────────────────────

    def _on_loadout_changed(self) -> None:
        self.status_label.setText("待确认")

    # ── 确认计算 ──────────────────────────────────

    def _build_request(self) -> Any:
        from gui_design.app.display_request import DisplayRequest
        from gui_design.app.loadout_state import read_loadout_from_panels

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
        )
        if loadout is None:
            return None
        return DisplayRequest(
            loadout=loadout,
            equipment_catalog={},
            preview_weapon_candidates=(),
        )

    def _on_confirm(self) -> None:
        char_data = self.char_panel.get_selected_data()
        weapon_data = self.weapon_panel.get_selected_data()
        if not char_data or not weapon_data:
            QMessageBox.warning(self.app, "无法计算", "请选择有效的角色和武器。")
            return

        request = self._build_request()
        if request is None:
            QMessageBox.warning(self.app, "无法计算", "无法读取配装数据。")
            return

        self.confirm_btn.setEnabled(False)
        self.confirm_btn.setText("计算中…")
        self.status_label.setText("计算中…")
        QApplication.processEvents()

        self._sync_evaluation(request)

        self.columns.refresh(request)
        self.status_label.setText("就绪")
        self.confirm_btn.setEnabled(True)
        self.confirm_btn.setText("确认选择")

    def _sync_evaluation(self, request: Any) -> None:
        from gui_design.app.loadout_evaluation import sync_evaluation_cache
        try:
            sync_evaluation_cache(request.loadout)
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("求值缓存同步失败: %s", exc)

    # ── 手动 Buff ─────────────────────────────

    def _on_manual_buff(self) -> None:
        QMessageBox.information(
            self.app, "场外 Buff 微调",
            "手动 Buff 编辑窗口当前为 CTk 独占功能。\n"
            "Qt 端将在此后版本支持。\n\n"
            "暂占位：请在 CTk 后端配置 Buff 后切回 Qt 查看。",
        )

    # ── 更多设置（工具与分享）回调 ──────────────

    def _on_export_preset(self) -> None:
        from gui_design.app.loadout_preset import (
            LoadoutPreset,
            export_preset_json,
        )
        preset = LoadoutPreset(
            char_name=self.char_panel.name_combo.currentText(),
            weapon_name=self.weapon_panel.name_combo.currentText(),
            char_level=self.char_panel.level_slider.value(),
            weapon_level=self.weapon_panel.level_slider.value(),
            trust_level=self.char_panel.get_trust_level(),
            skill_levels=(
                self.char_panel.get_skill_1_level(),
                self.char_panel.get_skill_2_level(),
                self.char_panel.get_skill_3_level(),
            ),
            calculation_mode=self._current_calc_mode,
            weapon_scope=self.control_dock.single_skill_scope_combo.currentText(),
            equipment_scope=self.control_dock.equipment_scope_combo.currentText(),
        )
        path, _ = QFileDialog.getSaveFileName(
            self.app, "导出配装预设", "preset.json", "JSON (*.json)",
        )
        if not path:
            return
        Path(path).write_text(export_preset_json(preset), encoding="utf-8")
        self.status_label.setText("预设已导出")

    def _on_import_preset(self) -> None:
        from gui_design.app.loadout_preset import import_presets_from_json_text
        path, _ = QFileDialog.getOpenFileName(
            self.app, "导入配装预设", "", "JSON (*.json)",
        )
        if not path:
            return
        try:
            presets = import_presets_from_json_text(Path(path).read_text(encoding="utf-8"))
            if presets:
                self.status_label.setText(f"已导入 {len(presets)} 条预设")
        except Exception as exc:
            QMessageBox.warning(self.app, "导入失败", str(exc))

    def _on_compare_presets(self) -> None:
        QMessageBox.information(
            self.app, "多方案对比",
            "多方案对比需要选择多个预设 JSON 文件。\n"
            "该功能当前为 CTk 独占，Qt 端将在此后版本支持。",
        )

    def _on_damage_dashboard(self) -> None:
        QMessageBox.information(
            self.app, "伤害仪表盘",
            "伤害仪表盘基于 matplotlib，当前为 CTk 独占功能。\n"
            "Qt 端将在此后版本支持。",
        )

    def _on_calc_history(self) -> None:
        QMessageBox.information(
            self.app, "计算历史",
            "计算历史面板当前为 CTk 独占功能。\n"
            "Qt 端将在此后版本支持。",
        )

    def _on_export_log(self) -> None:
        QMessageBox.information(
            self.app, "导出操作日志",
            "操作日志导出当前为 CTk 独占功能。\n"
            "Qt 端将在此后版本支持。",
        )

    # ── 搜索回调 ──────────────────────────────

    def _on_mvp_search(self) -> None:
        self.status_label.setText("MVP 搜索：CTk 独占，Qt 端待实现")

    def _on_full_search(self) -> None:
        self.status_label.setText("全量遍历搜索：CTk 独占，Qt 端待实现")

    def _on_cancel_search(self) -> None:
        self.status_label.setText("搜索已取消（占位）")

    # ── 数据来源与许可 ──────────────────────────

    def _on_attribution(self) -> None:
        from legal.attribution_content import SUMMARY_TEXT

        QMessageBox.information(
            self.app,
            "数据来源与许可",
            SUMMARY_TEXT,
        )

    @property
    def confirm_btn(self):
        return self.control_dock.confirm_btn
