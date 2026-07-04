# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""ComputeSheet QWidget — 声明式计算表组件。

将 DAG 公式图 + layout.json 排版渲染为可交互的 PySide6 控件树。

ComputeSheet 类的胶水代码，控件生成委托给 sheet_widgets，求值逻辑委托给 sheet_evaluator。
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QLabel,
    QPushButton,
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
        self._variables: dict[str, DAGVariable | dict[str, Any]] = dict(variables)
        self._base_context = base_context or {}
        self._user_context_overrides = user_context_overrides or {}
        self._context_overrides: dict[str, Any] = {}
        self._widget: QWidget | None = None
        self._output_labels: dict[str, QLabel] = {}
        self._input_widgets: dict[str, tuple[QWidget, ControlSpec]] = {}
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

    def render_html(self) -> str:
        """将当前输出面板渲染为 HTML 表格。"""
        return _do_render_html(self._layout, self._output_labels)

    def _read_input(self, path: str) -> Any:
        return _do_read_input(path, self._input_widgets, self._variables)

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
            var = var_to_dict(raw_var) if raw_var else {}
            spec = infer_control(var_path, var)
            if spec.widget == "none":
                continue
            label = QLabel(spec.label)
            label.setToolTip(spec.description)
            widget = create_control(spec)
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
