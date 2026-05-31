# SPDX-License-Identifier: AGPL-3.0
from __future__ import annotations

import json

import pytest
from calc_framework.dag.schema import (
    DAGGraph,
    DAGOutput,
    DAGSubgraph,
    DAGVariable,
    ExprNode,
)
from calc_framework.dag.serializer import dag_to_dict
from calc_framework.editor import (
    EditorState,
    LayoutEditor,
    discover_input_variables,
    discover_outputs,
)
from calc_framework.ui.layout import load_layout_json

SAMPLE_DAG = DAGGraph(
    name="test",
    variables={
        "character.基础攻击": DAGVariable(type="float", source="character", description="角色基础攻击"),
        "character.攻击加成": DAGVariable(type="float", source="character", description="攻击加成%"),
        "weapon_atk": DAGVariable(type="float", source="computed", description="武器攻击"),
    },
    nodes={
        "add_atk": ExprNode(expr="var_character_基础攻击 + weapon_atk"),
    },
    outputs={
        "最终攻击力": DAGOutput(node="add_atk", label="最终攻击力"),
    },
)

DAG_WITH_SUBGRAPHS = DAGGraph(
    name="test_sg",
    variables={
        "char_atk": DAGVariable(type="float", source="character", description="角色攻击"),
    },
    subgraphs={
        "calc_buff": DAGSubgraph(
            description="buff计算",
            parameters={
                "buff_rate": DAGVariable(type="float", source="character", description="buff倍率"),
                "base": DAGVariable(type="float", source="computed", description="基础值"),
            },
            nodes={
                "calc": ExprNode(expr="buff_rate * base"),
            },
            outputs={
                "buff_value": DAGOutput(node="calc", label="buff值"),
            },
        ),
    },
    nodes={
        "main": ExprNode(expr="char_atk"),
    },
    outputs={
        "final": DAGOutput(node="main", label="最终"),
    },
)


class TestDiscover:
    def test_finds_user_input_vars(self):
        result = discover_input_variables(SAMPLE_DAG)
        assert set(result) == {"character.攻击加成", "character.基础攻击"}

    def test_finds_outputs(self):
        result = discover_outputs(SAMPLE_DAG)
        assert result == ["最终攻击力"]

    def test_finds_input_vars_with_subgraphs(self):
        result = discover_input_variables(DAG_WITH_SUBGRAPHS)
        assert set(result) == {"buff_rate", "char_atk"}

    def test_finds_outputs_with_subgraphs(self):
        result = discover_outputs(DAG_WITH_SUBGRAPHS)
        assert result == ["buff_value", "final"]


