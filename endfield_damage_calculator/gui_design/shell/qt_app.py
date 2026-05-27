#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PySide6 主应用壳层（阶段 3）。

布局：双页签（计算页 / 高级页）。
计算页嵌入 QtAttributeColumns（三列无闪渲染）。
高级页嵌入 QtControlDock。
确认按钮通过 QThread 在后台执行，GUI 不卡顿。
"""

from __future__ import annotations

import sys
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
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
from gui_design.backends.qt_worker import CalcWorker
from please_read_me import get_exe_version


def _demo_heavy_calc() -> str:
    """模拟耗时计算（阶段 2 演示用，后续替换为真正的计算函数）。"""
    import time as _time
    _time.sleep(0.5)
    return "计算完成（演示结果）"


class QtDamageApp:
    """PySide6 主应用。

    属性：
        app: QMainWindow 实例
        big_font: 标题/主按钮字体（14px bold）
        small_font: 正文/次按钮字体（12px normal）
        tabs: 双页签
        columns: 计算页三列属性展示（QtAttributeColumns 实例）
        control_dock: 高级页控制栏（QtControlDock 实例）
        status_label: 计算状态文案（高级页底部）
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

        self._worker: Optional[CalcWorker] = None

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

        # 计算页 → 三列属性展示
        calc_page = QWidget()
        calc_layout = QVBoxLayout(calc_page)
        calc_layout.setContentsMargins(0, 0, 0, 0)

        self.columns: QtAttributeColumns = QtAttributeColumns(
            big_font=self.big_font,
            small_font=self.small_font,
        )
        self.columns.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        calc_layout.addWidget(self.columns)

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

    def run(self) -> None:
        """启动主事件循环。"""
        self.app.show()
        sys.exit(self._qapp.exec())

    # ── 内部方法 ──────────────────────────────────

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

    def _show_main_page(self) -> None:
        self.tabs.setCurrentIndex(0)

    def _on_confirm(self) -> None:
        """后台执行计算，GUI 不卡顿。完成后刷新三列。"""
        if self._worker is not None:
            self.status_label.setText("已有计算进行中")
            return

        self.confirm_btn.setEnabled(False)
        self.confirm_btn.setText("计算中…")
        self.status_label.setText("计算中…")

        self._worker = CalcWorker(fn=_demo_heavy_calc)
        self._worker.finished.connect(self._on_calc_result)
        self._worker.error.connect(self._on_calc_error)
        self._worker.start()

    def _on_calc_result(self, result: str) -> None:
        self.status_label.setText(f"就绪 — {result}")
        self.confirm_btn.setEnabled(True)
        self.confirm_btn.setText("确认选择")

        self.columns.refresh_from_demo()

        self._worker = None

    def _on_calc_error(self, message: str) -> None:
        self.status_label.setText("计算失败")
        QMessageBox.critical(self.app, "计算错误", message)
        self.confirm_btn.setEnabled(True)
        self.confirm_btn.setText("确认选择")
        self._worker = None

    def _on_attribution(self) -> None:
        QMessageBox.information(
            self.app,
            "数据来源与许可",
            "数据来源与许可说明待迁移",
        )

    @property
    def confirm_btn(self):
        return self.control_dock.confirm_btn
