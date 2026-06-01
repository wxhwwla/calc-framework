#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""

PySide6 主应用。



双页签（计算页 / 高级页），信号路由、面板联动、确认刷新、搜索、预设导入导出、

增强工具（计算历史 / 多方案对比 / 伤害仪表盘）、UI 偏好持久化。

"""



from __future__ import annotations

import sys
from typing import Any

from PySide6.QtCore import Qt, QThread
from PySide6.QtGui import QAction, QFont, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from scripts.please_read_me import get_exe_version

from games.endfield.data_loading.loader import get_characters, get_weapons
from games.endfield.framework_bridge import AdapterPackage, ComputeSheet, get_logger, load_layout_json
from gui_design.panels.selection.qt_panel import QtSelectionPanel
from gui_design.shared.calc_mode_labels import DEFAULT_CALC_MODE_LABEL, calculation_mode_from_label
from gui_design.shared.display_view.qt_columns import QtAttributeColumns
from gui_design.shell.qt_app_confirm_mixin import ConfirmMixin
from gui_design.shell.qt_app_dialog_mixin import DialogMixin
from gui_design.shell.qt_app_search_mixin import SearchMixin
from gui_design.shell.qt_control_dock import QtControlDock

_qt_logger = get_logger("gui.qt_app")



# ── 框架 ComputeSheet ──────────────────────────

import sys as _sys
from pathlib import Path as _Path

_FRAMEWORK_SRC = _Path(__file__).resolve().parents[4] / "framework" / "src"

if str(_FRAMEWORK_SRC) not in _sys.path:

    _sys.path.insert(0, str(_FRAMEWORK_SRC))



_FRAMEWORK_ADAPTER = _Path(__file__).resolve().parents[4] / "framework" / "adapters" / "endfield"



_adapter_pkg: AdapterPackage | None = None

_adapter_layout = None



def _ensure_adapter():

    global _adapter_pkg, _adapter_layout

    if _adapter_pkg is None:

        _adapter_pkg = AdapterPackage(str(_FRAMEWORK_ADAPTER))

        layout_path = _FRAMEWORK_ADAPTER / "ui" / "layout.json"

        _adapter_layout = load_layout_json(layout_path.read_text(encoding="utf-8"))

    return _adapter_pkg, _adapter_layout



class QtDamageApp(SearchMixin, ConfirmMixin, DialogMixin):

    """PySide6 主应用。



    管理顶层 QMainWindow、双页签布局、角色/武器选择面板联动、

    确认计算、全量搜索线程、预设导入导出、UI 偏好持久化。



    属性：

        app: QMainWindow 顶层窗口

        big_font / small_font: 标题/正文字体

        tabs: QTabWidget 双页签（计算页 / 高级页）

        char_panel / weapon_panel: 角色/武器四级联动选择面板

        columns: QtAttributeColumns 三列属性展示

        control_dock: QtControlDock 高级页控制栏

        status_label: 底部状态文案

        all_weapons: 全量武器列表

        _current_calc_mode: 当前计算模式内部标识

        _enemy_defense: 当前敌人防御值

        _enemy_resistance: 当前敌人抗性

        _ignore_resistance: 无视抗性比例

        _imbalance_vulnerability_coeff: 失衡易伤系数

        _is_unbalanced: 是否处于失衡状态

        _equipment_catalog: 当前装备目录（按装备范围筛选）

        _search_cancel_token: 搜索取消令牌

        _search_estimated_total_seconds: 最近搜索预估耗时（秒）

        _confirm_in_progress: 确认防重入标志

        _ui_preferences: UI 偏好字典

    """



    def __init__(self) -> None:

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



        self.app: QMainWindow = QMainWindow()

        self.app.setWindowTitle(f"终末地伤害计算小工具 v{get_exe_version()}")

        self.app.setMinimumSize(1024, 600)

        self.app.resize(1280, 720)

        self._setup_app_menu()



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

        self.all_weapons: list[dict[str, Any]] = list(weapons)



        panels_frame = QFrame()

        panels_frame.setStyleSheet("QFrame { background-color: #1E1E1E; border-radius: 8px; }")

        panels_row = QHBoxLayout(panels_frame)

        panels_row.setContentsMargins(8, 8, 8, 8)

        panels_row.setSpacing(12)



        self.char_panel = QtSelectionPanel(

            characters,

            self.big_font,

            parent=None,

        )

        self.weapon_panel = QtSelectionPanel(

            weapons,

            self.big_font,

            is_weapon_panel=True,

            parent=None,

        )



        panels_row.addWidget(self.char_panel, stretch=1)

        line = QFrame()

        line.setFrameShape(QFrame.Shape.VLine)

        line.setStyleSheet("color: #333333;")

        panels_row.addWidget(line)

        panels_row.addWidget(self.weapon_panel, stretch=1)



        calc_layout.addWidget(panels_frame)



        # ── 内容区：左 属性 + 右 ComputeSheet ──────

        from PySide6.QtWidgets import QSplitter



        content_split = QSplitter(Qt.Orientation.Horizontal)

        calc_layout.addWidget(content_split, stretch=1)



        self.columns: QtAttributeColumns = QtAttributeColumns(

            big_font=self.big_font,

            small_font=self.small_font,

        )

        content_split.addWidget(self.columns)



        self._compute_sheet: ComputeSheet | None = None

        self._compute_sheet_widget: QWidget = QWidget()

        sheet_layout = QVBoxLayout(self._compute_sheet_widget)

        sheet_layout.setContentsMargins(0, 0, 0, 0)

        sheet_layout.addWidget(QLabel("按「确认选择」加载乘区数据"))



        from gui_design.presentation.total_damage_panel import TotalDamagePanel



        self._total_damage_panel = TotalDamagePanel(self.big_font, self.small_font)

        sheet_layout.addWidget(self._total_damage_panel)



        sheet_scroll = QScrollArea()

        sheet_scroll.setWidgetResizable(True)

        sheet_scroll.setWidget(self._compute_sheet_widget)



        right_wrapper = QWidget()

        right_layout = QVBoxLayout(right_wrapper)

        right_layout.setContentsMargins(0, 0, 0, 0)

        right_layout.setSpacing(6)

        right_layout.addWidget(sheet_scroll, stretch=1)



        content_split.addWidget(right_wrapper)

        content_split.setSizes([400, 400])



        self.tabs.addTab(calc_page, "计算页")



        # ── 高级页 ────────────────────────────────

        self.control_dock: QtControlDock = QtControlDock(

            big_font=self.big_font,

            small_font=self.small_font,

            on_back_to_main=self._show_main_page,

            on_confirm=self._on_confirm,

            on_attribution=self._on_attribution,

            on_donation=self._on_donation,

            on_open_help=self._on_open_help,

            on_ocr_detect=self._on_ocr_detect,

            on_search_history=self._on_search_history,

        )



        adv_page = QWidget()

        adv_layout = QVBoxLayout(adv_page)

        adv_layout.setContentsMargins(0, 0, 0, 0)



        self.control_dock.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

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

        """初始化高级页控制栏：敌人下拉、装备 catalog、固定配装槽、手动 Buff 按钮。"""

        dock = self.control_dock



        # 保存确认按钮默认样式

        self._confirm_btn_default_style = dock.confirm_btn.styleSheet()



        # 敌人参数面板

        dock._enemy_panel.enemy_params_changed.connect(self._on_enemy_params_changed)

        initial_params = dock._enemy_panel.get_params()

        self._apply_enemy_params(initial_params)



        # 装备 catalog + 固定配装槽

        from games.endfield.data_loading.equipment_catalog import get_equipment_catalog



        self._equipment_catalog: dict[str, list[dict[str, Any]]] = get_equipment_catalog()

        dock.populate_fixed_loadout_slots(self._equipment_catalog)



        self._search_cancel_token = None

        self._search_estimated_total_seconds: float = 0.0



        # 装备范围变更时刷新固定配装槽

        dock.equipment_scope_combo.currentTextChanged.connect(self._on_equipment_scope_changed)



        # 手动 Buff 按钮

        dock._manual_buff_btn.clicked.connect(self._on_manual_buff)
        dock._survival_btn.clicked.connect(self._on_survival_estimate)



    def _on_equipment_scope_changed(self, scope_label: str) -> None:

        """装备范围下拉变更：重新获取 catalog 并刷新固定配装槽。"""

        from games.endfield.data_loading.equipment_catalog import get_equipment_catalog



        self._equipment_catalog = get_equipment_catalog(scope_label=scope_label)

        self.control_dock.populate_fixed_loadout_slots(self._equipment_catalog)

        self._on_loadout_changed()



    def run(self) -> None:

        """启动主事件循环：加载偏好、绑定关闭事件、最大化显示。"""

        self._load_preferences()

        self.app.closeEvent = self._on_close

        self.app.showMaximized()

        sys.exit(self._qapp.exec())



    # ── 偏好持久化 ─────────────────────────────



    def _load_preferences(self) -> None:

        """加载 UI 偏好（上次页签），恢复启动页。"""

        from gui_design.shared.ui_preferences import (
            load_ui_preferences,
            resolve_startup_page,
        )



        self._ui_preferences = load_ui_preferences()

        page = resolve_startup_page(self._ui_preferences)

        if page == "高级页":

            self.tabs.setCurrentIndex(1)

        else:

            self.tabs.setCurrentIndex(0)



    def _on_close(self, event: Any = None) -> None:

        """关闭窗口：保存 UI 偏好（当前页签），接受关闭事件。"""

        from gui_design.shared.ui_preferences import (
            record_last_page,
            save_ui_preferences,
        )



        try:

            page_name = "高级页" if self.tabs.currentIndex() == 1 else "计算页"

            self._ui_preferences = record_last_page(self._ui_preferences, page=page_name)

            save_ui_preferences(self._ui_preferences)

        except Exception:

            pass

        if event is not None:

            event.accept()



    # ── 样式 ──────────────────────────────────



    def _apply_dark_style(self) -> None:

        """应用暗色 Fusion 样式到 QApplication。"""

        self._qapp.setStyleSheet("""

            QMainWindow { background-color: #1A1A1A; }

            QWidget { background-color: #1A1A1A; }

            QLabel { color: #D1D1D1; }

        """)



    def _style_tabs(self) -> None:

        """美化 QTabWidget 页签样式。"""

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



    # ── 帮助菜单 ──────────────────────────────────



    def _setup_app_menu(self) -> None:

        menubar = self.app.menuBar()

        help_menu = menubar.addMenu("帮助(&H)")

        help_action = QAction("使用说明(&U)", self.app)

        help_action.setShortcut(QKeySequence("F1"))

        help_action.triggered.connect(self._on_open_help)

        help_menu.addAction(help_action)



    # ── 页面导航 ──────────────────────────────────



    def _show_main_page(self) -> None:

        """切回计算页。"""

        self.tabs.setCurrentIndex(0)



    # ── 角色 → 武器联动 ──────────────────────────



    def _on_char_name_change(self) -> None:

        """角色名称变更：按武器类型过滤武器面板，重建次数段行。"""

        char_data = self.char_panel.get_selected_data()

        if not char_data:

            self.weapon_panel.update_data_list(list(self.all_weapons))

            self._rebuild_segment_rows()

            return

        char_weapon_type = char_data.get("武器", "")

        if not char_weapon_type:

            self.weapon_panel.update_data_list(list(self.all_weapons))

            self._rebuild_segment_rows()

            return

        filtered = [w for w in self.all_weapons if w.get("类型") == char_weapon_type]

        if not filtered:

            self.weapon_panel.update_data_list(list(self.all_weapons))

            self._rebuild_segment_rows()

            return

        self.weapon_panel.update_data_list(filtered)

        self._rebuild_segment_rows()



    def _rebuild_segment_rows(self) -> None:

        """根据角色技能等级重建技能段数输入行。"""

        char_data = self.char_panel.get_selected_data()

        if not char_data:

            self.control_dock.rebuild_segment_rows(None, 1, 1, 1)

            return

        s1 = self.char_panel.get_skill_1_level()

        s2 = self.char_panel.get_skill_2_level()

        s3 = self.char_panel.get_skill_3_level()

        self.control_dock.rebuild_segment_rows(char_data, s1, s2, s3)



    # ── 计算模式 ──────────────────────────────────



    def _on_calc_mode_changed(self, label: str) -> None:

        """计算模式下拉变更：更新内部标识，标记待确认。"""

        self._current_calc_mode = calculation_mode_from_label(label)

        self._on_loadout_changed()



    # ── 配装变更 ──────────────────────────────────



    def _on_loadout_changed(self) -> None:

        """配装参数变更：按钮紫色「待更新」样式，重建次数段行，清空总伤面板。"""

        self.status_label.setText("待确认")

        self.confirm_btn.setText("确认选择（待更新）")

        self.confirm_btn.setStyleSheet("""

            QPushButton { background-color: #7C3AED; color: white;

                          border: none; border-radius: 4px;

                          font-size: 14px; font-weight: bold; }

            QPushButton:hover { background-color: #6D28D9; }

            QPushButton:disabled { background-color: #444; color: #888; }

        """)

        self._rebuild_segment_rows()

        self._total_damage_panel.hide_damage()



    def _sync_evaluation(self, request: Any) -> None:

        """将请求配装的求值结果写入缓存，避免重复计算。"""

        from gui_design.app.loadout_evaluation import sync_evaluation_cache



        try:

            sync_evaluation_cache(request.loadout)

        except Exception as exc:

            _qt_logger.warning("求值缓存同步失败: %s", exc)

    def _update_total_damage_panel(self) -> None:

        """从 app._last_damage_snapshot 刷新总伤面板。"""

        from gui_design.presentation.damage_snapshot import get_snapshot_from_app



        snapshot = get_snapshot_from_app(self)

        self._total_damage_panel.update_from_snapshot(snapshot)

    def _start_search_thread(self, worker: Any, status_running: str) -> None:

        """在 QThread 中启动 SearchWorker，连接进度/完成/错误信号。"""

        self._search_thread = QThread()

        worker.moveToThread(self._search_thread)



        worker.progress.connect(self._on_search_progress)

        worker.finished.connect(self._on_search_finished)

        worker.error.connect(self._on_search_error)



        self._search_thread.started.connect(worker.run)

        self._search_thread.finished.connect(self._search_thread.deleteLater)

        self._search_thread.start()



        self._set_search_btns_enabled(False)

        self.control_dock.search_cancel_btn.setEnabled(True)

        self.control_dock.mvp_status_label.setVisible(True)

        self.control_dock.mvp_status_label.setText(status_running)

    def _set_search_btns_enabled(self, enabled: bool) -> None:

        """根据是否搜索中，启用/禁用搜索按钮组。"""

        dock = self.control_dock

        dock.mvp_search_btn.setEnabled(enabled)

        dock.full_search_btn.setEnabled(enabled)

        dock.search_workers_combo.setEnabled(enabled)

        dock.search_top_n_combo.setEnabled(enabled)

        dock.search_cancel_btn.setEnabled(not enabled)

    @property

    def confirm_btn(self):

        """快捷访问 control_dock 中的确认按钮。"""

        return self.control_dock.confirm_btn

