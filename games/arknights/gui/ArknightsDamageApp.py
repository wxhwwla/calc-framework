# SPDX-License-Identifier: AGPL-3.0
"""明日方舟 Desktop GUI 伤害计算器。

基于 PySide6 的独立桌面应用，直接调用本地 DAG 引擎计算。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSlider,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

_DATA_DIR = Path(__file__).resolve().parents[2] / ".." / ".." / "tools" / "arknights_scout" / "output" / "parsed"


def _load_operators() -> dict[str, dict[str, Any]]:
    """加载所有干员 JSON 数据。"""
    result: dict[str, dict[str, Any]] = {}
    if not _DATA_DIR.is_dir():
        return result
    for f in sorted(_DATA_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            name = data.get("名称", f.stem)
            result[name] = data
        except (json.JSONDecodeError, OSError):
            pass
    return result


_OPERATORS_CACHE: dict[str, dict[str, Any]] | None = None


def _get_operators() -> dict[str, dict[str, Any]]:
    global _OPERATORS_CACHE
    if _OPERATORS_CACHE is None:
        _OPERATORS_CACHE = _load_operators()
    return _OPERATORS_CACHE


DARK_STYLESHEET = """
QMainWindow { background-color: #1A1A1A; }
QWidget { background-color: #1A1A1A; color: #D1D1D1; }
QLabel { color: #D1D1D1; }
QGroupBox {
    border: 1px solid #464646;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 16px;
    font-size: 13px;
    font-weight: bold;
    color: #E0E0E0;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}
QComboBox {
    background-color: #2B2B2B;
    color: #D1D1D1;
    border: 1px solid #464646;
    border-radius: 4px;
    padding: 4px 8px;
    min-height: 24px;
}
QComboBox:hover { border: 1px solid #2B6CB6; }
QComboBox QAbstractItemView {
    background-color: #2B2B2B;
    color: #D1D1D1;
    selection-background-color: #2B6CB6;
}
QLineEdit {
    background-color: #2B2B2B;
    color: #D1D1D1;
    border: 1px solid #464646;
    border-radius: 4px;
    padding: 4px 8px;
}
QLineEdit:focus { border: 1px solid #2B6CB6; }
QPushButton {
    background-color: #2B6CB6;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 24px;
    font-size: 14px;
    font-weight: bold;
    min-height: 20px;
}
QPushButton:hover { background-color: #3182CE; }
QPushButton:pressed { background-color: #1A4A8A; }
QPushButton:disabled { background-color: #4A4A4A; color: #888888; }
QSlider::groove:horizontal {
    height: 6px;
    background: #3C3C3C;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #2B6CB6;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}
QSlider::sub-page:horizontal { background: #2B6CB6; border-radius: 3px; }
QTableWidget {
    background-color: #1E1E1E;
    color: #D1D1D1;
    border: 1px solid #464646;
    border-radius: 4px;
    gridline-color: #333333;
}
QTableWidget::item { padding: 4px 8px; }
QHeaderView::section {
    background-color: #2B2B2B;
    color: #D1D1D1;
    border: 1px solid #464646;
    padding: 4px;
}
QScrollArea { border: none; }
QSplitter::handle {
    background-color: #464646;
    width: 2px;
}
"""


class ArknightsDamageApp(QMainWindow):
    """明日方舟桌面伤害计算器主窗口。"""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("明日方舟 伤害计算器")
        self.setMinimumSize(1024, 680)
        self.resize(1280, 760)

        self._operators_cache = _get_operators()
        self._operator_names = sorted(self._operators_cache.keys()) if self._operators_cache else []
        self._current_operator: dict[str, Any] | None = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        left_widget = self._build_left_panel()
        right_widget = self._build_right_panel()
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([400, 880])

    def _build_left_panel(self) -> QWidget:
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        select_group = QGroupBox("选择干员")
        select_layout = QVBoxLayout(select_group)

        self._operator_combo = QComboBox()
        self._operator_combo.setEditable(True)
        self._operator_combo.setPlaceholderText("搜索或选择干员...")
        self._operator_combo.addItems(self._operator_names)
        self._operator_combo.currentTextChanged.connect(self._on_operator_selected)
        select_layout.addWidget(self._operator_combo)

        self._skill_level_slider = QSlider(Qt.Horizontal)
        self._skill_level_slider.setRange(1, 10)
        self._skill_level_slider.setValue(7)
        self._skill_level_slider.setTickPosition(QSlider.TicksBelow)
        self._skill_level_slider.setTickInterval(1)

        skill_layout = QHBoxLayout()
        skill_layout.addWidget(QLabel("技能等级:"))
        self._skill_level_label = QLabel("Lv.7")
        self._skill_level_label.setStyleSheet("color: #2B6CB6; font-weight: bold;")
        skill_layout.addWidget(self._skill_level_label)
        skill_layout.addStretch()
        select_layout.addLayout(skill_layout)
        select_layout.addWidget(self._skill_level_slider)
        self._skill_level_slider.valueChanged.connect(self._on_skill_level_changed)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self._detail_widget = QWidget()
        self._detail_layout = QVBoxLayout(self._detail_widget)
        self._detail_layout.setContentsMargins(0, 0, 0, 0)

        self._detail_name_label = QLabel("")
        self._detail_name_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #E0E0E0;")
        self._detail_layout.addWidget(self._detail_name_label)

        self._detail_info_label = QLabel("")
        self._detail_info_label.setStyleSheet("color: #888888; font-size: 12px;")
        self._detail_layout.addWidget(self._detail_info_label)

        self._detail_trait_label = QLabel("")
        self._detail_trait_label.setWordWrap(True)
        self._detail_trait_label.setStyleSheet("color: #B0B0B0; font-style: italic; padding: 4px 0;")
        self._detail_layout.addWidget(self._detail_trait_label)

        self._stats_table = QTableWidget()
        self._stats_table.setColumnCount(2)
        self._stats_table.setHorizontalHeaderLabels(["属性", "数值"])
        self._stats_table.horizontalHeader().setStretchLastSection(True)
        self._stats_table.setMaximumHeight(250)
        self._stats_table.verticalHeader().setVisible(False)
        self._detail_layout.addWidget(self._stats_table)

        self._trust_label = QLabel("")
        self._trust_label.setWordWrap(True)
        self._trust_label.setStyleSheet("color: #68D391; font-size: 12px;")
        self._detail_layout.addWidget(self._trust_label)

        self._talent_label = QLabel("")
        self._talent_label.setWordWrap(True)
        self._talent_label.setStyleSheet("color: #B794F4; font-size: 12px;")
        self._detail_layout.addWidget(self._talent_label)

        self._detail_layout.addStretch()
        scroll.setWidget(self._detail_widget)

        layout.addWidget(select_group)
        layout.addWidget(scroll)

        status_label = QLabel(f"已加载 {len(self._operator_names)} 个干员")
        status_label.setStyleSheet("color: #666666; font-size: 11px;")
        layout.addWidget(status_label)

        return wrapper

    def _build_right_panel(self) -> QWidget:
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(10)

        enemy_group = QGroupBox("敌人参数")
        enemy_grid = QGridLayout(enemy_group)

        enemy_grid.addWidget(QLabel("防御力 (DEF):"), 0, 0)
        self._def_input = QLineEdit("200")
        enemy_grid.addWidget(self._def_input, 0, 1)

        enemy_grid.addWidget(QLabel("法术抗性 (RES):"), 1, 0)
        self._res_input = QLineEdit("50")
        enemy_grid.addWidget(self._res_input, 1, 1)

        self._def_slider = QSlider(Qt.Horizontal)
        self._def_slider.setRange(0, 3000)
        self._def_slider.setValue(200)
        self._def_slider.valueChanged.connect(lambda v: self._def_input.setText(str(v)))
        self._def_input.textChanged.connect(lambda t: self._sync_slider(self._def_slider, t))
        enemy_grid.addWidget(self._def_slider, 0, 2)

        self._res_slider = QSlider(Qt.Horizontal)
        self._res_slider.setRange(0, 100)
        self._res_slider.setValue(50)
        self._res_slider.valueChanged.connect(lambda v: self._res_input.setText(str(v)))
        self._res_input.textChanged.connect(lambda t: self._sync_slider(self._res_slider, t))
        enemy_grid.addWidget(self._res_slider, 1, 2)

        scroll_layout.addWidget(enemy_group)

        bonus_group = QGroupBox("额外加成")
        bonus_grid = QGridLayout(bonus_group)

        bonus_grid.addWidget(QLabel("攻击力%加成:"), 0, 0)
        self._atk_pct_input = QLineEdit("0")
        self._atk_pct_slider = QSlider(Qt.Horizontal)
        self._atk_pct_slider.setRange(-100, 200)
        self._atk_pct_slider.setValue(0)
        self._atk_pct_slider.valueChanged.connect(lambda v: self._atk_pct_input.setText(str(v)))
        self._atk_pct_input.textChanged.connect(lambda t: self._sync_slider(self._atk_pct_slider, t))
        bonus_grid.addWidget(self._atk_pct_input, 0, 1)
        bonus_grid.addWidget(self._atk_pct_slider, 0, 2)

        bonus_grid.addWidget(QLabel("伤害倍率加成%:"), 1, 0)
        self._dmg_bonus_input = QLineEdit("0")
        bonus_grid.addWidget(self._dmg_bonus_input, 1, 1)

        bonus_grid.addWidget(QLabel("防御穿透%:"), 2, 0)
        self._def_pen_input = QLineEdit("0")
        bonus_grid.addWidget(self._def_pen_input, 2, 1)

        bonus_grid.addWidget(QLabel("法抗穿透%:"), 3, 0)
        self._res_pen_input = QLineEdit("0")
        bonus_grid.addWidget(self._res_pen_input, 3, 1)

        bonus_grid.setColumnStretch(2, 1)
        scroll_layout.addWidget(bonus_group)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        self._compute_btn = QPushButton("开始计算")
        self._compute_btn.clicked.connect(self._on_compute)
        layout.addWidget(self._compute_btn)

        self._result_label = QLabel("选择干员并点击「开始计算」")
        self._result_label.setAlignment(Qt.AlignCenter)
        self._result_label.setStyleSheet("color: #888888; font-size: 12px; padding: 8px;")
        layout.addWidget(self._result_label)

        self._result_table = QTableWidget()
        self._result_table.setColumnCount(2)
        self._result_table.setHorizontalHeaderLabels(["指标", "数值"])
        self._result_table.horizontalHeader().setStretchLastSection(True)
        self._result_table.setMaximumHeight(300)
        self._result_table.verticalHeader().setVisible(False)
        layout.addWidget(self._result_table)

        return wrapper

    def _sync_slider(self, slider: QSlider, text: str) -> None:
        try:
            v = int(float(text))
            if slider.minimum() <= v <= slider.maximum():
                slider.blockSignals(True)
                slider.setValue(v)
                slider.blockSignals(False)
        except (ValueError, TypeError):
            pass

    def _on_skill_level_changed(self, value: int) -> None:
        label = f"Lv.{value}" if value <= 7 else f"专精{value - 7}"
        self._skill_level_label.setText(label)

    def _on_operator_selected(self, name: str) -> None:
        if not name or name not in self._operators_cache:
            return
        self._current_operator = self._operators_cache[name]
        self._update_detail_panel()

    def _update_detail_panel(self) -> None:
        op = self._current_operator
        if not op:
            return

        name = op.get("名称", "未知")
        star = op.get("星级", 0)
        cls = op.get("职业", "")
        branch = op.get("分支", "")
        trait = op.get("特性", "")
        stars_display = "★" * star
        self._detail_name_label.setText(f"{name}  {stars_display}")
        self._detail_info_label.setText(f"{cls} · {branch}")
        self._detail_trait_label.setText(trait)

        base = op.get("基础属性", {})
        stat_labels = {
            "生命": "生命上限", "攻击": "攻击力", "防御": "防御力",
            "法术抗性": "法术抗性", "部署费用": "部署费用",
            "再部署": "再部署时间", "阻挡数": "阻挡数", "攻击间隔": "攻击间隔",
        }
        self._stats_table.setRowCount(len(base))
        for i, (key, val) in enumerate(base.items()):
            label = stat_labels.get(key, key)
            self._stats_table.setItem(i, 0, QTableWidgetItem(label))
            val_str = str(val) if not isinstance(val, float) else f"{val:.1f}"
            self._stats_table.setItem(i, 1, QTableWidgetItem(val_str))
        self._stats_table.resizeColumnsToContents()

        trust = op.get("信赖加成", {})
        if trust and any(v != 0 for v in trust.values()):
            parts = []
            for k, v in trust.items():
                lbl = stat_labels.get(k, k)
                sign = "+" if v >= 0 else ""
                if isinstance(v, float):
                    parts.append(f"{lbl} {sign}{v:.1f}")
                else:
                    parts.append(f"{lbl} {sign}{v}")
            self._trust_label.setText(f"信赖加成（200%）：{'  '.join(parts)}")
            self._trust_label.show()
        else:
            self._trust_label.hide()

        talents = op.get("天赋", [])
        if talents:
            lines = []
            for t in talents:
                lines.append(f"{t.get('name', '')}（{t.get('unlock', '')}）：{t.get('description', '')}")
            self._talent_label.setText("天赋：\n" + "\n".join(lines))
            self._talent_label.show()
        else:
            self._talent_label.hide()

    def _on_compute(self) -> None:
        if not self._current_operator:
            self._result_label.setText("请先选择一个干员")
            return

        try:
            from games.arknights.calc.dag_adapter.adapter import compute_snapshot_with_dag

            skill_level = self._skill_level_slider.value()
            enemy_def = float(self._def_input.text() or "0")
            enemy_res = float(self._res_input.text() or "0")
            atk_pct = float(self._atk_pct_input.text() or "0")
            dmg_bonus = float(self._dmg_bonus_input.text() or "0")
            def_pen = float(self._def_pen_input.text() or "0")
            res_pen = float(self._res_pen_input.text() or "0")

            result = compute_snapshot_with_dag(
                operator=self._current_operator,
                skill_level=skill_level,
                skill_multiplier=1.0,
                enemy_def=enemy_def,
                enemy_res=enemy_res,
                atk_percent_bonus=atk_pct / 100.0,
                dmg_bonus=dmg_bonus / 100.0,
                def_penetration=def_pen,
                res_penetration=res_pen / 100.0,
            )

            outputs = result.outputs
            final_atk = outputs.get("最终攻击力", 0)
            phys = outputs.get("物理伤害", 0)
            magic = outputs.get("法术伤害", 0)
            true_dmg = outputs.get("真实伤害", 0)

            rows = [
                ("最终攻击力", f"{final_atk:.2f}"),
                ("物理伤害", f"{phys:.2f}"),
                ("法术伤害", f"{magic:.2f}"),
                ("真实伤害", f"{true_dmg:.2f}"),
            ]
            self._result_table.setRowCount(len(rows))
            for i, (k, v) in enumerate(rows):
                self._result_table.setItem(i, 0, QTableWidgetItem(k))
                item = QTableWidgetItem(v)
                if i == 1:
                    item.setForeground(Qt.darkYellow)
                elif i == 2:
                    item.setForeground(Qt.blue)
                self._result_table.setItem(i, 1, item)
            self._result_table.resizeColumnsToContents()

            self._result_label.setText(f"计算结果 — {self._current_operator.get('名称', '')}")
            self._result_label.setStyleSheet("color: #68D391; font-size: 14px; font-weight: bold; padding: 8px;")

        except Exception as e:
            self._result_label.setText(f"计算错误: {e}")
            self._result_label.setStyleSheet("color: #FC8181; font-size: 12px; padding: 8px;")
            import traceback
            traceback.print_exc()

    def run(self) -> None:
        self.show()


def main() -> None:
    """明日方舟桌面 GUI 入口。"""
    import sys as _sys
    from pathlib import Path as _Path

    _REPO_ROOT = _Path(__file__).resolve().parents[2] / ".." / ".."
    _FW_SRC = _REPO_ROOT / "framework" / "src"
    if str(_FW_SRC) not in _sys.path:
        _sys.path.insert(0, str(_FW_SRC))

    app = QApplication(_sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_STYLESHEET)

    window = ArknightsDamageApp()
    window.run()
    _sys.exit(app.exec())


if __name__ == "__main__":
    main()
