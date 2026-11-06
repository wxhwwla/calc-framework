# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""ComputeSheet 组件 — 单元测试。



验证声明式 UI 正确加载 DAG + layout.json 并渲染为 QWidget 控件树。

"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from calc_framework.dag.serializer import load_dag
from calc_framework.dag.service import DAGService
from calc_framework.ui.compute_sheet import ComputeSheet
from calc_framework.ui.layout import load_layout_json

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures"

UI_DAG = FIXTURE_DIR / "ui_test.dag.json"


LAYOUT_JSON = json.dumps(
    {
        "schema_version": "ui-v1",
        "name": "测试布局",
        "sections": [
            {
                "id": "inputs",
                "type": "inputs",
                "title": "输入参数",
                "variables": ["user.暴击率", "user.倍率"],
                "columns": 2,
            },
            {
                "id": "outputs",
                "type": "outputs",
                "title": "计算结果",
                "outputs": ["单段伤害", "暴击区"],
            },
        ],
    }
)


@pytest.fixture(scope="module")
def dag_service():
    graph = load_dag(UI_DAG)

    return DAGService(graph)


@pytest.fixture(scope="module")
def layout():
    return load_layout_json(LAYOUT_JSON)


@pytest.fixture(scope="module")
def qapp():
    import sys

    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()

    if app is None:
        app = QApplication(sys.argv)

    yield app


class TestComputeSheetBuild:
    def test_widget_created(self, dag_service, layout, qapp):
        sheet = ComputeSheet(
            dag_service=dag_service,
            layout=layout,
            variables=dag_service.dag.variables,
            base_context={"character": {"基础攻击": 500}, "computed": {"最终攻击力": 1000}},
        )

        w = sheet.widget

        assert w is not None

    def test_input_controls_created(self, dag_service, layout, qapp):
        sheet = ComputeSheet(
            dag_service=dag_service,
            layout=layout,
            variables=dag_service.dag.variables,
            base_context={"character": {"基础攻击": 500}, "computed": {"最终攻击力": 1000}},
        )

        sheet.widget

        assert len(sheet._input_widgets) > 0

    def test_output_labels_initialized(self, dag_service, layout, qapp):
        sheet = ComputeSheet(
            dag_service=dag_service,
            layout=layout,
            variables=dag_service.dag.variables,
            base_context={"character": {"基础攻击": 500}, "computed": {"最终攻击力": 1000}},
        )

        sheet.widget

        assert "单段伤害" in sheet._output_labels

        assert "暴击区" in sheet._output_labels


class TestComputeSheetInputLabels:
    def test_input_label_uses_description(self, dag_service, layout, qapp):
        """输入项标签优先显示 DAG 描述，而非英文变量路径。"""
        from PySide6.QtWidgets import QLabel

        sheet = ComputeSheet(
            dag_service=dag_service,
            layout=layout,
            variables=dag_service.dag.variables,
            base_context={"character": {"基础攻击": 500}, "computed": {"最终攻击力": 1000}},
        )

        widget = sheet.widget
        texts = [label.text() for label in widget.findChildren(QLabel)]

        assert "暴击率加成百分比" in texts
        assert "技能倍率" in texts
        assert "user.暴击率" not in texts
        assert "user.倍率" not in texts


class TestComputeSheetBaseContextSeeding:
    def test_user_input_widgets_seeded_from_base_context(self, dag_service, layout, qapp):
        sheet = ComputeSheet(
            dag_service=dag_service,
            layout=layout,
            variables=dag_service.dag.variables,
            base_context={
                "user": {"暴击率": 25.0, "倍率": 2.0},
                "character": {"基础攻击": 500},
                "computed": {"最终攻击力": 1000},
            },
        )

        sheet.widget

        values = sheet.read_user_inputs()

        assert values["user.暴击率"] == pytest.approx(25.0)
        assert values["user.倍率"] == pytest.approx(2.0)

        result = sheet.evaluate()

        assert result.outputs["暴击区"] == pytest.approx(1.25)
        assert result.outputs["单段伤害"] == pytest.approx(1000 * 2.0 * 1.25)

    def test_missing_base_value_falls_back_to_declared_default(self, dag_service, layout, qapp):
        sheet = ComputeSheet(
            dag_service=dag_service,
            layout=layout,
            variables=dag_service.dag.variables,
            base_context={"character": {"基础攻击": 500}, "computed": {"最终攻击力": 1000}},
        )

        sheet.widget

        values = sheet.read_user_inputs()

        assert values["user.暴击率"] == pytest.approx(0.0)
        assert values["user.倍率"] == pytest.approx(1.0)


class TestComputeSheetContextTransform:
    def test_transform_sees_merged_context_and_widget_values(self, dag_service, layout, qapp):
        seen: dict[str, object] = {}

        def transform(context, user_values):
            seen["context"] = context
            seen["user_values"] = user_values
            context["computed"]["最终攻击力"] = 2000.0
            return context

        sheet = ComputeSheet(
            dag_service=dag_service,
            layout=layout,
            variables=dag_service.dag.variables,
            base_context={
                "user": {"暴击率": 10.0, "倍率": 1.5},
                "character": {"基础攻击": 500},
                "computed": {"最终攻击力": 1000},
            },
            context_transform=transform,
        )

        sheet.widget

        result = sheet.evaluate()

        assert seen["context"]["character"]["基础攻击"] == 500  # type: ignore[index]
        assert seen["user_values"]["user.暴击率"] == pytest.approx(10.0)  # type: ignore[index]
        assert result.outputs["单段伤害"] == pytest.approx(2000.0 * 1.5 * 1.1)

    def test_transform_can_derive_values_from_widget_inputs(self, dag_service, layout, qapp):
        def transform(context, user_values):
            context["computed"]["最终攻击力"] = 1000.0 + float(user_values["user.暴击率"])
            return context

        sheet = ComputeSheet(
            dag_service=dag_service,
            layout=layout,
            variables=dag_service.dag.variables,
            base_context={"user": {"暴击率": 10.0, "倍率": 2.0}, "computed": {"最终攻击力": 1000}},
            context_transform=transform,
        )

        sheet.widget

        result = sheet.evaluate()

        assert result.outputs["单段伤害"] == pytest.approx(1010.0 * 2.0 * 1.1)


