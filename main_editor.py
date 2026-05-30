#!/usr/bin/env python3
"""
布局编辑器 — 独立入口（终末地数据支持版）

可视化编排 DAG 变量到 layout.json 节。
内置终末地角色/武器数据加载，预览时可直接求值。

使用方式：
    python main_editor.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QFont, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QMenuBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

_REPO_ROOT = Path(__file__).resolve().parent
_FRAMEWORK_SRC = _REPO_ROOT / "framework" / "src"
if str(_FRAMEWORK_SRC) not in sys.path:
    sys.path.insert(0, str(_FRAMEWORK_SRC))

_GAMES_DIR = _REPO_ROOT / "games" / "endfield"
if str(_GAMES_DIR) not in sys.path:
    sys.path.insert(0, str(_GAMES_DIR))

_DAG_PATH = _FRAMEWORK_SRC / "calc_framework" / "configs" / "endfield_full.dag.json"

from calc_framework.dag.schema import DAGGraph
from calc_framework.dag.serializer import load_dag
from calc_framework.dag.service import DAGService
from calc_framework.editor.gui import LayoutEditorWidget
from calc_framework.ui.compute_sheet import ComputeSheet
from calc_framework.ui.layout import load_layout
from utils.gui_help_dialog import HelpSection

APP_NAME = "布局编辑器"
APP_VERSION = "1.0.0"


def _load_json(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


class EndfieldLayoutEditor(LayoutEditorWidget):
    """终末地数据增强的布局编辑器。

    在继承 LayoutEditorWidget 的基础上，增加角色/武器选择器和数据加载，
    使预览功能能使用真实数据求值。
    """

    def __init__(
        self,
        dag_path: Path,
        characters: list[dict[str, Any]],
        weapons: list[dict[str, Any]],
        parent: QWidget | None = None,
    ):
        self._characters = characters
        self._weapons = weapons
        self._dag_path = dag_path
        self._ed_char_index = 0
        self._ed_weapon_index = 0
        self._ed_char_level = 80
        self._ed_weapon_level = 80
        self._ed_trust_level = 0
        self._data_panel: QWidget | None = None
        self._char_combo: QComboBox | None = None
        self._weapon_combo: QComboBox | None = None

        super().__init__(parent)

    def _build_ui(self) -> None:
        super()._build_ui()

        self._data_panel = QGroupBox("终末地数据预览")
        data_layout = QFormLayout(self._data_panel)

        self._char_combo = QComboBox()
        for c in self._characters:
            self._char_combo.addItem(c.get("名称", "?"))
        self._char_combo.currentIndexChanged.connect(self._on_char_changed)
        data_layout.addRow("角色:", self._char_combo)

        self._weapon_combo = QComboBox()
        for w in self._weapons:
            self._weapon_combo.addItem(w.get("名称", "?"))
        self._weapon_combo.currentIndexChanged.connect(self._on_weapon_changed)
        data_layout.addRow("武器:", self._weapon_combo)

        level_row = QHBoxLayout()
        self._char_level_spin = QSpinBox()
        self._char_level_spin.setRange(1, 90)
        self._char_level_spin.setValue(80)
        self._char_level_spin.valueChanged.connect(lambda v: setattr(self, "_ed_char_level", v))
        level_row.addWidget(QLabel("角色等级:"))
        level_row.addWidget(self._char_level_spin)

        self._weapon_level_spin = QSpinBox()
        self._weapon_level_spin.setRange(1, 90)
        self._weapon_level_spin.setValue(80)
        self._weapon_level_spin.valueChanged.connect(lambda v: setattr(self, "_ed_weapon_level", v))
        level_row.addWidget(QLabel("武器等级:"))
        level_row.addWidget(self._weapon_level_spin)

        self._trust_spin = QSpinBox()
        self._trust_spin.setRange(0, 200)
        self._trust_spin.setValue(0)
        self._trust_spin.valueChanged.connect(lambda v: setattr(self, "_ed_trust_level", v))
        level_row.addWidget(QLabel("信赖:"))
        level_row.addWidget(self._trust_spin)
        data_layout.addRow(level_row)

        reload_btn = QPushButton("加载 DAG")
        reload_btn.clicked.connect(self._load_default_dag)
        data_layout.addRow(reload_btn)

        self.layout().insertWidget(0, self._data_panel)

    def _on_char_changed(self, idx: int) -> None:
        self._ed_char_index = idx
        self._status_label.setText(f"已选择: {self._char_combo.currentText()}")

    def _on_weapon_changed(self, idx: int) -> None:
        self._ed_weapon_index = idx

    def _load_default_dag(self) -> None:
        dag = load_dag(self._dag_path)
        self._load_dag(dag, str(self._dag_path))
        self._status_label.setText(f"DAG 已加载: {self._dag_path.name}")

    def _preview(self) -> None:
        if not self._editor:
            QMessageBox.warning(self, "警告", "请先加载 DAG")
            return

        self._sync_sections()
        self._editor.set_name(self._name_input.text().strip() or "计算布局")
        layout = self._editor.state.to_layout()

        try:
            last_result = getattr(self, "_last_preview_result", None)
            if last_result:
                last_result.close()
        except Exception:
            pass

        preview = QWidget()
        preview.setWindowTitle(f"预览: {layout.name}")
        preview.resize(700, 500)
        preview_layout = QVBoxLayout(preview)

        try:
            char = self._characters[self._ed_char_index]
            weapon = self._weapons[self._ed_weapon_index]

            from adapters.endfield.calc.multiplicative_zones.dag.loader import (
                EndfieldContextLoader,
            )

            loader = EndfieldContextLoader()
            base_context = loader.build_context(
                character=char,
                weapon=weapon,
                char_level=self._ed_char_level,
                weapon_level=self._ed_weapon_level,
                trust_level=self._ed_trust_level,
            )

            service = DAGService(self._editor.dag)
            sheet = ComputeSheet(
                dag_service=service,
                layout=layout,
                variables={},
                base_context=base_context,
                parent=preview,
            )
            preview_layout.addWidget(sheet.widget)
        except Exception as e:
            preview_layout.addWidget(QLabel(f"渲染预览失败: {e}"))
            import traceback
            traceback.print_exc()

        preview.show()
        self._last_preview_result = preview


class LayoutEditorApp(QMainWindow):
    """布局编辑器主窗口。"""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)

        self._setup_menu()

        self.big_font = QFont()
        self.big_font.setPointSize(14)
        self.big_font.setBold(True)

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QLabel(f"  {APP_NAME} v{APP_VERSION}")
        header.setFixedHeight(36)
        header.setFont(self.big_font)
        header.setStyleSheet("background: #2d2d2d; color: #eee; padding-left: 12px;")
        header.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(header)

        characters = _load_json(
            _REPO_ROOT / "adapters" / "endfield" / "data" / "characters.json"
        )
        weapons = _load_json(
            _REPO_ROOT / "adapters" / "endfield" / "data" / "weapons.json"
        )

        self.editor = EndfieldLayoutEditor(
            dag_path=_DAG_PATH,
            characters=characters,
            weapons=weapons,
        )
        self.editor._load_default_dag()
        layout.addWidget(self.editor, 1)

    def _setup_menu(self) -> None:
        menubar = self.menuBar()
        help_menu = menubar.addMenu("帮助(&H)")
        help_action = QAction("使用说明(&U)", self)
        help_action.setShortcut(QKeySequence("F1"))
        help_action.triggered.connect(self._show_help)
        help_menu.addAction(help_action)

    def _show_help(self) -> None:
        from utils.gui_help_dialog import HelpDialog
        sections = self._build_layout_editor_help()
        dialog = HelpDialog(lambda: sections, self, title="布局编辑器 使用说明")
        dialog.exec()

    @staticmethod
    def _build_layout_editor_help() -> list[HelpSection]:
        return [
            HelpSection(
                category="入门",
                title="概述",
                content="""\