class TestLayoutEditorAPI:
    def test_create_from_dag(self, tmp_path):
        dag_path = tmp_path / "test.dag.json"
        dag_path.write_text(json.dumps(dag_to_dict(SAMPLE_DAG)), encoding="utf-8")

        editor = LayoutEditor(dag_path)
        assert set(editor.available_input_vars) == {"character.攻击加成", "character.基础攻击"}
        assert editor.available_outputs == ["最终攻击力"]

    def test_add_section(self, tmp_path):
        dag_path = tmp_path / "test.dag.json"
        dag_path.write_text(json.dumps(dag_to_dict(SAMPLE_DAG)), encoding="utf-8")

        editor = LayoutEditor(dag_path)
        editor.add_section("inputs", type="inputs", title="输入参数",
                           variables=["character.基础攻击"])
        editor.add_section("results", type="outputs", title="计算结果",
                           outputs=["最终攻击力"])

        layout = editor.state.to_layout()
        assert len(layout.sections) == 2
        assert layout.sections[0].id == "inputs"
        assert layout.sections[0].variables == ["character.基础攻击"]
        assert layout.sections[1].outputs == ["最终攻击力"]

    def test_remove_section(self, tmp_path):
        dag_path = tmp_path / "test.dag.json"
        dag_path.write_text(json.dumps(dag_to_dict(SAMPLE_DAG)), encoding="utf-8")

        editor = LayoutEditor(dag_path)
        editor.add_section("s1", type="outputs", title="第一组")
        editor.add_section("s2", type="outputs", title="第二组")
        assert len(editor.state.sections) == 2

        assert editor.remove_section("s1") is True
        assert len(editor.state.sections) == 1
        assert editor.remove_section("nonexistent") is False

    def test_set_section_variables(self, tmp_path):
        dag_path = tmp_path / "test.dag.json"
        dag_path.write_text(json.dumps(dag_to_dict(SAMPLE_DAG)), encoding="utf-8")

        editor = LayoutEditor(dag_path)
        editor.add_section("inputs", type="inputs", title="输入")
        editor.set_section_variables("inputs", ["character.基础攻击", "character.攻击加成"])

        sec = editor.state.find_section("inputs")
        assert sec is not None
        assert sec.variables == ["character.基础攻击", "character.攻击加成"]

    def test_auto_layout(self, tmp_path):
        dag_path = tmp_path / "test.dag.json"
        dag_path.write_text(json.dumps(dag_to_dict(SAMPLE_DAG)), encoding="utf-8")

        editor = LayoutEditor(dag_path)
        layout = editor.auto_layout()

        assert layout.name == "Computed Layout"
        assert layout.schema_version == "ui-v1"
        assert len(layout.sections) >= 1
        output_sec = layout.sections[-1]
        assert output_sec.type == "outputs"
        assert "最终攻击力" in output_sec.outputs

    def test_export_json(self, tmp_path):
        dag_path = tmp_path / "test.dag.json"
        dag_path.write_text(json.dumps(dag_to_dict(SAMPLE_DAG)), encoding="utf-8")

        editor = LayoutEditor(dag_path)
        editor.auto_layout()
        exported = editor.export_json()
        reloaded = load_layout_json(exported)
        output_sec = reloaded.find_section("outputs")
        assert output_sec is not None
        assert output_sec.outputs == ["最终攻击力"]

    def test_export_file(self, tmp_path):
        dag_path = tmp_path / "test.dag.json"
        dag_path.write_text(json.dumps(dag_to_dict(SAMPLE_DAG)), encoding="utf-8")

        editor = LayoutEditor(dag_path)
        editor.auto_layout()
        out = tmp_path / "layout.json"
        editor.export(out)

        assert out.exists()
        with out.open(encoding="utf-8") as f:
            data = json.load(f)
        assert data["schema_version"] == "ui-v1"

    def test_from_layout(self, tmp_path):
        dag_path = tmp_path / "test.dag.json"
        dag_path.write_text(json.dumps(dag_to_dict(SAMPLE_DAG)), encoding="utf-8")

        layout_path = tmp_path / "layout.json"
        editor1 = LayoutEditor(dag_path)
        editor1.set_name("My Layout")
        editor1.add_section("res", type="outputs", title="Result", outputs=["最终攻击力"])
        editor1.export(layout_path)

        editor2 = LayoutEditor.from_layout(dag_path, layout_path)
        assert editor2.state.to_layout().name == "My Layout"
        sec = editor2.state.find_section("res")
        assert sec is not None
        assert sec.outputs == ["最终攻击力"]

    def test_create_directly_from_dag(self):
        editor = LayoutEditor(dag=SAMPLE_DAG)
        assert set(editor.available_input_vars) == {"character.攻击加成", "character.基础攻击"}
        assert editor.available_outputs == ["最终攻击力"]

    def test_create_with_neither_raises(self):
        with pytest.raises(ValueError, match="必须提供"):
            LayoutEditor()

    def test_auto_layout_no_inputs(self, tmp_path):
        dag_no_inputs = DAGGraph(
            name="no_inputs",
            variables={},
            nodes={"c": ExprNode(expr="42")},
            outputs={"答案": DAGOutput(node="c", label="答案")},
        )
        editor = LayoutEditor(dag=dag_no_inputs)
        layout = editor.auto_layout()
        assert len(layout.sections) == 1
        assert layout.sections[0].type == "outputs"

    def test_dag_property(self, tmp_path):
        dag_path = tmp_path / "test.dag.json"
        dag_path.write_text(json.dumps(dag_to_dict(SAMPLE_DAG)), encoding="utf-8")
        editor = LayoutEditor(dag_path)
        assert editor.dag is not None
        assert editor.dag.name == "test"

    def test_set_name(self, tmp_path):
        dag_path = tmp_path / "test.dag.json"
        dag_path.write_text(json.dumps(dag_to_dict(SAMPLE_DAG)), encoding="utf-8")
        editor = LayoutEditor(dag_path)
        editor.set_name("Custom Name")
        assert editor.state.layout_name == "Custom Name"

    def test_set_section_variables_missing(self, tmp_path):
        dag_path = tmp_path / "test.dag.json"
        dag_path.write_text(json.dumps(dag_to_dict(SAMPLE_DAG)), encoding="utf-8")
        editor = LayoutEditor(dag_path)
        with pytest.raises(KeyError, match="不存在"):
            editor.set_section_variables("nonexistent", ["x"])

    def test_set_section_outputs(self, tmp_path):
        dag_path = tmp_path / "test.dag.json"
        dag_path.write_text(json.dumps(dag_to_dict(SAMPLE_DAG)), encoding="utf-8")
        editor = LayoutEditor(dag_path)
        editor.add_section("outs", type="outputs", title="结果")
        sec = editor.set_section_outputs("outs", ["最终攻击力"])
        assert sec.outputs == ["最终攻击力"]

    def test_set_section_outputs_missing(self, tmp_path):
        dag_path = tmp_path / "test.dag.json"
        dag_path.write_text(json.dumps(dag_to_dict(SAMPLE_DAG)), encoding="utf-8")
        editor = LayoutEditor(dag_path)
        with pytest.raises(KeyError, match="不存在"):
            editor.set_section_outputs("nonexistent", ["x"])

    def test_editor_state_find_section_none(self):
        state = EditorState()
        assert state.find_section("nope") is None
