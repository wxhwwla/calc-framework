# SPDX-License-Identifier: AGPL-3.0
"""EndfieldApp — 终末地伤害计算主窗口（主骨架）。

依赖 ShellMixin（面板创建/布局）和 ActionsMixin（事件处理/计算/搜索/对话框）。
"""

from __future__ import annotations

import sys
from pathlib import Path

# 路径设置：必须在 from gui.xxx 导入之前执行
_CUR_FILE = Path(__file__).resolve()
_GAMES_ENDDIR = _CUR_FILE.parents[1]  # games/endfield/
if str(_GAMES_ENDDIR) not in sys.path:
    sys.path.insert(0, str(_GAMES_ENDDIR))

_FRAMEWORK_SRC = _CUR_FILE.parents[4] / "framework" / "src"
if str(_FRAMEWORK_SRC) not in sys.path:
    sys.path.insert(0, str(_FRAMEWORK_SRC))

from typing import Any

from PySide6.QtGui import QAction, QFont, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from scripts.please_read_me import get_exe_version

from games.endfield.framework_bridge import get_logger
from games.endfield.gui.endfield_actions import ActionsMixin
from games.endfield.gui.endfield_search import ActionsSearchMixin
from games.endfield.gui.endfield_shell import ShellMixin
from games.endfield.gui.shared.calc_mode_labels import DEFAULT_CALC_MODE_LABEL, calculation_mode_from_label
from games.endfield.gui.shared.ui_preferences import (
    load_ui_preferences,
    record_last_page,
    resolve_startup_page,
    save_ui_preferences,
)

_logger = get_logger("gui.endfield_app")


class EndfieldApp(QMainWindow, ShellMixin, ActionsMixin, ActionsSearchMixin):
    """终末地伤害计算器主窗口。

    通过多重继承组合 ShellMixin（UI 面板/布局）、ActionsMixin（事件处理/计算/对话框）
    和 ActionsSearchMixin（搜索相关事件处理）。
    管理顶层 QMainWindow、双页签布局、角色/武器选择面板联动、
    确认计算、全量搜索线程、预设导入导出、UI 偏好持久化。

    属性：
        big_font / small_font: 标题/正文字体
        tabs: QTabWidget 双页签（计算页 / 高级页）
        char_panel / weapon_panel: 角色/武器四级联动选择面板
        columns: QtAttributeColumns 三列属性展示
        control_dock: QtControlDock 高级页控制栏
        status_label: 底部状态文案
        all_weapons: 全量武器列表
        _current_calc_mode: 当前计算模式内部标识
        _enemy_defense: 当前敌人防御值
        _equipment_catalog: 当前装备目录（按装备范围筛选）
        _search_cancel_token: 搜索取消令牌
        _search_estimated_total_seconds: 最近搜索预估耗时（秒）
        _confirm_in_progress: 确认防重入标志
        _ui_preferences: UI 偏好字典
    """

    def __init__(self) -> None:
        super().__init__()

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
        self._enemy_resistance: float = 0.0
        self._ignore_resistance: float = 0.0
        self._imbalance_vulnerability_coeff: float = 1.3
        self._is_unbalanced: bool = False
        self._is_true_damage: bool = False
        self._enemy_tier: str = "普通"
        self._combo_stacks: int = 0
        self._attached_effect_multiplier: float = 1.0
        self._corrosion_duration_seconds: float = 15.0
        self._imbalance_efficiency_bonus: float = 0.0
        self._break_defense_stacks: int = 0

        self.setWindowTitle(f"终末地伤害计算小工具 v{get_exe_version()}")
        self.setMinimumSize(1024, 600)
        self.resize(1280, 720)

        self._setup_app_menu()

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(0)

        self.tabs: QTabWidget = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self._style_tabs()
        main_layout.addWidget(self.tabs, stretch=1)

        self._build_calc_page()
        self._build_adv_page()

        self._init_control_dock()
        self._connect_signals()
        self._on_char_name_change()
        """初始化实例。"""

    def run(self) -> None:
        self._load_preferences()
        self.closeEvent = self._on_close
        self.showMaximized()
        sys.exit(self._qapp.exec())
        """执行主流程。"""

    def _load_preferences(self) -> None:
        self._ui_preferences = load_ui_preferences()
        page = resolve_startup_page(self._ui_preferences)
        self.tabs.setCurrentIndex(1 if page == "高级页" else 0)
        """load preferences。"""

    def _on_close(self, event: Any = None) -> None:
        try:
            page_name = "高级页" if self.tabs.currentIndex() == 1 else "计算页"
            self._ui_preferences = record_last_page(self._ui_preferences, page=page_name)
            save_ui_preferences(self._ui_preferences)
        except Exception:
            pass
        if event is not None:
            event.accept()
        """on close。"""

    def _apply_dark_style(self) -> None:
        self._qapp.setStyleSheet("""
            QMainWindow { background-color: #1A1A1A; }
            QWidget { background-color: #1A1A1A; }
            QLabel { color: #D1D1D1; }
        """)
        """apply dark style。"""

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
        """style tabs。"""

    def _setup_app_menu(self) -> None:
        menubar = self.menuBar()
        help_menu = menubar.addMenu("帮助(&H)")
        help_action = QAction("使用说明(&U)", self)
        help_action.setShortcut(QKeySequence("F1"))
        help_action.triggered.connect(self._on_open_help)
        help_menu.addAction(help_action)
        """setup app menu。"""

    @property
    def confirm_btn(self):
        return self.control_dock.confirm_btn
        """confirm btn。"""
