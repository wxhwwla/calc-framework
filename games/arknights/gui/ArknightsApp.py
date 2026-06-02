# SPDX-License-Identifier: AGPL-3.0
"""单片式 ArknightsApp — 明日方舟伤害计算主窗口。

使用 ComputeSheet + layout.json 声明式面板，与终末地 EndfieldApp 架构对齐。
左侧为干员选择面板（游戏特有），右侧为 ComputeSheet（框架通用）。
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

_CUR_FILE = Path(__file__).resolve()
_GAMES_ARKNIGHTS = _CUR_FILE.parents[1]
if str(_GAMES_ARKNIGHTS) not in sys.path:
    sys.path.insert(0, str(_GAMES_ARKNIGHTS))

for p in [d for d in (Path.cwd(), _CUR_FILE.parents[3], _CUR_FILE.parents[2].parent / "endfield")
          if str(d) not in sys.path]:
    sys.path.insert(0, str(p))

from games.arknights.calc.dag_adapter.adapter import compute_snapshot_with_dag, get_parsed_skill_info
from games.arknights.data_loading.loader import load_operators_map, filter_operator_index
from games.arknights.framework_bridge import AdapterPackage, ComputeSheet, get_logger, load_layout_json
from games.endfield.gui.legal.donation_qt import open_donation_dialog

_logger = get_logger("gui.arknights_app")

_FRAMEWORK_ADAPTER = _CUR_FILE.parents[4] / "framework" / "adapters" / "arknights"

_adapter_pkg: AdapterPackage | None = None
_adapter_layout = None


def _ensure_adapter():
    """获取或初始化 DAG 适配器包和布局（惰性加载）。"""
    global _adapter_pkg, _adapter_layout
    if _adapter_pkg is None:
        _adapter_pkg = AdapterPackage(str(_FRAMEWORK_ADAPTER))
        layout_path = _FRAMEWORK_ADAPTER / "ui" / "layout.json"
        _adapter_layout = load_layout_json(layout_path.read_text(encoding="utf-8"))
    return _adapter_pkg, _adapter_layout


class ArknightsApp(QMainWindow):
    """明日方舟伤害计算器主窗口。

    左侧为干员筛选与选择面板（游戏特有）。
    右侧为 ComputeSheet 声明式输入/输出面板（框架通用）。
    """

    def __init__(self) -> None:
        super().__init__()
        """初始化实例。"""

        self._qapp: QApplication = QApplication(sys.argv)
        self._qapp.setStyle("Fusion")
        self._apply_dark_style()

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

        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setMinimumWidth(320)
        left_panel = self._build_operator_panel()
        left_scroll.setWidget(left_panel)
        splitter.addWidget(left_scroll)

        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        self._compute_sheet_widget = QWidget()
        self._compute_sheet_widget.setLayout(QVBoxLayout())
        right_scroll.setWidget(self._compute_sheet_widget)
        splitter.addWidget(right_scroll)

        splitter.setSizes([400, 600])

        self._operator_data: dict[str, Any] | None = None
        self._result_labels: dict[str, QLabel] = {}
        self._zone_labels: dict[str, QLabel] = {}
        self._donation_btn = QPushButton("☕ 打赏支持")
        self._donation_btn.clicked.connect(lambda: open_donation_dialog(self))
        """初始化实例。"""
        """初始化实例。"""

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
        self._skill_level_slider.valueChanged.connect(
            lambda v: self._skill_level_label.setText(f"技能等级: {v}")
        )
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

        self._all_operators: list[dict[str, Any]] = []
        self._filtered_operators: list[dict[str, Any]] = []
        try:
            self._all_operators = load_operators_map()
            self._filtered_operators = list(self._all_operators)
        except Exception as exc:
            _logger.warning("干员数据加载失败: %s", exc)
            self._all_operators = []
            self._filtered_operators = []

        self._filter_and_populate()

        return panel

    def _filter_and_populate(self) -> None:
        """按星级/职业/分支/搜索词筛选干员并更新下拉列表。"""
        selected_stars = [i + 1 for i, cb in enumerate(self._star_checkboxes) if cb.isChecked()]
        prof = self._profession_combo.currentText()
        branch = self._branch_combo.currentText()
        search = self._search_input.text().strip()
        try:
            self._filtered_operators = filter_operator_index(
                self._all_operators, selected_stars, prof, branch, search,
            )
        except Exception as exc:
            _logger.warning("筛选失败: %s", exc)
            self._filtered_operators = list(self._all_operators)

        current_name = self._operator_combo.currentText() if self._operator_combo.count() > 0 else ""
        self._operator_combo.blockSignals(True)
        self._operator_combo.clear()
        for op in self._filtered_operators:
            self._operator_combo.addItem(op.get("名称", "?"))
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
            self._detail_widget.setText("请选择有效干员")
            self._on_skill_changed()
            return
        self._operator_data = self._filtered_operators[idx]
        name = self._operator_data.get("名称", "?")
        info_parts = [f"<b>{name}</b>"]
        prof = self._operator_data.get("职业", "")
        star = self._operator_data.get("星级", "")
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
        skill_idx = self._skill_combo.currentIndex()
        level = self._skill_level_slider.value()
        try:
            info = get_parsed_skill_info(self._operator_data, level=level, skill_index=skill_idx)
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
        """用 DAG 引擎执行伤害计算并更新结果。"""
        if self._operator_data is None:
            return
        skill_idx = self._skill_combo.currentIndex()
        level = self._skill_level_slider.value()
        try:
            result = compute_snapshot_with_dag(
                self._operator_data,
                skill_level=level,
            )
            self._on_compute_result(result)
        except Exception as exc:
            _logger.warning("计算失败: %s", exc)

    def _on_compute_result(self, result: Any) -> None:
        """接收到 DAG 计算结果后渲染 ComputeSheet 和结果表格。"""
        pkg, layout = _ensure_adapter()
        dag_service = pkg.dag_service

        variables = dict(dag_service.dag.variables)
        user_vars: dict[str, Any] = {
            "user_input.技能倍率": {"source": "user_input", "type": "float", "default": 1.0, "min": 0.0, "max": 10.0, "step": 0.01},
            "user_input.技能等级": {"source": "user_input", "type": "int", "default": 7, "min": 1, "max": 10, "step": 1},
            "user_input.敌人防御": {"source": "user_input", "type": "float", "default": 200.0, "min": 0, "max": 10000, "step": 10},
            "user_input.敌人法术抗性": {"source": "user_input", "type": "float", "default": 50.0, "min": 0, "max": 100, "step": 1},
            "user_input.攻击力百分比加成": {"source": "user_input", "type": "float", "default": 0.0, "min": 0, "max": 5.0, "step": 0.01},
            "user_input.伤害加成": {"source": "user_input", "type": "float", "default": 0.0, "min": -5.0, "max": 5.0, "step": 0.01},
            "user_input.物理穿透": {"source": "user_input", "type": "float", "default": 0.0, "min": 0, "max": 3000, "step": 10},
            "user_input.法术穿透": {"source": "user_input", "type": "float", "default": 0.0, "min": 0, "max": 1.0, "step": 0.01},
            "user_input.信赖攻击": {"source": "user_input", "type": "float", "default": 0, "min": 0, "max": 500, "step": 1},
            "user_input.潜能攻击": {"source": "user_input", "type": "float", "default": 0, "min": 0, "max": 500, "step": 1},
        }
        variables.update(user_vars)

        user_context_overrides = {
            "user_input.技能倍率": ("computed.技能倍率", ["override"]),
            "user_input.技能等级": ("computed.技能等级", ["override"]),
            "user_input.敌人防御": ("enemy.防御", ["override"]),
            "user_input.敌人法术抗性": ("enemy.法术抗性", ["override"]),
            "user_input.攻击力百分比加成": ("computed.攻击力百分比加成", ["override"]),
            "user_input.伤害加成": ("computed.伤害加成", ["override"]),
            "user_input.物理穿透": ("computed.物理穿透", ["override"]),
            "user_input.法术穿透": ("computed.法术穿透", ["override"]),
            "user_input.信赖攻击": ("character.信赖攻击", ["override"]),
            "user_input.潜能攻击": ("character.潜能攻击", ["override"]),
        }

        compute_sheet = ComputeSheet(
            dag_service, layout, variables, base_context={},
            user_context_overrides=user_context_overrides,
        )

        op = self._operator_data or {}
        base_atk = float(op.get("攻击力", 0))
        compute_sheet.set("character.攻击力", base_atk)

        outputs = result.outputs if hasattr(result, "outputs") else {}
        for out_name, val in outputs.items():
            compute_sheet.set(out_name, val)  # direct DAG output override

        compute_sheet.evaluate()

        cw = self._compute_sheet_widget
        old_layout = cw.layout()
        if old_layout is not None:
            while old_layout.count():
                item = old_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
        new_layout = QVBoxLayout()
        new_layout.setContentsMargins(0, 0, 0, 0)

        sheet_widget = compute_sheet.widget

        result_text = self._build_result_text(result)
        result_label = QLabel(result_text)
        result_label.setTextFormat(Qt.TextFormat.RichText)
        result_label.setWordWrap(True)
        result_label.setStyleSheet("font-size: 14px; padding: 8px;")

        new_layout.addWidget(sheet_widget, stretch=1)
        new_layout.addWidget(result_label)
        new_layout.addWidget(self._donation_btn)
        cw.setLayout(new_layout)

    def _build_result_text(self, result: Any) -> str:
        """将计算结果格式化为 HTML 表格字符串。"""
        outputs = result.outputs if hasattr(result, "outputs") else {}
        lines = ['<hr><table style="width:100%;border-collapse:collapse;">']
        lines.append('<tr style="background:#2B6CB6;color:white;">'
                     '<td colspan="2" style="padding:6px 10px;font-weight:bold;font-size:15px;">'
                     '计算结果</td></tr>')
        for name in ["最终攻击力", "物理伤害", "法术伤害", "真伤伤害"]:
            val = outputs.get(name)
            if val is not None:
                lines.append(f'<tr><td style="padding:3px 10px;">{name}</td>'
                             f'<td style="padding:3px 10px;text-align:right;font-weight:bold;">'
                             f'{val:.2f}</td></tr>')
        lines.append('</table>')
        return "\n".join(lines)

    def _on_compute_sheet_evaluated(self, result: Any = None) -> None:
        """ComputeSheet 求值完成回调（预留）。"""
        pass

    def _apply_dark_style(self) -> None:
        """应用深色主题样式表。"""
        self._qapp.setStyleSheet("""
            QMainWindow { background-color: #1A1A1A; }
            QWidget { background-color: #1A1A1A; }
            QLabel { color: #D1D1D1; }
        """)

    def run(self) -> None:
        """启动应用主循环。"""
        self.closeEvent = self._on_close
        self.showMaximized()
        sys.exit(self._qapp.exec())

    def _on_close(self, event: Any = None) -> None:
        """窗口关闭事件处理。"""
        if event is not None:
            event.accept()
