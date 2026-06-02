# SPDX-License-Identifier: AGPL-3.0
"""布局编辑器 QWidget — 可视化编排 DAG 变量到 layout.json Section。



交互模式：

- 加载 DAG JSON → 左侧显示可用输入变量和输出

- 中间：section 列表，可添加/删除/编辑每个 section 的变量和输出

- 底部：布局名称 + 导出/预览按钮

"""



from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ..dag.schema import DAGGraph
from ..dag.serializer import load_dag
from ..dag.service import DAGService
from ..ui.compute_sheet import ComputeSheet
from . import LayoutEditor


class _SectionWidget(QGroupBox):

    def __init__(

        self,

        section_id: str,

        section_type: str,

        title: str,

        available_inputs: list[str],

        available_outputs: list[str],

        selected_vars: list[str],

        selected_outs: list[str],

        on_remove: Any = None,

        on_changed: Any = None,

    ):

        super().__init__(title)

        self._section_id = section_id

        self._section_type = section_type

        self._available_inputs = available_inputs

        self._available_outputs = available_outputs

        self._on_remove = on_remove

        self._on_changed = on_changed



        layout = QVBoxLayout(self)



        header = QHBoxLayout()

        type_label = "输入" if section_type == "inputs" else "输出"

        header.addWidget(QLabel(f"类型: {type_label}"))

        header.addStretch()

        remove_btn = QPushButton("删除")

        remove_btn.setFixedWidth(60)

        remove_btn.clicked.connect(lambda: on_remove(section_id) if on_remove else None)

        header.addWidget(remove_btn)

        layout.addLayout(header)



        if section_type == "inputs":

            self._target_list = available_inputs

            self._selected = set(selected_vars)

            layout.addWidget(QLabel("变量:"))

        else:

            self._target_list = available_outputs

            self._selected = set(selected_outs)

            layout.addWidget(QLabel("输出:"))



        self._checkboxes: dict[str, QCheckBox] = {}

        for name in self._target_list:

            cb = QCheckBox(name)

            cb.setChecked(name in self._selected)

            cb.toggled.connect(self._on_toggled)

            self._checkboxes[name] = cb

            layout.addWidget(cb)



    def _on_toggled(self) -> None:

        if self._on_changed:

            self._on_changed()



    def selected_names(self) -> list[str]:

        return [name for name, cb in self._checkboxes.items() if cb.isChecked()]



    @property

    def section_id(self) -> str:

        return self._section_id



    @property

    def section_type(self) -> str:

        return self._section_type





