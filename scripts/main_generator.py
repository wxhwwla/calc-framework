#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""AI 计算器生成器 — 桌面版。

用法::

    python scripts/main_generator.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _path_setup import ensure_root

ensure_root()

from tools.generator import GeneratorEngine


class GeneratorWindow(QMainWindow):
    """AI 计算器生成器主窗口。"""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AI 计算器生成器")
        self.resize(1000, 700)
        self.engine = GeneratorEngine()
        self._result_files: dict[str, str] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        splitter = QSplitter(Qt.Horizontal)

        # ── 左侧：模板列表 ──────────────────────────────
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(QLabel("品类模板"))
        self.template_list = QListWidget()
        self.template_list.itemClicked.connect(self._on_template_selected)
        left_layout.addWidget(self.template_list)
        splitter.addWidget(left_widget)

        # ── 中间：游戏信息 ──────────────────────────────
        mid_widget = QWidget()
        mid_layout = QVBoxLayout(mid_widget)
        mid_layout.setContentsMargins(0, 0, 0, 0)

        info_group = QGroupBox("游戏信息")
        info_layout = QVBoxLayout(info_group)
        self.game_name_input = QLineEdit()
        self.game_name_input.setPlaceholderText("输入游戏名称")
        info_layout.addWidget(self.game_name_input)
        mid_layout.addWidget(info_group)

        self.template_info = QTextEdit()
        self.template_info.setReadOnly(True)
        self.template_info.setPlaceholderText("选择模板后显示详情")
        mid_layout.addWidget(self.template_info)

        self.generate_btn = QPushButton("生成计算器")
        self.generate_btn.clicked.connect(self._on_generate)
        self.generate_btn.setEnabled(False)
        mid_layout.addWidget(self.generate_btn)

        splitter.addWidget(mid_widget)

        # ── 右侧：结果 ──────────────────────────────────
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(QLabel("生成结果"))
        self.result_view = QTextEdit()
        self.result_view.setReadOnly(True)
        self.result_view.setPlaceholderText("生成后显示文件列表")
        right_layout.addWidget(self.result_view)

        self.export_btn = QPushButton("导出到目录")
        self.export_btn.clicked.connect(self._on_export)
        self.export_btn.setEnabled(False)
        right_layout.addWidget(self.export_btn)

        splitter.addWidget(right_widget)

        splitter.setSizes([200, 350, 450])
        layout.addWidget(splitter)

        self._load_templates()

    # ── 数据方法 ──────────────────────────────────────

    def _load_templates(self) -> None:
        templates = self.engine.list_templates()
        for tid, info in templates.items():
            item = QListWidgetItem(f"{info['name']}\n({info['description']})")
            item.setData(Qt.UserRole, tid)
            item.setToolTip(info['description'])
            self.template_list.addItem(item)

    def _on_template_selected(self, item: QListWidgetItem) -> None:
        tid = item.data(Qt.UserRole)
        from tools.generator.templates import load_template

        try:
            template = load_template(tid)
            meta = template.get("meta", {})
            dag = template.get("dag", {})
            self.template_info.setPlainText(
                f"名称: {meta.get('name', '?')}\n"
                f"游戏: {meta.get('game', '?')}\n"
                f"描述: {meta.get('description', '')}\n"
                f"DAG 节点: {len(dag.get('nodes', {})) if dag else 0}\n"
                f"DAG 输出: {len(dag.get('outputs', {})) if dag else 0}\n"
            )
            self.generate_btn.setEnabled(True)
        except Exception as e:
            self.template_info.setPlainText(f"加载失败: {e}")

    def _on_generate(self) -> None:
        tid_item = self.template_list.currentItem()
        if not tid_item:
            return
        tid = tid_item.data(Qt.UserRole)
        game_name = self.game_name_input.text().strip()
        if not game_name:
            QMessageBox.warning(self, "提示", "请输入游戏名称")
            return

        try:
            files = self.engine.generate(tid, game_name)
            self._result_files = files
            preview = f"生成成功！共 {len(files)} 个文件\n\n"
            for fname, content in files.items():
                lines = content.count("\n") + 1
                preview += f"  {fname} ({lines} 行)\n"
            self.result_view.setPlainText(preview)
            self.export_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "生成失败", str(e))

    def _on_export(self) -> None:
        if not self._result_files:
            return
        dir_path = QFileDialog.getExistingDirectory(self, "选择导出目录")
        if not dir_path:
            return
        try:
            out = Path(dir_path)
            for filepath, content in self._result_files.items():
                fp = out / filepath
                fp.parent.mkdir(parents=True, exist_ok=True)
                fp.write_text(content, encoding="utf-8")
            QMessageBox.information(
                self, "导出成功",
                f"已导出 {len(self._result_files)} 个文件到:\n{dir_path}",
            )
        except Exception as e:
            QMessageBox.critical(self, "导出失败", str(e))


def main() -> None:
    app = QApplication(sys.argv)
    window = GeneratorWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