<h2>布局编辑器</h2>

<p>布局编辑器是一个可视化编排工具，用于管理 DAG 变量到 Layout Section 的映射。<br>
同时内置终末地角色/武器数据支持，可进行实时 DAG 求值和预览。</p>

<h3>主要功能</h3>
<ul>
<li>可视化编排 DAG 变量到 Section</li>
<li>角色/武器选择与实时 DAG 求值预览</li>
<li>导出 layout.json 配置文件</li>
<li>布局自动平衡（均匀分配变量到各 Section）</li>
</ul>

<h3>工作流程</h3>
<ol>
<li>选择角色和武器（可选，用于预览求值）</li>
<li>查看 DAG 变量列表</li>
<li>将变量拖拽分配到不同 Section</li>
<li>点击「导出 layout.json」保存配置文件</li>
</ol>
""",
            ),
            HelpSection(
                category="界面",
                title="界面说明",
                content="""\
<h2>界面说明</h2>

<h3>标题栏</h3>
<p>显示应用名称和版本号。</p>

<h3>DAG 编辑器主体</h3>
<p>由 LayoutEditorWidget 提供核心功能，包含：</p>
<ul>
<li><b>角色/武器选择</b> — 选择角色和武器进行实时 DAG 求值预览</li>
<li><b>变量列表</b> — 显示所有 DAG 变量，可拖拽到 Section 中</li>
<li><b>Section 面板</b> — 可视化编排变量的分组</li>
<li><b>预览面板</b> — 当前约束下 DAG 的求值结果</li>
</ul>

<h3>工具栏</h3>
<ul>
<li><b>导出 layout.json</b> — 保存 Section 编排结果</li>
<li><b>加载 layout.json</b> — 载入已有的编排配置</li>
<li><b>自动平衡</b> — 自动将变量均匀分配到各 Section</li>
</ul>
""",
            ),
            HelpSection(
                category="操作",
                title="操作说明",
                content="""\
<h2>操作说明</h2>

<h3>选择角色/武器</h3>
<p>在顶部下拉框中选择角色和武器。选择后：</p>
<ul>
<li>系统自动加载对应的 DAG 数据</li>
<li>预览面板会显示基于当前选角的求值结果</li>
<li>变量值随角色/武器切换而变化</li>
</ul>

<h3>编排 Section</h3>
<ul>
<li><b>创建 Section</b> — 点击「新建 Section」按钮</li>
<li><b>分配变量</b> — 从变量列表拖拽变量到 Section 中</li>
<li><b>重命名 Section</b> — 双击 Section 标题编辑名称</li>
<li><b>删除 Section</b> — 右键或点击删除按钮</li>
</ul>

<h3>导出配置</h3>
<p>编排完成后，点击「导出 layout.json」按钮保存配置。<br>
导出的文件可以在计算器中使用。</p>
""",
            ),
            HelpSection(
                category="常见问题",
                title="使用技巧",
                content="""\
<h2>使用技巧</h2>

<ul>
<li>先在角色/武器选择中选定目标，再编排 Section，可以看到变量实际值</li>
<li>「自动平衡」功能适合初始编排，后续再手动微调</li>
<li>导出前可以先「预览」，确认结果是否正确</li>
</ul>
""",
            ),
        ]


def main() -> None:
    app = QApplication(sys.argv)
    window = LayoutEditorApp()
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
