#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PySide6 主应用（阶段 7 完整集成）。

双页签（计算页 / 高级页），信号路由、后台计算、三列刷新全链路。
"""

from __future__ import annotations

import sys
from typing import Any, Dict, List

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
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
    """PySide6 主应用（完整集成）。

    属性：
        app: QMainWindow
        big_font / small_font: 字体
        tabs: 双页签
        char_panel / weapon_panel: 角色/武器选择面板
        columns: 三列属性展示
        control_dock: 高级页控制栏
        status_label: 底部状态文案
        all_weapons: 全量武器列表（角色联动过滤用）
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

        self.app: QMainWindow = QMainWindow()
        self.app.setWindowTitle(f"终末地伤害计算小工具 v{get_exe_version()}")
        self.app.setMinimumSize(1024, 600)
        self.app.resize(1280, 720)

        central = QWidget()
        self.app.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(0)

        # ── 双页签 ────────────────────────────────
        self.tabs: QTabWidget = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self._style_tabs()
        main_layout.addWidget(self.tabs, stretch=1)

        # 计算页：选择面板（上） + 三列属性展示（下）
        calc_page = QWidget()
        calc_layout = QVBoxLayout(calc_page)
        calc_layout.setContentsMargins(0, 0, 0, 0)
        calc_layout.setSpacing(4)

        characters = get_characters()
        weapons = get_weapons()
        self.all_weapons: List[Dict[str, Any]] = list(weapons)

        # 选择面板（角色 + 武器左右并排）
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

        # 三列属性展示
        self.columns: QtAttributeColumns = QtAttributeColumns(
            big_font=self.big_font,
            small_font=self.small_font,
        )
        self.columns.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        calc_layout.addWidget(self.columns, stretch=1)

        self.tabs.addTab(calc_page, "计算页")

        # 高级页 → 三列控制栏
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

        # ── 信号连线 ──────────────────────────────
        self._connect_signals()

        # 初始化武器过滤
        self._on_char_name_change()

    def _connect_signals(self) -> None:
        # 角色名称变化 → 过滤武器面板
        self.char_panel.name_combo.currentTextChanged.connect(self._on_char_name_change)

        # 角色/武器各级联下拉、滑块 → 标记待确认
        self.char_panel.type_combo.currentIndexChanged.connect(self._on_loadout_changed)
        self.char_panel.star_combo.currentIndexChanged.connect(self._on_loadout_changed)
        self.char_panel.name_combo.currentIndexChanged.connect(self._on_loadout_changed)
        self.char_panel.level_slider.valueChanged.connect(self._on_loadout_changed)
        self.weapon_panel.type_combo.currentIndexChanged.connect(self._on_loadout_changed)
        self.weapon_panel.star_combo.currentIndexChanged.connect(self._on_loadout_changed)
        self.weapon_panel.name_combo.currentIndexChanged.connect(self._on_loadout_changed)
        self.weapon_panel.level_slider.valueChanged.connect(self._on_loadout_changed)

        # 控制栏信号
        self.control_dock.calc_mode_changed.connect(self._on_calc_mode_changed)

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
        """角色名称变化 → 按角色武器类型过滤武器面板。"""
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

    # ── 配装变更 ──────────────────────────────────

    def _on_loadout_changed(self) -> None:
        """任意配装参数变化 → 更新状态文案。"""
        self.status_label.setText("待确认")

    # ── 确认计算 ──────────────────────────────────

    def _build_request(self) -> Any:
        """在主线程构建 DisplayRequest（读取面板控件，不可在子线程执行）。"""
        from gui_design.app.display_request import DisplayRequest
        from gui_design.app.loadout_state import read_loadout_from_panels
        from calculation.loadout.slot_search import FixedLoadoutSelection

        loadout = read_loadout_from_panels(
            self.char_panel,
            self.weapon_panel,
            calculation_mode=self._current_calc_mode,
            weapon_scope_label=self.control_dock.single_skill_scope_combo.currentText(),
            equipment_scope_label=self.control_dock.equipment_scope_combo.currentText(),
            fixed_loadout=FixedLoadoutSelection(),
            use_manual_multi_skill_counts=False,
            manual_counts={},
            enemy_defense=100.0,
        )
        if loadout is None:
            return None
        return DisplayRequest(
            loadout=loadout,
            equipment_catalog={},
            preview_weapon_candidates=(),
        )

    def _on_confirm(self) -> None:
        """同步执行求值缓存 + 刷新三列（后续可改为后台线程）。"""
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
        from PySide6.QtWidgets import QApplication as QA
        QA.processEvents()

        # 同步求值缓存（主线程内完成，后续可改为 CalcWorker）
        self._sync_evaluation(request)

        self.columns.refresh(request)
        self.status_label.setText("就绪")
        self.confirm_btn.setEnabled(True)
        self.confirm_btn.setText("确认选择")

    def _sync_evaluation(self, request: Any) -> None:
        """调用求值缓存同步（主线程）。"""
        from gui_design.app.loadout_evaluation import sync_evaluation_cache
        try:
            sync_evaluation_cache(request.loadout)
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("求值缓存同步失败: %s", exc)

    def _on_attribution(self) -> None:
        """打开数据来源与许可说明（纯 Qt 实现）。"""
        from legal.attribution_content import SUMMARY_TEXT

        QMessageBox.information(
            self.app,
            "数据来源与许可",
            SUMMARY_TEXT,
        )

    @property
    def confirm_btn(self):
        return self.control_dock.confirm_btn
