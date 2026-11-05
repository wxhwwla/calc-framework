# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""ComputeSheet QWidget — 声明式计算表组件。

将 DAG 公式图 + layout.json 排版渲染为可交互的 PySide6 控件树。

ComputeSheet 类的胶水代码，控件生成委托给 sheet_widgets，求值逻辑委托给 sheet_evaluator。
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..dag.engine import DAGResult
from ..dag.schema import DAGVariable
from ..dag.service import DAGService
from ..logging import get_logger
from .controls import ControlSpec, infer_control
from .layout import Layout, Section
from .sheet_evaluator import build_context, var_to_dict
from .sheet_evaluator import read_input as _do_read_input
from .sheet_evaluator import render_html as _do_render_html
from .sheet_evaluator import update_outputs as _do_update_outputs
from .sheet_widgets import _ResponsiveGroupBox, create_control

logger = get_logger(__name__)

# 后处理钩子：(合并后的 context, 当前 user_input 值) -> context
ContextTransform = Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]

# 变量路径中不应展示给用户的代码前缀（按最长前缀优先匹配）。
_CODE_PREFIXES: tuple[str, ...] = (
    "user_input.",
    "computed.",
    "character.",
    "equipment.",
    "mothership.",
    "weapon.",
    "enemy.",
    "ship.",
    "user.",
    "buff.",
)


def display_text(path: str) -> str:
    """把变量路径转换为用户可读的标签。

    DAG 未提供 ``description`` / ``label`` 时，直接展示 ``user_input.敌人防御``
    这类路径会暴露代码命名。先去掉已知前缀；纯英文路径再把下划线换成空格，
    中文路径保持原样。

    Args:
        path: DAG 变量路径或输出名。

    Returns:
        去掉代码前缀后的显示文本。
    """
    text = path
    for prefix in _CODE_PREFIXES:
        if text.startswith(prefix):
            text = text[len(prefix) :]
            break
    has_cjk = any(0x4E00 <= ord(char) <= 0x9FFF for char in text)
    if "_" in text and not has_cjk:
        text = text.replace("_", " ")
    return text


