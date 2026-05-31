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

LAYOUT_JSON = json.dumps({
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
})


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