class TestOutputColumns:
    def test_output_section_honours_configured_columns(self, dag_service, qapp):
        from PySide6.QtWidgets import QGroupBox

        layout_data = json.loads(LAYOUT_JSON)
        layout_data["sections"][1]["outputs"] = ["单段伤害", "暴击区", "单段伤害", "暴击区"]
        layout_data["sections"][1]["columns"] = 2
        layout = load_layout_json(json.dumps(layout_data))

        sheet = ComputeSheet(
            dag_service=dag_service,
            layout=layout,
            variables=dag_service.dag.variables,
            base_context={"character": {"基础攻击": 500}, "computed": {"最终攻击力": 1000}},
        )

        widget = sheet.widget
        group = next(g for g in widget.findChildren(QGroupBox) if g.title() == "计算结果")
        grid = group.layout().itemAt(0).layout()

        assert grid.itemAtPosition(0, 0) is not None
        assert grid.itemAtPosition(0, 2) is not None
        assert grid.itemAtPosition(0, 4) is None


class TestComputeSheetTabs:
    @staticmethod
    def _tabbed_layout():
        layout_data = json.loads(LAYOUT_JSON)
        layout_data["sections"][0]["tab"] = "计算"
        layout_data["sections"][1]["tab"] = "乘区明细"
        return load_layout_json(json.dumps(layout_data))

    def test_sections_are_grouped_into_tabs(self, dag_service, qapp):
        from PySide6.QtWidgets import QGroupBox, QTabWidget

        sheet = ComputeSheet(
            dag_service=dag_service,
            layout=self._tabbed_layout(),
            variables=dag_service.dag.variables,
            base_context={"character": {"基础攻击": 500}, "computed": {"最终攻击力": 1000}},
        )

        tabs = sheet.widget.findChild(QTabWidget)
        assert tabs is not None
        assert tabs.count() == 2
        assert tabs.tabText(0) == "计算"
        assert tabs.tabText(1) == "乘区明细"
        first_titles = {group.title() for group in tabs.widget(0).findChildren(QGroupBox)}
        second_titles = {group.title() for group in tabs.widget(1).findChildren(QGroupBox)}
        assert first_titles == {"输入参数"}
        assert second_titles == {"计算结果"}

    def test_outputs_on_second_tab_still_update(self, dag_service, qapp):
        sheet = ComputeSheet(
            dag_service=dag_service,
            layout=self._tabbed_layout(),
            variables=dag_service.dag.variables,
            base_context={"character": {"基础攻击": 500}, "computed": {"最终攻击力": 1000}},
        )

        sheet.widget
        result = sheet.evaluate()

        assert result.outputs["暴击区"] == pytest.approx(1.0)
        assert sheet._output_labels["暴击区"].text() == "1.0000"

    def test_layout_without_tabs_has_no_tab_widget(self, dag_service, layout, qapp):
        from PySide6.QtWidgets import QTabWidget

        sheet = ComputeSheet(
            dag_service=dag_service,
            layout=layout,
            variables=dag_service.dag.variables,
            base_context={"character": {"基础攻击": 500}, "computed": {"最终攻击力": 1000}},
        )

        assert sheet.widget.findChild(QTabWidget) is None


class TestInputEnablement:
    def test_set_input_enabled_toggles_widget_and_label(self, dag_service, layout, qapp):
        from PySide6.QtWidgets import QLabel

        sheet = ComputeSheet(
            dag_service=dag_service,
            layout=layout,
            variables=dag_service.dag.variables,
            base_context={"character": {"基础攻击": 500}, "computed": {"最终攻击力": 1000}},
        )

        widget = sheet.widget
        control = sheet._input_widgets["user.暴击率"][0]

        assert control.isEnabled()

        sheet.set_input_enabled("user.暴击率", False, reason="不需要")

        assert not control.isEnabled()
        assert control.toolTip() == "不需要"
        labels = [label for label in widget.findChildren(QLabel) if label.text() == "暴击率加成百分比"]
        assert labels and not labels[0].isEnabled()

        sheet.set_input_enabled("user.暴击率", True)

        assert control.isEnabled()
        assert control.toolTip() == ""


class TestComputeSheetEvaluate:
    def test_evaluates_and_updates_outputs(self, dag_service, layout, qapp):
        sheet = ComputeSheet(
            dag_service=dag_service,
            layout=layout,
            variables=dag_service.dag.variables,
            base_context={"character": {"基础攻击": 500}, "computed": {"最终攻击力": 1000}},
        )

        sheet.widget

        result = sheet.evaluate()

        assert result.outputs["暴击区"] == pytest.approx(1.0)

        assert "单段伤害" in result.outputs

    def test_emits_evaluated_signal(self, dag_service, layout, qapp):
        signals_received = []

        sheet = ComputeSheet(
            dag_service=dag_service,
            layout=layout,
            variables=dag_service.dag.variables,
            base_context={"character": {"基础攻击": 500}, "computed": {"最终攻击力": 1000}},
        )

        sheet.widget

        sheet.evaluated.connect(lambda r: signals_received.append(r))

        sheet.evaluate()

        assert len(signals_received) == 1

        assert signals_received[0].outputs["暴击区"] == pytest.approx(1.0)
