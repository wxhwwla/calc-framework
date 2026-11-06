# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""ComputeSheet 分区构建、输入变更信号与标签回退 — 单元测试。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QLabel, QSlider

from calc_framework.dag.serializer import load_dag
from calc_framework.dag.service import DAGService
from calc_framework.ui.compute_sheet import ComputeSheet
from calc_framework.ui.layout import load_layout_json

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures"
UI_DAG = FIXTURE_DIR / "ui_test.dag.json"

LAYOUT_JSON = json.dumps(
    {
        "schema_version": "ui-v1",
        "name": "分区测试布局",
        "sections": [
            {
                "id": "inputs",
                "type": "inputs",
                "title": "输入参数",
                "variables": ["user.暴击率", "user.倍率"],
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
    return DAGService(load_dag(UI_DAG))


@pytest.fixture(scope="module")
def layout():
    return load_layout_json(LAYOUT_JSON)


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


def _sheet(dag_service, layout, variables=None, base_context=None):
    return ComputeSheet(
        dag_service=dag_service,
        layout=layout,
        variables=variables if variables is not None else dag_service.dag.variables,
        base_context=base_context or {"character": {"基础攻击": 500}, "computed": {"最终攻击力": 1000}},
    )


class TestBuildSectionWidget:
    def test_builds_input_section_without_full_sheet(self, dag_service, layout, qapp):
        sheet = _sheet(dag_service, layout)

        widget = sheet.build_section_widget(layout.sections[0])

        assert widget is not None
        assert sheet._widget is None
        assert "user.暴击率" in sheet._input_widgets
        assert sheet.read_user_inputs()["user.倍率"] == pytest.approx(1.0)

    def test_builds_output_section(self, dag_service, layout, qapp):
        sheet = _sheet(dag_service, layout)

        widget = sheet.build_section_widget(layout.sections[1])

        assert widget is not None
        assert "单段伤害" in sheet._output_labels
        assert "暴击区" in sheet._output_labels

    def test_returns_none_for_unknown_section_type(self, dag_service, layout, qapp):
        from calc_framework.ui.layout import Section

        sheet = _sheet(dag_service, layout)

        assert sheet.build_section_widget(Section(id="x", type="unknown", title="未知")) is None


class TestValueChangedSignal:
    def _collect(self, sheet):
        events: list[tuple[str, object]] = []
        sheet.value_changed.connect(lambda path, value: events.append((path, value)))
        return events

    def test_slider_emits_logical_value(self, dag_service, layout, qapp):
        sheet = _sheet(dag_service, layout)
        sheet.widget
        events = self._collect(sheet)

        slider = sheet._input_widgets["user.暴击率"][0]
        assert isinstance(slider, QSlider)
        slider.setValue(2500)

        assert events[-1] == ("user.暴击率", pytest.approx(25.0))

    def test_spinbox_emits_value(self, dag_service, layout, qapp):
        sheet = _sheet(dag_service, layout)
        sheet.widget
        events = self._collect(sheet)

        spin = sheet._input_widgets["user.倍率"][0]
        assert isinstance(spin, QDoubleSpinBox)
        spin.setValue(2.5)

        assert events[-1] == ("user.倍率", pytest.approx(2.5))

    def test_checkbox_and_dropdown_emit_values(self, dag_service, qapp):
        variables = {
            "user_input.开关": {"type": "bool", "source": "user_input", "default": False},
            "user_input.选择": {
                "type": "str",
                "source": "user_input",
                "default": "甲",
                "options": ["甲", "乙"],
            },
        }
        layout = load_layout_json(
            json.dumps(
                {
                    "schema_version": "ui-v1",
                    "name": "控件信号布局",
                    "sections": [
                        {
                            "id": "inputs",
                            "type": "inputs",
                            "title": "输入参数",
                            "variables": ["user_input.开关", "user_input.选择"],
                        }
                    ],
                }
            )
        )
        sheet = _sheet(dag_service, layout, variables=variables)
        sheet.widget
        events = self._collect(sheet)

        checkbox = sheet._input_widgets["user_input.开关"][0]
        assert isinstance(checkbox, QCheckBox)
        checkbox.setChecked(True)

        dropdown = sheet._input_widgets["user_input.选择"][0]
        assert isinstance(dropdown, QComboBox)
        dropdown.setCurrentIndex(1)

        assert events[-2] == ("user_input.开关", True)
        assert events[-1] == ("user_input.选择", "乙")


class TestDisplayLabelFallback:
    def _build_labels(self, dag_service, variables, section_variables):
        layout = load_layout_json(
            json.dumps(
                {
                    "schema_version": "ui-v1",
                    "name": "标签回退布局",
                    "sections": [
                        {
                            "id": "inputs",
                            "type": "inputs",
                            "title": "输入参数",
                            "variables": section_variables,
                        }
                    ],
                }
            )
        )
        sheet = _sheet(dag_service, layout, variables=variables)
        widget = sheet.widget
        return [label.text() for label in widget.findChildren(QLabel)]

    def test_strips_code_prefix_when_description_missing(self, dag_service, qapp):
        texts = self._build_labels(
            dag_service,
            {"user_input.敌人防御": {"type": "float", "source": "user_input", "default": 100}},
            ["user_input.敌人防御"],
        )

        assert "敌人防御" in texts
        assert "user_input.敌人防御" not in texts

    def test_replaces_underscores_in_english_paths(self, dag_service, qapp):
        texts = self._build_labels(
            dag_service,
            {"user_input.fleet_count": {"type": "int", "source": "user_input", "default": 1}},
            ["user_input.fleet_count"],
        )

        assert "fleet count" in texts
        assert "user_input.fleet_count" not in texts

    def test_keeps_description_when_present(self, dag_service, layout, qapp):
        sheet = _sheet(dag_service, layout)
        widget = sheet.widget

        texts = [label.text() for label in widget.findChildren(QLabel)]

        assert "暴击率加成百分比" in texts