class ComputeSheet(QObject):
    """声明式计算表主控制器。

    管理 DAGService 与 layout.json 的生命周期，暴露 widget 属性供嵌入。
    """

    value_changed = Signal(str, object)
    evaluated = Signal(object)

    def __init__(
        self,
        dag_service: DAGService,
        layout: Layout,
        variables: Mapping[str, DAGVariable | dict[str, Any]],
        base_context: dict[str, Any] | None = None,
        parent: QWidget | None = None,
        user_context_overrides: dict[str, tuple[str, list[str]]] | None = None,
        context_transform: ContextTransform | None = None,
    ):
        """user_context_overrides: {user_input_var_path: (target_dotted_path, [merge_keys])}

        将 user_input 变量的值合并到 DAG context 的目标路径下。

        示例:

          "user_input.敌人防御" → ("enemy.防御", ["override"])

            → 用 user_input 值直接覆盖 enemy.防御

          "user_input.额外暴击率" → ("character.暴击率", ["add"])

            → 将 user_input 值加到 character.暴击率上

        context_transform: 可选的求值后处理钩子。在 base_context、user_input
        值和覆盖规则全部合并之后调用，用于把原始输入换算成派生的乘区值
        （例如百分比抗性 → 抗性区乘数）。返回值作为最终 DAG context。

        base_context 中同名的 ``user_input.*`` 值会作为输入控件的初始值，
        避免重新确认后控件与已确认配装不一致。
        """
        super().__init__(parent)
        self._dag_service = dag_service
        self._layout = layout
        self._variables: dict[str, DAGVariable | dict[str, Any]] = dict(variables)
        self._base_context = base_context or {}
        self._user_context_overrides = user_context_overrides or {}
        self._context_transform = context_transform
        self._context_overrides: dict[str, Any] = {}
        self._widget: QWidget | None = None
        self._output_labels: dict[str, QLabel] = {}
        self._input_widgets: dict[str, tuple[QWidget, ControlSpec]] = {}
        self._input_labels: dict[str, QLabel] = {}
        self._output_formats: dict[str, str] = {oid: odef.format for oid, odef in dag_service.dag.outputs.items() if odef.format}

    @property
    def widget(self) -> QWidget:
        if self._widget is None:
            self._widget = self._build()
        return self._widget

    def evaluate(self) -> DAGResult:
        logger.debug("ComputeSheet 求值开始: %d 个输出, %d 个变量", len(self._dag_service.dag.outputs), len(self._variables))
        context = build_context(
            self._base_context,
            self._variables,
            self._input_widgets,
            self._user_context_overrides,
            self._context_overrides,
        )
        if self._context_transform is not None:
            context = self._context_transform(context, self.read_user_inputs())
        result = self._dag_service.evaluate(context)
        _do_update_outputs(result, self._layout, self._output_labels, self._output_formats)
        self.evaluated.emit(result)
        return result

    def read_user_inputs(self) -> dict[str, Any]:
        """读取所有 user_input 类型变量的当前值（用于调用方合并到 DAG context）。"""
        result: dict[str, Any] = {}
        for path, raw_var in self._variables.items():
            vd = var_to_dict(raw_var) if raw_var else {}
            if vd.get("source") == "user_input":
                result[path] = _do_read_input(path, self._input_widgets, self._variables)
        return result

    def set(self, key: str, value: Any) -> None:
        """向 DAG context 设置一个变量值。"""
        self._context_overrides[key] = value

    def set_input_enabled(self, path: str, enabled: bool, reason: str = "") -> None:
        """启用或禁用某个输入控件（并同步其标签）。

        Args:
            path: ``user_input.*`` 变量路径。
            enabled: ``False`` 时灰显控件并在悬停提示中说明原因。
            reason: 禁用原因；为空时使用控件原有描述。
        """
        entry = self._input_widgets.get(path)
        if entry is None:
            return
        widget, spec = entry
        widget.setEnabled(enabled)
        widget.setToolTip("" if enabled else reason or spec.description)

        label = self._input_labels.get(path)
        if label is not None:
            label.setEnabled(enabled)
            label.setToolTip(spec.description if enabled else reason or spec.description)

    def render_html(self) -> str:
        """将当前输出面板渲染为 HTML 表格。"""
        return _do_render_html(self._layout, self._output_labels)

    def build_section_widget(self, sec: Section) -> QWidget | None:
        """构建单个 layout 分区，并注册其中的输入/输出控件。

        共享外壳会把不同分区放入不同区域（例如输入放右上、输出放右下），
        因此需要在不构建整张计算表的情况下单独生成一个分区。

        Args:
            sec: layout.json 中的一个分区。

        Returns:
            分区控件；未知分区类型返回 ``None``。
        """
        return self._build_section(sec)

    def _read_input(self, path: str) -> Any:
        return _do_read_input(path, self._input_widgets, self._variables)

    def _build(self) -> QWidget:
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)

        if any(sec.tab for sec in self._layout.sections):
            root_layout.addWidget(self._build_tabs(), 1)
        else:
            for sec in self._layout.sections:
                widget = self._build_section(sec)
                if widget is not None:
                    root_layout.addWidget(widget)
            root_layout.addStretch()

        eval_btn = QPushButton("计算")
        eval_btn.clicked.connect(self.evaluate)
        root_layout.addWidget(eval_btn)

        return root

    def _build_tabs(self) -> QTabWidget:
        """按 section.tab 分组渲染为 QTabWidget，保持布局中首次出现的页序。"""
        tabs = QTabWidget()
        pages: dict[str, QWidget] = {}
        page_layouts: dict[str, QVBoxLayout] = {}

        for sec in self._layout.sections:
            page = pages.get(sec.tab)
            if page is None:
                page = QWidget()
                page_layout = QVBoxLayout(page)
                page_layout.setContentsMargins(0, 0, 0, 0)
                pages[sec.tab] = page
                page_layouts[sec.tab] = page_layout
                tabs.addTab(page, sec.tab)

            widget = self._build_section(sec)
            if widget is not None:
                page_layouts[sec.tab].addWidget(widget)

        for page_layout in page_layouts.values():
            page_layout.addStretch()

        return tabs

    def _build_section(self, sec: Section) -> QWidget | None:
        if sec.type == "inputs":
            return self._build_input_section(sec)
        if sec.type == "outputs":
            return self._build_output_section(sec)
        if sec.type == "widget":
            return self._build_widget_section(sec)
        return None

    def _base_context_value(self, path: str) -> Any:
        """按点分路径读取 base_context 中的值；缺失时返回 None。"""
        node: Any = self._base_context
        for part in path.split("."):
            if not isinstance(node, Mapping) or part not in node:
                return None
            node = node[part]
        return node

    def _collect_input_items(self, sec: Section) -> list[tuple[str, QLabel, QWidget | None, ControlSpec]]:
        """收集 section 中的 input 项，用于响应式重排。"""
        items: list[tuple[str, QLabel, QWidget | None, ControlSpec]] = []
        for var_path in sec.variables:
            raw_var = self._variables.get(var_path, {})
            var = var_to_dict(raw_var) if raw_var else {}
            spec = infer_control(var_path, var)
            if spec.widget == "none":
                continue
            if var.get("source") == "user_input":
                seeded = self._base_context_value(var_path)
                if seeded is not None:
                    spec.default = seeded
            # 优先用 DAG 描述作可见标签；没有描述时去掉代码前缀，
            # 避免把 user_input.fleet_count 这类命名直接展示给用户。
            label = QLabel(spec.description or display_text(spec.label))
            label.setToolTip(spec.description)
            widget = create_control(spec)
            items.append((var_path, label, widget, spec))
        return items

    def _build_input_section(self, sec: Section) -> QWidget:
        items = self._collect_input_items(sec)
        for var_path, label, widget, spec in items:
            if widget is not None:
                self._input_widgets[var_path] = (widget, spec)
                self._input_labels[var_path] = label
        for var_path, _label, widget, _spec in items:
            if widget is not None:
                self._wire_input_signal(var_path, widget)
        container = _ResponsiveGroupBox(sec.title, items)
        container._on_resized()
        return container

    def _wire_input_signal(self, path: str, widget: QWidget) -> None:
        """在输入控件变化时发出 ``value_changed(path, 逻辑值)``。

        信号携带的是 ``read_input`` 的语义值（例如滑杆的 2500 会换算成
        25.0），调用方可以直接用于标记「待确认」或做预览。
        """

        def _emit(*_args: Any) -> None:
            self.value_changed.emit(path, _do_read_input(path, self._input_widgets, self._variables))

        if isinstance(widget, QSlider | QSpinBox | QDoubleSpinBox):
            widget.valueChanged.connect(_emit)
        elif isinstance(widget, QCheckBox):
            widget.toggled.connect(_emit)
        elif isinstance(widget, QComboBox):
            widget.currentTextChanged.connect(_emit)

    def _build_output_section(self, sec: Section) -> QWidget:
        group = QGroupBox(sec.title)
        layout = QVBoxLayout(group)
        grid = QGridLayout()

        columns = max(1, sec.columns)
        for i, out_name in enumerate(sec.outputs):
            output_def = self._dag_service.dag.outputs.get(out_name)
            display = (output_def.label if output_def is not None else "") or display_text(out_name)
            label = QLabel(display)
            label.setToolTip(out_name)
            # 标签与数值不参与最小宽度计算，输出网格才能收进可视区而不产生横向滚动。
            label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            value_label = QLabel("--")
            value_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            row, column = divmod(i, columns)
            grid.addWidget(label, row, column * 2)
            grid.addWidget(value_label, row, column * 2 + 1)
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
            layout.addWidget(
                DonationWidget(
                    text=cfg.get("text", "感谢使用！如果觉得有用，欢迎支持开发者。"),
                    image_path=cfg.get("image_path") or DONATION_IMAGE_PATH,
                    parent=group,
                )
            )
            return group
        group = QGroupBox(sec.title)
        layout = QVBoxLayout(group)
        layout.addWidget(QLabel(f"未知组件: {sec.widget_type}"))
        return group
