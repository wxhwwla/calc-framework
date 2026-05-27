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
from calc_framework.ui.controls import ControlSpec, infer_control
from calc_framework.ui.format import format_node_value
from calc_framework.ui.layout import Layout, Section


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
    ):
        super().__init__(parent)
        self._dag_service = dag_service
        self._layout = layout
        self._variables = variables
        self._base_context = base_context or {}
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
        context = dict(self._base_context)

        for path, var in self._variables.items():
            vd = _var_to_dict(var)
            source = vd.get("source", "")
            if source == "user_input":
                value = self._read_input(path)
                parts = path.split(".", 1)
                if len(parts) == 2:
                    context.setdefault(parts[0], {})[parts[1]] = value

        result = self._dag_service.evaluate(context)
        self._update_outputs(result)
        self.evaluated.emit(result)
        return result

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

        eval_btn = QPushButton("计算")
        eval_btn.clicked.connect(self.evaluate)
        root_layout.addWidget(eval_btn)

        root_layout.addStretch()
        return root

    def _build_input_section(self, sec: Section) -> QWidget:
        group = QGroupBox(sec.title)
        grid = QGridLayout(group)
        grid.setColumnStretch(1, 1)

        for i, var_path in enumerate(sec.variables):
            raw_var = self._variables.get(var_path, {})
            var = _var_to_dict(raw_var) if raw_var else {}
            spec = infer_control(var_path, var)
            if spec.widget == "none":
                continue

            label = QLabel(spec.label)
            label.setToolTip(spec.description)
            grid.addWidget(label, i, 0)

            widget = self._create_control(spec)
            if widget is not None:
                grid.addWidget(widget, i, 1)
                self._input_widgets[var_path] = (widget, spec)

        return group

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
