"""CalcPackViewer — 通用用户展示层。

加载 .calcpack 文件并渲染完整的交互式计算界面。
支持实体选择（角色/武器/装备）、自定义输入、实时 DAG 求值。

用法::

    python -m calc_framework.ui.viewer path/to/game.calcpack
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QScrollArea,
    QSlider,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from calc_framework.dag.schema import DAGVariable
from calc_framework.dag.serializer import dag_from_dict
from calc_framework.dag.service import DAGService
from calc_framework.ui.compute_sheet import ComputeSheet
from calc_framework.ui.layout import load_layout, Layout

_VARIABLE_FIELD_MAP: dict[str, str] = {
    "基础攻击力": "基础攻击",
}

_SOURCE_TO_DATA_FILE: dict[str, str] = {
    "character": "characters",
    "weapon": "weapons",
    "equipment": "equipments",
}

_DATA_FILE_TO_SOURCE: dict[str, str] = {
    "characters": "character",
    "weapons": "weapon",
    "equipments": "equipment",
}

_FALLBACK_DEFAULTS: dict[str, float] = {
    "技能倍率": 1.0,
    "伤害加成": 0.0,
    "伤害减免": 0.0,
    "增幅": 0.0,
    "虚弱": 0.0,
    "庇护": 0.0,
    "脆弱": 0.0,
    "易伤": 0.0,
    "失衡易伤": 0.0,
    "抗性": 0.0,
    "非主控减伤": 0.0,
    "连击增伤": 0.0,
    "特殊乘区": 1.0,
    "主能力平值加算": 0.0,
    "副能力平值加算": 0.0,
    "主能力百分比": 0.0,
    "副能力百分比": 0.0,
    "力量加成值": 0.0,
    "敏捷加成值": 0.0,
    "智识加成值": 0.0,
    "意志加成值": 0.0,
    "防御": 100.0,
    "暴击率": 0.05,
    "暴击伤害": 0.5,
}


def _load_calcpack(path: str | Path) -> dict[str, Any]:
    """加载 .calcpack 文件，返回内部文件映射 {arcname: raw_bytes}。"""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f".calcpack 文件未找到: {p}")
    result: dict[str, Any] = {}
    with zipfile.ZipFile(p, "r") as zf:
        for name in zf.namelist():
            raw = zf.read(name)
            if name.endswith(".json"):
                result[name] = json.loads(raw.decode("utf-8"))
            else:
                result[name] = raw
    return result


def _resolve_field_name(field: str) -> str:
    """将实体数据字段名映射为 DAG context 字段名。

    例如 "基础攻击力" → "基础攻击"（Endfield 命名差异）。
    通用情况下直接返回原字段名。
    """
    return _VARIABLE_FIELD_MAP.get(field, field)


def _build_context_from_entity(
    entity: dict[str, Any],
    namespace: str,
    level: int = 90,
) -> dict[str, float]:
    """从实体数据构建 context 命名空间字典。

    level 为 1-indexed（1 = 最低等级）。
    """
    ctx: dict[str, float] = {}
    for key, val in entity.items():
        if key in ("名称", "技能", "_entity_type", "类型", "星级", "武器",
                   "主能力", "副能力", "装备种类", "部位", "稀有度",
                   "所属套组", "套装", "属性词条", "效果", "三件套效果", "_source",
                   "等级", "潜能", "信赖", "信赖加成"):
            continue
        if isinstance(val, list) and all(isinstance(v, (int, float)) for v in val):
            idx = min(level, len(val)) - 1
            resolved = _resolve_field_name(key)
            ctx[resolved] = float(val[idx])
        elif isinstance(val, (int, float)):
            resolved = _resolve_field_name(key)
            ctx[resolved] = float(val)
    return ctx


class CalcPackViewer(QMainWindow):
    """通用 .calcpack 查看器 — 加载计算包并渲染交互界面。"""

    def __init__(self, calcpack_path: str | None = None):
        super().__init__()
        self.setWindowTitle("计算包查看器")
        self.resize(1100, 750)

        self._loaded_data: dict[str, Any] = {}
        self._dag_service: DAGService | None = None
        self._layout: Layout | None = None
        self._variables: dict[str, DAGVariable] = {}
        self._theme: dict[str, Any] = {}
        self._data_files: dict[str, list[dict[str, Any]]] = {}
        self._compute_sheet: ComputeSheet | None = None
        self._entity_selectors: dict[str, QComboBox] = {}
        self._level_spin: QSpinBox | None = None
        self._current_level: int = 90
        self._entity_data: dict[str, dict[str, Any]] = {}

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self._build_menu()

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left = QWidget()
        self._left_layout = QVBoxLayout(left)
        self._left_layout.setContentsMargins(4, 4, 4, 4)
        self._entity_group = QGroupBox("选择实体")
        self._entity_form = QFormLayout(self._entity_group)
        self._left_layout.addWidget(self._entity_group)
        self._left_layout.addStretch()
        splitter.addWidget(left)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._sheet_container = QWidget()
        self._sheet_layout = QVBoxLayout(self._sheet_container)
        self._scroll.setWidget(self._sheet_container)
        splitter.addWidget(self._scroll)

        right = QWidget()
        self._right_layout = QVBoxLayout(right)
        self._right_layout.setContentsMargins(4, 4, 4, 4)
        self._info_group = QGroupBox("包信息")
        info_form = QFormLayout(self._info_group)
        self._info_name = QLabel("—")
        info_form.addRow("名称:", self._info_name)
        self._info_game = QLabel("—")
        info_form.addRow("游戏:", self._info_game)
        self._info_version = QLabel("—")
        info_form.addRow("版本:", self._info_version)
        self._info_vars = QLabel("—")
        info_form.addRow("变量:", self._info_vars)
        self._info_outputs = QLabel("—")
        info_form.addRow("输出:", self._info_outputs)
        self._right_layout.addWidget(self._info_group)
        self._right_layout.addStretch()
        splitter.addWidget(right)

        splitter.setSizes([220, 580, 200])
        main_layout.addWidget(splitter, stretch=1)

        bar = QStatusBar()
        self._status_label = QLabel("就绪 — 打开一个 .calcpack 文件开始使用")
        bar.addWidget(self._status_label)
        self._progress = QProgressBar()
        self._progress.setMaximumWidth(160)
        self._progress.setVisible(False)
        bar.addPermanentWidget(self._progress)
        self.setStatusBar(bar)

        if calcpack_path:
            path_copy = calcpack_path
            QTimer.singleShot(100, lambda p=path_copy: self.load_calcpack(p))

    def _build_menu(self) -> None:
        mb = self.menuBar()
        file_menu = mb.addMenu("文件")

        open_action = QAction("打开 .calcpack...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_file)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def _open_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "打开 .calcpack", "",
            "CalcPack (*.calcpack);;ZIP (*.zip);;All Files (*)",
        )
        if path:
            self.load_calcpack(path)

    def load_calcpack(self, path: str | Path) -> None:
        """加载 .calcpack 文件并渲染 UI。"""
        try:
            self._loaded_data = _load_calcpack(path)
        except Exception as e:
            QMessageBox.critical(self, "加载失败", str(e))
            return

        meta = self._loaded_data.get("meta.json", {})
        self._info_name.setText(meta.get("name", "—"))
        self._info_game.setText(meta.get("game", "—"))
        self._info_version.setText(meta.get("version", "—"))

        dag_data = self._loaded_data.get("dag/formula.dag.json")
        if not dag_data:
            QMessageBox.critical(self, "加载失败", ".calcpack 缺少 dag/formula.dag.json")
            return
        dag = dag_from_dict(dag_data)
        self._dag_service = DAGService(dag)
        self._variables = dag.variables

        layout_data = self._loaded_data.get("ui/layout.json")
        if not layout_data:
            QMessageBox.critical(self, "加载失败", ".calcpack 缺少 ui/layout.json")
            return
        self._layout = load_layout(layout_data)

        self._theme = self._loaded_data.get("ui/theme.json", {})

        self._data_files = {}
        for arcname, data in self._loaded_data.items():
            if arcname.startswith("data/") and isinstance(data, list):
                key = arcname.replace("data/", "").replace(".json", "")
                self._data_files[key] = data

        self._info_vars.setText(str(len(self._variables)))
        self._info_outputs.setText(str(len(dag.outputs)))

        self._rebuild_entity_selectors()
        self._rebuild_sheet()

        self._apply_theme()

        name = meta.get("name", Path(path).stem)
        self.setWindowTitle(f"{name} — 计算包查看器")
        self._status_label.setText(f"已加载 {name} ({len(self._variables)} 变量, {len(dag.outputs)} 输出)")

    def _rebuild_entity_selectors(self) -> None:
        while self._entity_form.count():
            item = self._entity_form.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        self._entity_selectors.clear()
        self._entity_data.clear()

        level_box = QSpinBox()
        level_box.blockSignals(True)
        level_box.setRange(1, 100)
        level_box.setValue(90)
        level_box.blockSignals(False)
        level_box.valueChanged.connect(self._on_entity_changed)
        self._level_spin = level_box
        self._entity_form.addRow("等级:", level_box)

        for source_prefix, data_key in _SOURCE_TO_DATA_FILE.items():
            entities = self._data_files.get(data_key, [])
            if not entities:
                continue
            names = [e.get("名称", f"未命名 {i}") for i, e in enumerate(entities)]
            combo = QComboBox()
            combo.blockSignals(True)
            combo.addItems(names)
            combo.setCurrentIndex(0)
            combo.blockSignals(False)
            combo.currentIndexChanged.connect(self._on_entity_changed)
            self._entity_selectors[source_prefix] = combo
            self._entity_data[source_prefix] = {
                n: e for n, e in zip(names, entities)
            }
            label = {"character": "角色", "weapon": "武器", "equipment": "装备"}.get(
                source_prefix, source_prefix
            )
            self._entity_form.addRow(f"{label}:", combo)

    def _rebuild_sheet(self) -> None:
        while self._sheet_layout.count():
            item = self._sheet_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if not self._dag_service or not self._layout:
            self._sheet_layout.addWidget(QLabel("请先打开一个 .calcpack 文件"))
            return

        base_context: dict[str, Any] = self._build_current_context()

        patched_vars: dict[str, DAGVariable] = {}
        for path, var in self._variables.items():
            source = var.source if hasattr(var, "source") else ""
            if source == "computed" and self._is_var_in_input_sections(path):
                parts = path.split(".", 1)
                field_name = parts[1] if len(parts) == 2 else ""
                fallback = _FALLBACK_DEFAULTS.get(field_name, 0.0)
                patched_vars[path] = DAGVariable(
                    type=var.type,
                    source="user_input",
                    description=var.description,
                    default=var.default if var.default is not None else fallback,
                    min=var.min,
                    max=var.max,
                )
            else:
                patched_vars[path] = var

        self._compute_sheet = ComputeSheet(
            dag_service=self._dag_service,
            layout=self._layout,
            variables=patched_vars,
            base_context=base_context,
            parent=self._sheet_container,
        )
        self._sheet_layout.addWidget(self._compute_sheet.widget)
        self._sheet_layout.addStretch()

        self._compute_sheet.evaluate()

    def _is_var_in_input_sections(self, path: str) -> bool:
        if not self._layout:
            return False
        for sec in self._layout.sections:
            if sec.type == "inputs" and path in sec.variables:
                return True
        return False

    def _build_current_context(self) -> dict[str, Any]:
        """根据当前选中的实体和等级构建 DAG context，缺失变量使用 0.0。"""
        ctx: dict[str, Any] = {}
        level = self._level_spin.value() if self._level_spin else 90
        for source_prefix, combo in self._entity_selectors.items():
            idx = combo.currentIndex()
            if idx < 0:
                continue
            name = combo.currentText()
            entity = self._entity_data.get(source_prefix, {}).get(name)
            if entity:
                ns = source_prefix
                ns_ctx = _build_context_from_entity(entity, ns, level)
                ctx[ns] = ns_ctx

        for path, var in self._variables.items():
            source = var.source if hasattr(var, "source") else ""
            parts = path.split(".", 1)
            if len(parts) != 2:
                continue
            ns, key = parts
            if ns not in ctx:
                ctx[ns] = {}
            if isinstance(ctx.get(ns), dict) and key not in ctx[ns]:
                default = var.default if var.default is not None else _FALLBACK_DEFAULTS.get(key, 0.0)
                ctx[ns][key] = default
        return ctx

    def _on_entity_changed(self) -> None:
        """当用户切换实体或更改等级时重新求值。"""
        if self._compute_sheet is None:
            return
        context = self._build_current_context()
        self._compute_sheet._base_context = context
        self._compute_sheet.evaluate()

        selected = []
        for src, combo in self._entity_selectors.items():
            if combo.currentIndex() >= 0:
                selected.append(f"{src}={combo.currentText()}")
        lv = self._level_spin.value() if self._level_spin else 90
        self._status_label.setText(
            f"已求值 — {', '.join(selected) if selected else '自定义输入'} Lv.{lv}"
        )

    def _apply_theme(self) -> None:
        if not self._theme:
            return
        try:
            colors = self._theme.get("colors", {})
            bg = colors.get("background", "#1E1E1E")
            surface = colors.get("surface", "#2D2D2D")
            text = colors.get("text", "#F0F0F0")
            self.setStyleSheet(f"""
                QMainWindow {{ background-color: {bg}; }}
                QGroupBox {{
                    background-color: {surface};
                    border: 1px solid {colors.get("border", "#3D3D3D")};
                    border-radius: 6px;
                    margin-top: 8px;
                    padding-top: 16px;
                    font-weight: bold;
                    color: {text};
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 2px 8px;
                    color: {text};
                }}
                QLabel {{ color: {text}; }}
                QComboBox, QSpinBox, QDoubleSpinBox {{
                    background-color: {surface};
                    color: {text};
                    border: 1px solid {colors.get("border", "#3D3D3D")};
                    border-radius: 4px;
                    padding: 2px 6px;
                }}
                QPushButton {{
                    background-color: {colors.get("primary", "#0078D4")};
                    color: {text};
                    border: none;
                    border-radius: 4px;
                    padding: 6px 16px;
                }}
                QPushButton:hover {{
                    opacity: 0.9;
                }}
                QScrollArea {{ background-color: {bg}; border: none; }}
                QSlider::groove:horizontal {{
                    background: {surface};
                    height: 6px;
                    border-radius: 3px;
                }}
                QSlider::handle:horizontal {{
                    background: {colors.get("primary", "#0078D4")};
                    width: 16px;
                    height: 16px;
                    margin: -5px 0;
                    border-radius: 8px;
                }}
            """)
            font_family = self._theme.get("font", {}).get("family", "")
            font_size = self._theme.get("font", {}).get("size", 0)
            if font_family:
                font = QFont(font_family, font_size or 12)
                self.setFont(font)
        except Exception:
            pass


def open_calcpack(path: str | Path) -> None:
    """便捷函数：加载并显示 .calcpack 文件。"""
    app = QApplication.instance() or QApplication([])
    viewer = CalcPackViewer()
    viewer.load_calcpack(path)
    viewer.show()


def main() -> None:
    """CLI 入口。

    用法::

        python -m calc_framework.ui.viewer [path/游戏名.calcpack]
    """
    import sys
    app = QApplication(sys.argv)
    app.setApplicationName("计算包查看器")

    path = sys.argv[1] if len(sys.argv) > 1 else None
    viewer = CalcPackViewer(path)

    if path:
        viewer.load_calcpack(path)

    viewer.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
