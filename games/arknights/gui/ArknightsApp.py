# ruff: noqa: N999
# SPDX-License-Identifier: AGPL-3.0
"""单片式 ArknightsApp — 明日方舟伤害计算主窗口。

使用 ComputeSheet + layout.json 声明式面板，与终末地 EndfieldApp 架构对齐。
**注意**：当前 launcher / main.py 默认使用功能完整的 `ArknightsDamageApp`（见
``docs/plans/arknights-desktop-web-parity.md``）；本模块为 ComputeSheet 声明式线，
可通过 ``CALC_ARKNIGHTS_GUI=sheet`` 启动。
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSlider,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

_CUR_FILE = Path(__file__).resolve()
_GAMES_ARKNIGHTS = _CUR_FILE.parents[1]
if str(_GAMES_ARKNIGHTS) not in sys.path:
    sys.path.insert(0, str(_GAMES_ARKNIGHTS))

for p in [
    d for d in (Path.cwd(), _CUR_FILE.parents[3], _CUR_FILE.parents[2].parent / "endfield") if str(d) not in sys.path
]:
    sys.path.insert(0, str(p))

from calc_framework.ui.log_widget import LogWidget

from games.arknights.calc.dag_adapter.adapter import get_parsed_skill_info
from games.arknights.framework_bridge import ComputeSheet, get_logger
from games.arknights.gui.arknights_compute_sheet import (
    build_result_html,
    combo_index_to_skill_index,
    create_arknights_compute_sheet,
    ensure_arknights_adapter,
    mount_compute_sheet,
    populate_operator_context,
    wire_compute_button,
)
from games.arknights.operator_catalog import build_operator_index, filter_operator_index, load_operators_map
from games.endfield.gui.legal.donation_qt import open_donation_dialog

_logger = get_logger("gui.arknights_app")


def _ensure_adapter():
    """获取或初始化 DAG 适配器包和布局（惰性加载）。"""
    return ensure_arknights_adapter()


class ArknightsApp(QMainWindow):
    """明日方舟伤害计算器主窗口。

    左侧为干员筛选与选择面板（游戏特有）。
    右侧为 ComputeSheet 声明式输入/输出面板（框架通用）。
    """

    def __init__(self, *, embedded: bool = False) -> None:
        self._embedded = embedded
        existing = QApplication.instance()
        if existing is None:
            self._qapp: QApplication = QApplication(sys.argv)
            self._owns_qapp = True
        else:
            self._qapp = existing
            self._owns_qapp = False
        if self._owns_qapp:
            self._qapp.setStyle("Fusion")
            self._apply_dark_style()

        super().__init__()

        self.big_font: QFont = QFont()
        self.big_font.setPointSize(14)
        self.big_font.setBold(True)

        self.normal_font: QFont = QFont()
        self.normal_font.setPointSize(12)

        self.setWindowTitle("明日方舟伤害计算器")
        self.setMinimumSize(1000, 600)
        self.resize(1280, 720)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        self._compute_sheet_widget = QWidget()
        self._compute_sheet_widget.setLayout(QVBoxLayout())
        right_scroll.setWidget(self._compute_sheet_widget)

        self._operator_data: dict[str, Any] | None = None
        self._compute_sheet: ComputeSheet | None = None
        self._result_summary = QLabel("")
        self._result_summary.setTextFormat(Qt.TextFormat.RichText)
        self._result_summary.setWordWrap(True)
        self._result_summary.setStyleSheet("font-size: 14px; padding: 8px;")
        self._donation_btn = QPushButton("☕ 打赏支持")
        self._donation_btn.clicked.connect(lambda: open_donation_dialog(self))
        self._init_compute_sheet()

        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setMinimumWidth(320)
        left_panel = self._build_operator_panel()
        left_scroll.setWidget(left_panel)
        splitter.addWidget(left_scroll)
        splitter.addWidget(right_scroll)

        splitter.setSizes([400, 600])

        self._setup_menu()

    def _build_operator_panel(self) -> QWidget:
        """构建左侧干员选择面板，含筛选/搜索/技能选择。"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(8)

        filter_group = QGroupBox("筛选")
        filter_layout = QVBoxLayout(filter_group)

        star_row = QHBoxLayout()
        self._star_checkboxes: list[QCheckBox] = []
        for s in range(1, 7):
            cb = QCheckBox(str(s))
            cb.setChecked(True)
            cb.stateChanged.connect(self._on_filter_changed)
            self._star_checkboxes.append(cb)
            star_row.addWidget(cb)
        filter_layout.addWidget(QLabel("星级"))
        filter_layout.addLayout(star_row)

        self._profession_combo = QComboBox()
        self._profession_combo.addItems(["全部", "先锋", "近卫", "重装", "狙击", "术师", "医疗", "辅助", "特种"])
        self._profession_combo.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(QLabel("职业"))
        filter_layout.addWidget(self._profession_combo)

        self._branch_combo = QComboBox()
        self._branch_combo.addItems(["全部分支"])
        self._branch_combo.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(QLabel("分支"))
        filter_layout.addWidget(self._branch_combo)

        layout.addWidget(filter_group)

        select_group = QGroupBox("选择干员")
        select_layout = QVBoxLayout(select_group)

        search_layout = QHBoxLayout()
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("输入干员名搜索...")
        self._search_input.textChanged.connect(self._on_filter_changed)
        search_layout.addWidget(self._search_input)

        self._operator_combo = QComboBox()
        self._operator_combo.setEditable(False)
        self._operator_combo.currentIndexChanged.connect(self._on_operator_selected)
        select_layout.addWidget(QLabel("干员"))
        select_layout.addWidget(self._operator_combo)

        layout.addWidget(select_group)

        skill_group = QGroupBox("技能选择")
        skill_layout = QVBoxLayout(skill_group)

        self._skill_combo = QComboBox()
        self._skill_combo.addItems(["普通攻击", "技能1", "技能2", "技能3"])
        self._skill_combo.currentIndexChanged.connect(self._on_skill_changed)
        skill_layout.addWidget(QLabel("技能"))
        skill_layout.addWidget(self._skill_combo)

        self._skill_level_slider = QSlider(Qt.Orientation.Horizontal)
        self._skill_level_slider.setRange(1, 10)
        self._skill_level_slider.setValue(7)
        self._skill_level_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._skill_level_slider.setTickInterval(1)
        self._skill_level_label = QLabel("技能等级: 7")
        self._skill_level_slider.valueChanged.connect(lambda v: self._skill_level_label.setText(f"技能等级: {v}"))
        skill_layout.addWidget(self._skill_level_label)
        skill_layout.addWidget(self._skill_level_slider)

        self._skill_info_box = QLabel("选择干员后显示技能信息")
        self._skill_info_box.setWordWrap(True)
        self._skill_info_box.setStyleSheet("color: #A0A0A0; padding: 4px;")
        skill_layout.addWidget(self._skill_info_box)

        layout.addWidget(skill_group)

        self._operator_detail = QScrollArea()
        self._operator_detail.setWidgetResizable(True)
        self._operator_detail.setMinimumHeight(150)
        self._detail_widget = QLabel("选择干员后显示详细信息")
        self._detail_widget.setWordWrap(True)
        self._operator_detail.setWidget(self._detail_widget)
        layout.addWidget(self._operator_detail, stretch=1)

        self._all_operators: dict[str, dict[str, Any]] = {}
        self._filtered_operators: list[dict[str, Any]] = []
        try:
            self._all_operators = load_operators_map()
            self._operator_index = build_operator_index(self._all_operators)
            self._filtered_operators = list(self._all_operators.values())
        except Exception as exc:
            _logger.warning("干员数据加载失败: %s", exc)
            self._all_operators = {}
            self._operator_index = []
            self._filtered_operators = []

        self._filter_and_populate()

        return panel

    def _init_compute_sheet(self) -> None:
        """创建持久化 ComputeSheet 并挂载到右栏（Phase 3 双向绑定）。"""
        pkg, layout = _ensure_adapter()
        assert layout is not None
        sheet = create_arknights_compute_sheet(pkg.dag_service, layout, parent=self)
        sheet.evaluated.connect(self._on_compute_sheet_evaluated)
        wire_compute_button(sheet, self._compute_result)
        mount_compute_sheet(
            self._compute_sheet_widget,
            sheet,
            extra_widgets=[self._result_summary, self._donation_btn],
        )
        self._compute_sheet = sheet

    def _filter_and_populate(self) -> None:
        """按星级/职业/分支/搜索词筛选干员并更新下拉列表。"""
        selected_stars = [i + 1 for i, cb in enumerate(self._star_checkboxes) if cb.isChecked()]
        prof = self._profession_combo.currentText()
        branch = self._branch_combo.currentText()
        search = self._search_input.text().strip()
        try:
            self._filtered_operators = filter_operator_index(
                self._operator_index,
                active_stars=set(selected_stars),
                profession=prof,
                branch=branch,
                search=search,
            )
        except Exception as exc:
            _logger.warning("筛选失败: %s", exc)
            self._filtered_operators = list(self._operator_index)

        current_name = self._operator_combo.currentText() if self._operator_combo.count() > 0 else ""
        self._operator_combo.blockSignals(True)
        self._operator_combo.clear()
        for op in self._filtered_operators:
            self._operator_combo.addItem(op.get("名称", "?"))
        if self._operator_combo.count() == 0:
            self._operator_combo.addItem("（无干员数据）")
        idx = self._operator_combo.findText(current_name)
        if idx >= 0:
            self._operator_combo.setCurrentIndex(idx)
        self._operator_combo.blockSignals(False)
        self._on_operator_selected()

    def _on_filter_changed(self) -> None:
        """筛选条件变化时重新筛选并更新下拉。"""
        self._filter_and_populate()

    def _on_operator_selected(self) -> None:
        """当前选中的干员变化时更新详情和技能信息。"""
        idx = self._operator_combo.currentIndex()
        if idx < 0 or idx >= len(self._filtered_operators):
            self._operator_data = None
            if self._operator_combo.currentText() == "（无干员数据）":
                self._detail_widget.setText(
                    "未找到干员数据。请重新打包，或确认 exe 同目录存在 "
                    "framework/adapters/arknights/data/operators_standard.json。"
                )
            else:
                self._detail_widget.setText("请选择有效干员")
            self._on_skill_changed()
            return
        entry = self._filtered_operators[idx]
        name = str(entry.get("名称") or "")
        self._operator_data = self._all_operators.get(name)
        if self._operator_data is None:
            self._detail_widget.setText("请选择有效干员")
            self._on_skill_changed()
            return
        info_parts = [f"<b>{name}</b>"]
        prof = entry.get("职业", "")
        star = entry.get("星级", "")
        info_parts.append(f"职业: {prof}  星级: {star}")
        atk = self._operator_data.get("攻击力", "?")
        info_parts.append(f"攻击力: {atk}")
        self._detail_widget.setText("<br>".join(info_parts))
        self._on_skill_changed()

    def _on_skill_changed(self) -> None:
        """技能或技能等级变化时更新技能信息并触发计算。"""
        if self._operator_data is None:
            self._skill_info_box.setText("选择干员后显示技能信息")
            self._compute_result()
            return
        skill_index = combo_index_to_skill_index(self._skill_combo.currentIndex())
        level = self._skill_level_slider.value()
        try:
            info = get_parsed_skill_info(self._operator_data, level=level, skill_index=skill_index)
            lines = [f"倍率: {info.multiplier}" if info.multiplier else "倍率: 待解析"]
            if info.attack_count and info.attack_count > 1:
                lines.append(f"攻击次数: {info.attack_count}")
            if info.description:
                lines.append(info.description[:200])
            self._skill_info_box.setText("\n".join(lines))
        except Exception as exc:
            self._skill_info_box.setText(f"技能信息解析中... ({exc})")
        self._compute_result()

    def _compute_result(self) -> None:
        """同步干员/技能上下文后通过 ComputeSheet 求值。"""
        if self._operator_data is None or self._compute_sheet is None:
            self._result_summary.setText("")
            return
        level = self._skill_level_slider.value()
        skill_index = combo_index_to_skill_index(self._skill_combo.currentIndex())
        try:
            info = get_parsed_skill_info(
                self._operator_data,
                level=level,
                skill_index=skill_index,
            )
            populate_operator_context(
                self._compute_sheet,
                self._operator_data,
                skill_multiplier=info.effective_multiplier,
                skill_level=level,
            )
            self._compute_sheet.evaluate()
        except Exception as exc:
            _logger.warning("计算失败: %s", exc)

    def _on_compute_sheet_evaluated(self, result: Any = None) -> None:
        """ComputeSheet 求值完成：更新底部结果摘要。"""
        if result is None:
            return
        self._result_summary.setText(build_result_html(result))

    # ── 菜单栏 ──────────────────────────────────────────

    def _setup_menu(self) -> None:
        """设置菜单栏。"""
        menubar = self.menuBar()

        debug_menu = menubar.addMenu("调试(&D)")
        log_action = QAction("日志(&L)", self)
        log_action.triggered.connect(self._open_log_dialog)
        debug_menu.addAction(log_action)

    def _open_log_dialog(self) -> None:
        """打开日志查看对话框。"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout

        dialog = QDialog(self)
        dialog.setWindowTitle("运行时日志")
        dialog.resize(700, 400)
        layout = QVBoxLayout(dialog)
        log_widget = LogWidget(max_lines=5000)
        log_widget.attach_to_logger(level=logging.INFO)
        layout.addWidget(log_widget)
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        dialog.show()
        _logger.info("日志查看窗口已打开")

    def _apply_dark_style(self) -> None:
        """应用深色主题样式表（委托框架 ThemeManager）。"""
        from calc_framework.ui.theme import ThemeManager

        tm = ThemeManager()
        self._qapp.setStyleSheet(tm.stylesheet("dark"))

    def run(self) -> None:
        """启动应用主循环。"""
        self.closeEvent = self._on_close
        self.showMaximized()
        if self._owns_qapp:
            sys.exit(self._qapp.exec())

    def show_embedded(self) -> None:
        """由启动器同进程拉起时仅显示窗口。"""
        self.closeEvent = self._on_close
        self.showMaximized()

    def _on_close(self, event: Any = None) -> None:
        """窗口关闭事件处理。"""
        if event is not None:
            event.accept()
