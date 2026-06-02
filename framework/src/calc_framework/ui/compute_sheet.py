# SPDX-License-Identifier: AGPL-3.0
"""ComputeSheet QWidget — 声明式计算表组件。



将 DAG 公式图 + layout.json 排版渲染为可交互的 PySide6 控件树。

"""



from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from calc_framework.dag.engine import DAGResult
from calc_framework.dag.schema import DAGVariable
from calc_framework.dag.service import DAGService
from calc_framework.logging import get_logger
from calc_framework.ui.controls import ControlSpec, infer_control
from calc_framework.ui.format import format_node_value
from calc_framework.ui.layout import Layout, Section

logger = get_logger(__name__)



_AVG_ITEM_WIDTH = 280





class _ResponsiveGroupBox(QGroupBox):

    """QGroupBox 子类，根据可用宽度自动重排行内 input 项。"""



    def __init__(

        self,

        title: str,

        items: list[tuple[str, QLabel, QWidget | None, ControlSpec]],

        parent: QWidget | None = None,

    ) -> None:

        super().__init__(title, parent)

        self._items = items

        self._grid = QGridLayout(self)

        self._grid.setColumnStretch(1, 1)



    def _on_resized(self) -> None:

        available = self.width() - 40

        cols = max(1, available // _AVG_ITEM_WIDTH)

        cols = cols * 2  # each item takes 2 columns (label + widget)



        while self._grid.count():

            item = self._grid.takeAt(0)

            w = item.widget()

            if w:

                w.setParent(None)



        for i, (_var_path, label, widget, spec) in enumerate(self._items):

            row = i // (cols // 2)

            col_offset = (i % (cols // 2)) * 2

            self._grid.addWidget(label, row, col_offset)

            if widget is not None:

                self._grid.addWidget(widget, row, col_offset + 1)



    def resizeEvent(self, event) -> None:

        super().resizeEvent(event)

        self._on_resized()





def _var_to_dict(var: DAGVariable | dict[str, Any]) -> dict[str, Any]:

    if isinstance(var, dict):

        return var

    return {

        "type": var.type,

        "source": var.source,

        "description": var.description,

        "default": var.default,

        "min": var.min,

        "max": var.max,

    }





class ComputeSheet(QObject):

    value_changed = Signal(str, object)

    evaluated = Signal(object)



    def __init__(

        self,

        dag_service: DAGService,

        layout: Layout,

        variables: dict[str, DAGVariable],

        base_context: dict[str, Any] | None = None,

        parent: QWidget | None = None,

        user_context_overrides: dict[str, tuple[str, list[str]]] | None = None,

    ):

        """user_context_overrides: {user_input_var_path: (target_dotted_path, [merge_keys])}

        将 user_input 变量的值合并到 DAG context 的目标路径下。

        示例:

          "user_input.敌人防御" → ("enemy.防御", ["override"])

            → 用 user_input 值直接覆盖 enemy.防御

          "user_input.额外暴击率" → ("character.暴击率", ["add"])

            → 将 user_input 值加到 character.暴击率上

        """

        super().__init__(parent)

        self._dag_service = dag_service

        self._layout = layout

        self._variables = variables

        self._base_context = base_context or {}

        self._user_context_overrides = user_context_overrides or {}

        self._context_overrides: dict[str, Any] = {}

        self._widget: QWidget | None = None

        self._output_labels: dict[str, QLabel] = {}

        self._input_widgets: dict[str, tuple[QWidget, ControlSpec]] = {}

        self._output_formats: dict[str, str] = {

            oid: odef.format

            for oid, odef in dag_service.dag.outputs.items()

            if odef.format

        }



    @property

    def widget(self) -> QWidget:

        if self._widget is None:

            self._widget = self._build()

        return self._widget



    def evaluate(self) -> DAGResult:

        logger.debug("ComputeSheet 求值开始: %d 个输出, %d 个变量",

                      len(self._dag_service.dag.outputs), len(self._variables))

        context = dict(self._base_context)



        user_values: dict[str, float] = {}

        for path, var in self._variables.items():

            vd = _var_to_dict(var)

            source = vd.get("source", "")

            if source == "user_input":

                value = self._read_input(path)

                parts = path.split(".", 1)

                if len(parts) == 2:

                    context.setdefault(parts[0], {})[parts[1]] = value

                user_values[path] = value



        for user_path, (target_path, merge_keys) in self._user_context_overrides.items():

            uv = user_values.get(user_path)

            if uv is None:

                continue

            parts = target_path.split(".", 1)

            if len(parts) != 2:

                continue

            ns, key = parts

            for mk in merge_keys:

                if mk == "override":

                    context.setdefault(ns, {})[key] = uv

                elif mk == "add":

                    current = context.get(ns, {}).get(key, 0.0)

                    context.setdefault(ns, {})[key] = current + uv



        for path, value in self._context_overrides.items():

            parts = path.split(".", 1)

            if len(parts) == 2:

                context.setdefault(parts[0], {})[parts[1]] = value



        result = self._dag_service.evaluate(context)

        self._update_outputs(result)

        self.evaluated.emit(result)

        return result



    def read_user_inputs(self) -> dict[str, Any]:

        """读取所有 user_input 类型变量的当前值（用于调用方合并到 DAG context）。"""

        result: dict[str, Any] = {}

        for path, raw_var in self._variables.items():

            vd = _var_to_dict(raw_var) if raw_var else {}

            if vd.get("source") == "user_input":

                result[path] = self._read_input(path)

        return result



    def set(self, key: str, value: Any) -> None:

        """向 DAG context 设置一个变量值。"""

        self._context_overrides[key] = value



    def render_html(self) -> str:

        """将当前输出面板渲染为 HTML 表格。"""

        parts: list[str] = ['<table style="width:100%;border-collapse:collapse;">']

        for sec in self._layout.sections:

            if sec.type != "outputs":

                continue

            parts.append(f'<tr style="background:#2B6CB6;color:white;">'

                         f'<td colspan="2" style="padding:4px 8px;font-weight:bold;">'

                         f'{sec.title}</td></tr>')

            for out_name in sec.outputs:

                label = self._output_labels.get(out_name)

                val = label.text() if label else "--"

                parts.append(f'<tr>' + (f'<td style="padding:2px 8px;">{out_name}</td>'

                                         f'<td style="padding:2px 8px;text-align:right;">{val}</td>'

                                         f'</tr>'))

        parts.append('</table>')

        return "\n".join(parts)



    def _read_input(self, path: str) -> Any:

        entry = self._input_widgets.get(path)

        if entry is None:

            raw_var = self._variables.get(path)

            if raw_var is None:

                return 0

            vd = _var_to_dict(raw_var)

            return vd.get("default", 0)

        w, spec = entry

        if isinstance(w, QSlider):

            val = w.value()

            if spec.step < 1:

                return val / 100.0

            return val

        if isinstance(w, QDoubleSpinBox):

            return w.value()

        if isinstance(w, QSpinBox):

            return w.value()

        if isinstance(w, QCheckBox):

            return w.isChecked()

        if isinstance(w, QComboBox):

            return w.currentText()

        if isinstance(w, QLineEdit):

            try:

                return float(w.text())

            except ValueError:

                return 0.0

        return 0



    def _update_outputs(self, result: DAGResult) -> None:

        for sec in self._layout.sections:

            if sec.type != "outputs":

                continue

            for out_name in sec.outputs:

                label = self._output_labels.get(out_name)

                if label is None:

                    continue

                value = result.outputs.get(out_name)

                fmt = self._output_formats.get(out_name, ".4f")

                label.setText(format_node_value(value, fmt))



    def _build(self) -> QWidget:

        root = QWidget()

        root_layout = QVBoxLayout(root)

        root_layout.setContentsMargins(0, 0, 0, 0)



        for sec in self._layout.sections:

            if sec.type == "inputs":

                root_layout.addWidget(self._build_input_section(sec))

            elif sec.type == "outputs":

                root_layout.addWidget(self._build_output_section(sec))

            elif sec.type == "widget":

                root_layout.addWidget(self._build_widget_section(sec))



        eval_btn = QPushButton("计算")

        eval_btn.clicked.connect(self.evaluate)

        root_layout.addWidget(eval_btn)



        root_layout.addStretch()

        return root



    def _collect_input_items(self, sec: Section) -> list[tuple[str, QLabel, QWidget | None, ControlSpec]]:

        """收集 section 中的 input 项，用于响应式重排。"""

        items: list[tuple[str, QLabel, QWidget | None, ControlSpec]] = []

        for var_path in sec.variables:

            raw_var = self._variables.get(var_path, {})

            var = _var_to_dict(raw_var) if raw_var else {}

            spec = infer_control(var_path, var)

            if spec.widget == "none":

                continue

            label = QLabel(spec.label)

            label.setToolTip(spec.description)

            widget = self._create_control(spec)

            items.append((var_path, label, widget, spec))

        return items



    def _build_input_section(self, sec: Section) -> QWidget:

        items = self._collect_input_items(sec)

        for var_path, _, widget, spec in items:

            if widget is not None:

                self._input_widgets[var_path] = (widget, spec)

        container = _ResponsiveGroupBox(sec.title, items)

        container._on_resized()

        return container



    def _build_output_section(self, sec: Section) -> QWidget:

        group = QGroupBox(sec.title)

        layout = QVBoxLayout(group)

        grid = QGridLayout()



        for i, out_name in enumerate(sec.outputs):

            label = QLabel(out_name)

            value_label = QLabel("--")

            value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

            grid.addWidget(label, i, 0)

            grid.addWidget(value_label, i, 1)

            self._output_labels[out_name] = value_label



        layout.addLayout(grid)

        return group



    def _build_widget_section(self, sec: Section) -> QWidget:

        if sec.widget_type == "donation":

            from utils.gui.donation import DONATION_IMAGE_PATH, DonationWidget

            cfg = sec.widget_config

            group = QGroupBox(sec.title)

            layout = QVBoxLayout(group)

            layout.setContentsMargins(0, 0, 0, 0)

            layout.addWidget(DonationWidget(

                text=cfg.get("text", "感谢使用！如果觉得有用，欢迎支持开发者。"),

                image_path=cfg.get("image_path") or DONATION_IMAGE_PATH,

                parent=group,

            ))

            return group

        group = QGroupBox(sec.title)

        layout = QVBoxLayout(group)

        layout.addWidget(QLabel(f"未知组件: {sec.widget_type}"))

        return group



    def _create_control(self, spec: ControlSpec) -> QWidget | None:

        if spec.widget == "slider":

            return self._make_slider(spec)

        if spec.widget == "spinbox":

            return self._make_spinbox(spec)

        if spec.widget == "switch":

            return self._make_checkbox(spec)

        if spec.widget == "dropdown":

            return self._make_dropdown(spec)

        return None



    def _make_slider(self, spec: ControlSpec) -> QWidget:

        min_v = int(spec.min_val or 0)

        max_v = int(spec.max_val or 100)

        if spec.step < 1:

            min_v = int(min_v * 100)

            max_v = int(max_v * 100)

            slider = QSlider(Qt.Horizontal)

            slider.setRange(min_v, max_v)

            slider.setValue(int(float(spec.default) * 100))

            slider.setSingleStep(max(1, int(spec.step * 100)))

        else:

            slider = QSlider(Qt.Horizontal)

            slider.setRange(min_v, max_v)

            slider.setValue(int(spec.default))

            slider.setSingleStep(int(spec.step))

        return slider



    def _make_spinbox(self, spec: ControlSpec) -> QWidget:

        if isinstance(spec.default, int) or spec.step == 1:

            box = QSpinBox()

            box.setValue(int(spec.default))

            box.setSingleStep(int(spec.step))

        else:

            box = QDoubleSpinBox()

            box.setValue(float(spec.default))

            box.setSingleStep(spec.step)

            box.setDecimals(max(0, -int(spec.step).bit_length() if spec.step < 1 else 2))

        if spec.min_val is not None:

            box.setMinimum(spec.min_val)  # type: ignore[reportArgumentType]

        if spec.max_val is not None:

            box.setMaximum(spec.max_val)  # type: ignore[reportArgumentType]

        return box



    def _make_checkbox(self, spec: ControlSpec) -> QWidget:

        cb = QCheckBox()

        cb.setChecked(bool(spec.default))

        return cb



    def _make_dropdown(self, spec: ControlSpec) -> QWidget:

        combo = QComboBox()

        combo.addItems(spec.options)

        default_idx = combo.findText(str(spec.default))

        if default_idx >= 0:

            combo.setCurrentIndex(default_idx)

        return combo