class LayoutEditorWidget(QWidget):

    def __init__(self, parent: QWidget | None = None):

        super().__init__(parent)

        self._editor: LayoutEditor | None = None

        self._section_widgets: list[_SectionWidget] = []

        self._build_ui()



    def _build_ui(self) -> None:

        main_layout = QVBoxLayout(self)



        toolbar = QHBoxLayout()

        open_btn = QPushButton("加载 DAG")

        open_btn.clicked.connect(self._open_dag)

        toolbar.addWidget(open_btn)



        export_btn = QPushButton("导出 layout.json")

        export_btn.clicked.connect(self._export)

        toolbar.addWidget(export_btn)



        preview_btn = QPushButton("预览计算表")

        preview_btn.clicked.connect(self._preview)

        toolbar.addWidget(preview_btn)



        toolbar.addStretch()

        main_layout.addLayout(toolbar)



        splitter = QSplitter(Qt.Orientation.Horizontal)



        left = QWidget()

        left_layout = QVBoxLayout(left)

        left_layout.addWidget(QLabel("可用输入变量"))

        self._input_list = QListWidget()

        left_layout.addWidget(self._input_list)

        left_layout.addWidget(QLabel("可用输出"))

        self._output_list = QListWidget()

        left_layout.addWidget(self._output_list)

        splitter.addWidget(left)



        center = QWidget()

        center_layout = QVBoxLayout(center)

        center_layout.addWidget(QLabel("节列表"))



        add_btn_row = QHBoxLayout()

        self._section_title_input = QLineEdit()

        self._section_title_input.setPlaceholderText("节标题")

        add_btn_row.addWidget(self._section_title_input)

        add_inputs_btn = QPushButton("+ 输入节")

        add_inputs_btn.clicked.connect(lambda: self._add_section("inputs"))

        add_btn_row.addWidget(add_inputs_btn)

        add_outputs_btn = QPushButton("+ 输出节")

        add_outputs_btn.clicked.connect(lambda: self._add_section("outputs"))

        add_btn_row.addWidget(add_outputs_btn)

        center_layout.addLayout(add_btn_row)



        self._sections_container = QVBoxLayout()

        center_layout.addLayout(self._sections_container)

        center_layout.addStretch()

        splitter.addWidget(center)



        splitter.setSizes([250, 400])

        splitter.setStretchFactor(0, 1)

        splitter.setStretchFactor(1, 2)

        main_layout.addWidget(splitter, stretch=1)



        bottom = QHBoxLayout()

        bottom.addWidget(QLabel("布局名称:"))

        self._name_input = QLineEdit("计算布局")

        bottom.addWidget(self._name_input)

        bottom.addStretch()

        self._status_label = QLabel("")

        bottom.addWidget(self._status_label)

        main_layout.addLayout(bottom)



    def _open_dag(self) -> None:

        path, _ = QFileDialog.getOpenFileName(

            self, "选择 DAG JSON", "", "JSON Files (*.json);;All Files (*)"

        )

        if not path:

            return

        try:

            dag = load_dag(Path(path))

        except Exception as e:

            QMessageBox.critical(self, "错误", f"无法加载 DAG:\n{e}")

            return

        self._load_dag(dag, path)



    def _load_dag(self, dag: DAGGraph, _path: str = "") -> None:

        self._editor = LayoutEditor(dag=dag)

        self._refresh_lists()

        self._rebuild_sections()

        self._status_label.setText(f"已加载 {dag.name or 'DAG'}")



    def _refresh_lists(self) -> None:

        if not self._editor:

            return

        self._input_list.clear()

        for v in self._editor.available_input_vars:

            item = QListWidgetItem(v)

            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)

            self._input_list.addItem(item)

        self._output_list.clear()

        for o in self._editor.available_outputs:

            item = QListWidgetItem(o)

            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)

            self._output_list.addItem(item)



    def _rebuild_sections(self) -> None:

        while self._sections_container.count():

            child = self._sections_container.takeAt(0)

            if child.widget():

                child.widget().deleteLater()

        self._section_widgets.clear()



        if not self._editor:

            return



        for sec in self._editor.state.sections:

            sw = _SectionWidget(

                section_id=sec.id,

                section_type=sec.type,

                title=sec.title,

                available_inputs=self._editor.available_input_vars,

                available_outputs=self._editor.available_outputs,

                selected_vars=sec.variables,

                selected_outs=sec.outputs,

                on_remove=self._remove_section,

                on_changed=self._sync_sections,

            )

            self._sections_container.addWidget(sw)

            self._section_widgets.append(sw)



    def _add_section(self, sec_type: str) -> None:

        if not self._editor:

            return

        title = self._section_title_input.text().strip()

        if not title:

            title = "输入节" if sec_type == "inputs" else "输出节"

        sec_id = f"section_{len(self._editor.state.sections) + 1}"

        self._editor.add_section(sec_id, type=sec_type, title=title)

        self._rebuild_sections()



    def _remove_section(self, sec_id: str) -> None:

        if self._editor:

            self._editor.remove_section(sec_id)

        self._rebuild_sections()



    def _sync_sections(self) -> None:

        if not self._editor:

            return

        for sw in self._section_widgets:

            names = sw.selected_names()

            if sw.section_type == "inputs":

                self._editor.set_section_variables(sw.section_id, names)

            else:

                self._editor.set_section_outputs(sw.section_id, names)



    def _export(self) -> None:

        if not self._editor:

            QMessageBox.warning(self, "警告", "请先加载 DAG")

            return

        self._editor.set_name(self._name_input.text().strip() or "计算布局")

        path, _ = QFileDialog.getSaveFileName(

            self, "导出 layout.json", "layout.json", "JSON Files (*.json)"

        )

        if not path:

            return

        try:

            self._editor.export(path)

            self._status_label.setText(f"已导出 → {path}")

        except Exception as e:

            QMessageBox.critical(self, "导出失败", str(e))



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

        preview.resize(500, 400)

        preview_layout = QVBoxLayout(preview)



        try:

            service = DAGService(self._editor.dag)

            sheet = ComputeSheet(

                dag_service=service,

                layout=layout,

                variables={},

                base_context={},

                parent=preview,

            )

            preview_layout.addWidget(sheet.widget)

        except Exception as e:

            preview_layout.addWidget(QLabel(f"渲染失败: {e}"))



        preview.show()

        self._last_preview_result = preview



    def load_dag_file(self, path: str) -> None:

        dag = load_dag(Path(path))

        self._load_dag(dag, path)



    def load_layout_file(self, dag_path: str, layout_path: str) -> None:

        editor = LayoutEditor.from_layout(dag_path, layout_path)

        self._editor = editor

        self._name_input.setText(editor.state.layout_name)

        self._refresh_lists()

        self._rebuild_sections()

        self._status_label.setText(f"已加载 {editor.state.layout_name}")

