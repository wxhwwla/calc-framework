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
