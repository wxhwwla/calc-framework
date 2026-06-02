# SPDX-License-Identifier: AGPL-3.0
from __future__ import annotations

import json

import pytest

from calc_framework.dag.schema import (
    DAGGraph,
    DAGOutput,
    DAGVariable,
    ExprNode,
)

SIMPLE_DAG = DAGGraph(
    name="simple",
    variables={
        "character.攻击": DAGVariable(type="float", source="character"),
        "computed.加成": DAGVariable(type="float", source="computed"),
    },
    nodes={"r": ExprNode(expr="var_character_攻击 + var_computed_加成")},
    outputs={"result": DAGOutput(node="r", label="result")},
)


@pytest.fixture(scope="module")
def qapp():
    import sys

    from PySide6.QtWidgets import QApplication


    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


class TestLayoutEditorWidget:
    def test_create_widget(self, qapp):
        from calc_framework.editor.gui import LayoutEditorWidget

        w = LayoutEditorWidget()
        assert w is not None
        w.close()

    def test_load_dag(self, qapp):
        from calc_framework.editor.gui import LayoutEditorWidget

        w = LayoutEditorWidget()
        w._load_dag(SIMPLE_DAG)
        assert w._editor is not None
        assert w._input_list.count() == 1
        assert w._output_list.count() == 1
        w.close()

    def test_add_section(self, qapp):
        from calc_framework.editor.gui import LayoutEditorWidget

        w = LayoutEditorWidget()
        w._load_dag(SIMPLE_DAG)
        w._section_title_input.setText("攻击区")
        w._add_section("outputs")
        assert len(w._editor.state.sections) == 1
        assert w._editor.state.sections[0].title == "攻击区"
        w.close()

    def test_export(self, qapp, tmp_path):
        from calc_framework.editor.gui import LayoutEditorWidget

        w = LayoutEditorWidget()
        w._load_dag(SIMPLE_DAG)
        w._section_title_input.setText("结果区")
        w._add_section("outputs")
        w._name_input.setText("Test Layout")
        w._editor.set_name("Test Layout")

        out_path = tmp_path / "layout.json"
        w._editor.export(out_path)

        assert out_path.exists()
        with out_path.open(encoding="utf-8") as f:
            data = json.load(f)
        assert data["name"] == "Test Layout"
        assert data["sections"][0]["title"] == "结果区"
        w.close()
