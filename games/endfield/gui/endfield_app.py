# SPDX-License-Identifier: AGPL-3.0
"""单片式 EndfieldApp — 终末地伤害计算主窗口。

替代 qt_app.py + SearchMixin + ConfirmMixin + DialogMixin 的分散结构。
P2 迁移目标：所有面板最终使用 ComputeSheet + layout.json。
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

from PySide6.QtCore import Qt, QThread
from PySide6.QtGui import QAction, QFont, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from games.endfield.data_loading.loader import get_characters, get_weapons
from games.endfield.framework_bridge import AdapterPackage, ComputeSheet, get_logger, load_layout_json
from games.endfield.gui.app.loadout_evaluation import refresh_damage_snapshot, sync_evaluation_cache as _sync_eval_cache
from games.endfield.gui.app.loadout_state import read_loadout_from_panels
from games.endfield.gui.controls.search.qt_actions import QtSearchResultsDialog, SearchWorker
from games.endfield.gui.controls.search.qt_search_browser import SearchHistoryDialog
from games.endfield.gui.legal.attribution_content import SUMMARY_TEXT
from games.endfield.gui.legal.donation_qt import open_donation_dialog
from games.endfield.gui.presentation.damage_snapshot import get_snapshot_from_app
from games.endfield.gui.presentation.search_results_lines import build_search_results_report_lines
from games.endfield.gui.presentation.total_damage_panel import TotalDamagePanel
from games.endfield.gui.shared.calc_history import HistoryEntry, get_app_calculation_history
from games.endfield.gui.shared.calc_mode_labels import DEFAULT_CALC_MODE_LABEL, calculation_mode_from_label
from games.endfield.gui.shared.display_view.qt_columns import QtAttributeColumns
from games.endfield.gui.shared.ui_preferences import (
    load_ui_preferences,
    record_last_page,
    resolve_startup_page,
    save_ui_preferences,
)
from games.endfield.gui.panels.selection.qt_panel import QtSelectionPanel
from games.endfield.gui.shell.qt_control_dock import QtControlDock
from scripts.please_read_me import get_exe_version
from utils.app_paths import allocate_search_run_directory, default_search_output_root

_logger = get_logger("gui.endfield_app")

_FRAMEWORK_ADAPTER = _CUR_FILE.parents[4] / "framework" / "adapters" / "endfield"

_adapter_pkg: AdapterPackage | None = None
_adapter_layout = None


def _ensure_adapter():
    global _adapter_pkg, _adapter_layout
    if _adapter_pkg is None:
        _adapter_pkg = AdapterPackage(str(_FRAMEWORK_ADAPTER))
        layout_path = _FRAMEWORK_ADAPTER / "ui" / "layout.json"
        _adapter_layout = load_layout_json(layout_path.read_text(encoding="utf-8"))
    return _adapter_pkg, _adapter_layout
    """ensure adapter。"""


class EndfieldApp(QMainWindow):
    """终末地伤害计算器主窗口（单片式）。

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

    def _build_calc_page(self) -> None:
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

        self.char_panel = QtSelectionPanel(characters, self.big_font, parent=None)
        self.weapon_panel = QtSelectionPanel(weapons, self.big_font, is_weapon_panel=True, parent=None)

        panels_row.addWidget(self.char_panel, stretch=1)
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setStyleSheet("color: #333333;")
        panels_row.addWidget(line)
        panels_row.addWidget(self.weapon_panel, stretch=1)

        calc_layout.addWidget(panels_frame)

        content_split = QSplitter(Qt.Orientation.Horizontal)
        calc_layout.addWidget(content_split, stretch=1)

        self.columns: QtAttributeColumns = QtAttributeColumns(big_font=self.big_font, small_font=self.small_font)
        content_split.addWidget(self.columns)

        self._compute_sheet: ComputeSheet | None = None
        self._compute_sheet_widget: QWidget = QWidget()
        sheet_layout = QVBoxLayout(self._compute_sheet_widget)
        sheet_layout.setContentsMargins(0, 0, 0, 0)
        sheet_layout.addWidget(QLabel("按「确认选择」加载乘区数据"))

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
        """build calc page。"""

    def _build_adv_page(self) -> None:
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
        """build adv page。"""

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

    def _show_main_page(self) -> None:
        self.tabs.setCurrentIndex(0)
        """show main page。"""

    def _on_char_name_change(self) -> None:
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
        """on char name change。"""

    def _rebuild_segment_rows(self) -> None:
        char_data = self.char_panel.get_selected_data()
        if not char_data:
            self.control_dock.rebuild_segment_rows(None, 1, 1, 1)
            return
        s1 = self.char_panel.get_skill_1_level()
        s2 = self.char_panel.get_skill_2_level()
        s3 = self.char_panel.get_skill_3_level()
        self.control_dock.rebuild_segment_rows(char_data, s1, s2, s3)
        """rebuild segment rows。"""

    def _on_calc_mode_changed(self, label: str) -> None:
        self._current_calc_mode = calculation_mode_from_label(label)
        self._on_loadout_changed()
        """on calc mode changed。"""

    def _on_loadout_changed(self) -> None:
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
        """on loadout changed。"""

    def _init_control_dock(self) -> None:
        dock = self.control_dock

        self._confirm_btn_default_style = dock.confirm_btn.styleSheet()

        dock._enemy_panel.enemy_params_changed.connect(self._on_enemy_params_changed)
        initial_params = dock._enemy_panel.get_params()
        self._apply_enemy_params(initial_params)

        from games.endfield.data_loading.equipment_catalog import get_equipment_catalog

        self._equipment_catalog: dict[str, list[dict[str, Any]]] = get_equipment_catalog()
        dock.populate_fixed_loadout_slots(self._equipment_catalog)

        self._search_cancel_token = None
        self._search_estimated_total_seconds: float = 0.0

        dock.equipment_scope_combo.currentTextChanged.connect(self._on_equipment_scope_changed)

        dock._enemy_panel.setVisible(False)

        dock._manual_buff_btn.clicked.connect(self._on_manual_buff)
        dock._survival_btn.clicked.connect(self._on_survival_estimate)
        """init control dock。"""

    def _on_equipment_scope_changed(self, scope_label: str) -> None:
        from games.endfield.data_loading.equipment_catalog import get_equipment_catalog

        self._equipment_catalog = get_equipment_catalog(scope_label=scope_label)
        self.control_dock.populate_fixed_loadout_slots(self._equipment_catalog)
        self._on_loadout_changed()
        """on equipment scope changed。"""

    @property
    def confirm_btn(self):
        return self.control_dock.confirm_btn
        """confirm btn。"""

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
        """build request。"""

    def _on_confirm(self) -> None:
        if getattr(self, "_confirm_in_progress", False):
            return
        char_data = self.char_panel.get_selected_data()
        weapon_data = self.weapon_panel.get_selected_data()
        if not char_data or not weapon_data:
            QMessageBox.warning(self, "无法计算", "请选择有效的角色和武器。")
            return
        request = self._build_request()
        if request is None:
            QMessageBox.warning(self, "无法计算", "无法读取配装数据。")
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
            "user_input.敌人防御": {"source": "user_input", "type": "float", "default": 100.0, "min": 0, "max": 99999, "step": 10.0},
            "user_input.敌人等阶": {"source": "user_input", "type": "str", "default": "普通"},
            "user_input.敌人抗性": {"source": "user_input", "type": "float", "default": 0.0, "min": -100, "max": 100, "step": 1.0},
            "user_input.无视抗性": {"source": "user_input", "type": "float", "default": 0.0, "min": -100, "max": 100, "step": 1.0},
            "user_input.失衡易伤系数": {"source": "user_input", "type": "float", "default": 1.3, "min": 0.1, "max": 10.0, "step": 0.05},
            "user_input.是否失衡": {"source": "user_input", "type": "bool", "default": False},
            "user_input.是否真实伤害": {"source": "user_input", "type": "bool", "default": False},
            "user_input.连击层数": {"source": "user_input", "type": "int", "default": 0, "min": 0, "max": 4, "step": 1},
            "user_input.额外暴击率": {"source": "user_input", "type": "float", "default": 0.0, "min": 0, "max": 1.0, "step": 0.01},
            "user_input.额外暴击伤害": {"source": "user_input", "type": "float", "default": 0.0, "min": 0, "max": 5.0, "step": 0.01},
            "user_input.额外伤害加成": {"source": "user_input", "type": "float", "default": 0.0, "min": 0, "max": 5.0, "step": 0.01},
            "user_input.附带效果倍率": {"source": "user_input", "type": "float", "default": 1.0, "min": 0.1, "max": 3.0, "step": 0.05},
            "user_input.破防层数": {"source": "user_input", "type": "int", "default": 0, "min": 0, "max": 4, "step": 1},
            "user_input.失衡效率加成": {"source": "user_input", "type": "float", "default": 0.0, "min": 0, "max": 1.0, "step": 0.05},
            "user_input.腐蚀计时(秒)": {"source": "user_input", "type": "float", "default": 15.0, "min": 0.0, "max": 15.0, "step": 0.5},
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

        compute_sheet = ComputeSheet(
            dag_service, layout, variables, base_context={},
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

    def _refresh_search_estimate(self) -> None:
        dock = self.control_dock
        if dock.estimate_output_label is None:
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
        """refresh search estimate。"""

    # ── 全量搜索 ──────────────────────────────────

    def _build_search_job_inputs(self) -> Any:
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
        )
        if loadout is None:
            return None
        return loadout.to_search_job_inputs(
            all_weapons=list(self.all_weapons),
            equipment_catalog=dict(self._equipment_catalog),
        )
        """build search job inputs。"""

    def _on_mvp_search(self) -> None:
        from games.endfield.calc.search.plan.controller import prepare_search_job
        from games.endfield.calc.search.run.cancel import SearchCancelToken

        inputs = self._build_search_job_inputs()
        if inputs is None:
            QMessageBox.warning(self, "MVP 搜索", "请先选择有效的角色和武器。")
            return
        job, err = prepare_search_job(inputs)
        if err or job is None:
            QMessageBox.warning(self, "最优搜索", err or "无法准备搜索任务")
            return

        output_dir = QFileDialog.getExistingDirectory(
            self, "选择 MVP 搜索导出目录", str(default_search_output_root()),
        )
        export_root = allocate_search_run_directory(purpose="mvp_search") if not output_dir else Path(output_dir)

        cancel_token = SearchCancelToken()
        self._search_cancel_token = cancel_token
        worker = SearchWorker(
            job, mode_label="最优搜索并导出", export_root=export_root,
            top_n_choice=self.control_dock.read_top_n_choice(),
            workers_choice=self.control_dock.read_workers_choice(),
            status_prefix="最优搜索状态", cancel_token=cancel_token,
        )
        self._start_search_thread(worker, "最优搜索状态：计算中，请稍候...")
        """on mvp search。"""

    def _on_full_search(self) -> None:
        from games.endfield.calc.search.plan.controller import prepare_search_job
        from games.endfield.calc.search.run.cancel import SearchCancelToken
        from games.endfield.calc.search.run.single_skill import estimate_single_skill_search
        from games.endfield.gui.controls.search.search_settings import resolve_parallel_workers, resolve_top_n

        inputs = self._build_search_job_inputs()
        if inputs is None:
            QMessageBox.warning(self, "全量遍历", "请先选择有效的角色和武器。")
            return
        job, err = prepare_search_job(inputs)
        if err or job is None:
            QMessageBox.warning(self, "全量遍历", err or "无法准备搜索任务")
            return

        dock = self.control_dock
        estimate = estimate_single_skill_search(
            job, max_workers=resolve_parallel_workers(dock.read_workers_choice()),
            top_n=resolve_top_n(dock.read_top_n_choice()),
        )
        self._search_estimated_total_seconds = estimate.estimated_seconds
        if estimate.estimated_seconds >= 120:
            reply = QMessageBox.question(
                self, "确认全量遍历", f"{estimate.text}\n\n组合较多，是否仍要开始？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        cancel_token = SearchCancelToken()
        self._search_cancel_token = cancel_token
        export_root = allocate_search_run_directory(purpose="full_search")
        mode_label = "多技能加权全量遍历" if job.multi_skill_eval is not None else "单技能全量遍历"
        worker = SearchWorker(
            job, mode_label=mode_label, export_root=export_root,
            top_n_choice=dock.read_top_n_choice(),
            workers_choice=dock.read_workers_choice(),
            status_prefix="全量遍历", cancel_token=cancel_token,
        )
        self._start_search_thread(worker, "全量遍历：计算中，请稍候。")
        """on full search。"""

    def _start_search_thread(self, worker: Any, status_running: str) -> None:
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
        """start search thread。"""

    def _on_search_progress(self, text: str) -> None:
        self.control_dock.mvp_status_label.setText(text)
        """on search progress。"""

    def _on_search_finished(self, mode_label: str, job: Any, outcome: Any, export_paths: dict) -> None:
        self._search_cancel_token = None
        self._search_thread.quit()
        self._search_thread.wait()
        damage_metric = "加权总伤" if job.multi_skill_eval is not None else "伤害"
        lines = build_search_results_report_lines(
            mode_label=mode_label, skill_label=str(job.skill_label),
            scope_labels=(str(job.weapon_scope), str(job.equipment_scope)),
            processed_combinations=int(outcome.processed_combinations),
            total_combinations=int(outcome.total_combinations),
            top_results=outcome.top_results, export_paths=export_paths,
            cancelled=bool(outcome.cancelled), damage_metric=damage_metric,
            segment_counts=(dict(job.multi_skill_eval.skill_counts) if job.multi_skill_eval else None),
            abnormal_counts=dict(job.physical_abnormal_counts or {}),
            spell_abnormal_counts=dict(job.spell_abnormal_counts or {}),
        )
        suffix = "（已取消）" if outcome.cancelled else "：完成"
        mode = "全量遍历" if "全量" in mode_label else "MVP搜索状态"
        status = f"{mode}{suffix}（{outcome.processed_combinations}/{outcome.total_combinations}）"
        self.control_dock.mvp_status_label.setText(status)
        self._set_search_btns_enabled(True)
        dialog = QtSearchResultsDialog(
            self, title=mode_label, lines=lines,
            big_font=self.big_font, small_font=self.small_font,
            top_results=outcome.top_results,
            damage_metric=damage_metric,
            segment_counts=(dict(job.multi_skill_eval.skill_counts) if job.multi_skill_eval else None),
            abnormal_counts=dict(job.physical_abnormal_counts or {}),
            spell_abnormal_counts=dict(job.spell_abnormal_counts or {}),
        )
        dialog.exec()
        """on search finished。"""

    def _on_search_error(self, error_msg: str) -> None:
        self._search_cancel_token = None
        if hasattr(self, "_search_thread") and self._search_thread:
            self._search_thread.quit()
            self._search_thread.wait()
        self.control_dock.mvp_status_label.setText(f"搜索失败：{error_msg}")
        self._set_search_btns_enabled(True)
        QMessageBox.critical(self, "搜索失败", error_msg)
        """on search error。"""

    def _on_cancel_search(self) -> None:
        if self._search_cancel_token is not None:
            self._search_cancel_token.cancel()
            self.control_dock.mvp_status_label.setText("搜索状态：正在取消。")
        """on cancel search。"""

    def _set_search_btns_enabled(self, enabled: bool) -> None:
        dock = self.control_dock
        dock.mvp_search_btn.setEnabled(enabled)
        dock.full_search_btn.setEnabled(enabled)
        dock.search_workers_combo.setEnabled(enabled)
        dock.search_top_n_combo.setEnabled(enabled)
        dock.search_cancel_btn.setEnabled(not enabled)
        """set search btns enabled。"""

    # ── 对话框 / 工具 / 信号 ─────────────────────

    def _on_manual_buff(self) -> None:
        from games.endfield.gui.controls.manual_buff.qt_window import QtManualBuffDialog

        def _read_counts():
            dock = self.control_dock
            return dock.read_skill_counts(), dock.read_physical_abnormal_counts(), dock.read_spell_abnormal_counts()
            """read counts。"""

        dialog = QtManualBuffDialog(
            self, big_font=self.big_font, small_font=self.small_font,
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
            is_true_damage=self._is_true_damage,
        )
        if loadout is None:
            QMessageBox.warning(self, "处决/治疗估算", "请先选择角色与武器。")
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
            is_true_damage=self._is_true_damage,
        )
        if loadout is None:
            QMessageBox.warning(self, "导出预设", "无法读取配装数据。")
            return
        preset = loadout.to_loadout_preset()
        path, _ = QFileDialog.getSaveFileName(self, "导出配装预设", "preset.json", "JSON (*.json)")
        if not path:
            return
        Path(path).write_text(export_preset_json(preset), encoding="utf-8")
        self.status_label.setText("预设已导出")
        """on export preset。"""

    def _on_import_preset(self) -> None:
        from games.endfield.gui.app.loadout_preset import import_presets_from_json_text

        path, _ = QFileDialog.getOpenFileName(self, "导入配装预设", "", "JSON (*.json)")
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
            QMessageBox.warning(self, "导入预设失败", str(exc))
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
            parent=self, big_font=self.big_font, small_font=self.small_font,
            char_panel=self.char_panel, weapon_panel=self.weapon_panel,
        )
        dialog.exec()
        """on compare presets。"""

    def _on_attribution(self) -> None:
        QMessageBox.about(self, "数据来源与声明", SUMMARY_TEXT)
        """on attribution。"""

    def _on_donation(self) -> None:
        open_donation_dialog(self)
        """on donation。"""

    def _on_damage_dashboard(self) -> None:
        from games.endfield.gui.controls.enhancement.qt_dialogs import QtDamageDashboardDialog

        snapshot = get_snapshot_from_app(self)
        dialog = QtDamageDashboardDialog(
            self, big_font=self.big_font, small_font=self.small_font, snapshot=snapshot,
        )
        dialog.exec()
        """on damage dashboard。"""

    def _on_calc_history(self) -> None:
        from games.endfield.gui.controls.enhancement.qt_dialogs import QtCalcHistoryDialog

        history = get_app_calculation_history(self)
        dialog = QtCalcHistoryDialog(
            self, big_font=self.big_font, small_font=self.small_font,
            history=history, apply_fn=self._apply_preset_to_qt_app,
        )
        dialog.exec()
        """on calc history。"""

    def _on_export_log(self) -> None:
        from utils.operation_log import get_session_operation_log

        path, _ = QFileDialog.getSaveFileName(self, "导出操作日志", "operation_log.json", "JSON (*.json)")
        if not path:
            return
        try:
            get_session_operation_log().export_to_file(Path(path))
            self.status_label.setText("操作日志已导出")
        except Exception as exc:
            QMessageBox.warning(self, "导出失败", str(exc))
        """on export log。"""

    def _on_open_help(self) -> None:
        from utils.gui.help_calculator import build_calculator_help
        from utils.gui.help_dialog import HelpDialog

        dialog = HelpDialog(build_calculator_help, self, title="终末地伤害计算器 使用说明")
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

            open_ocr_detection_dialog(self, on_apply=_apply_ocr)
        except Exception as exc:
            msg = f"无法加载 OCR 模块：\n{exc}\n\n请安装: pip install torchvision easyocr"
            QMessageBox.warning(self, "截图识装", msg)
        """on ocr detect。"""

    def _on_search_history(self) -> None:
        dialog = SearchHistoryDialog(self, big_font=self.big_font, small_font=self.small_font)
        dialog.exec()
        """on search history。"""

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

    def _connect_search_estimate_triggers(self) -> None:
        dock = self.control_dock
        dock.single_skill_scope_combo.currentTextChanged.connect(self._refresh_search_estimate)
        dock.equipment_scope_combo.currentTextChanged.connect(self._refresh_search_estimate)
        dock.search_workers_combo.currentTextChanged.connect(self._refresh_search_estimate)
        dock.search_top_n_combo.currentTextChanged.connect(self._refresh_search_estimate)
        """connect search estimate triggers。"""
