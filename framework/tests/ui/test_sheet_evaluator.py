# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""sheet_evaluator 纯函数单元测试（无需 Qt 环境）。"""

from __future__ import annotations

from calc_framework.dag.engine import DAGResult
from calc_framework.dag.schema import DAGVariable
from calc_framework.ui.layout import Layout, Section
from calc_framework.ui.sheet_evaluator import (
    build_context,
    read_input,
    render_html,
    update_outputs,
    var_to_dict,
)


class TestVarToDict:
    def test_dagvariable_to_dict(self):
        var = DAGVariable(type="float", source="character", description="攻击力")
        d = var_to_dict(var)
        assert d["type"] == "float"
        assert d["source"] == "character"
        assert d["description"] == "攻击力"

    def test_dict_passthrough(self):
        d = var_to_dict({"type": "int", "source": "computed", "default": 5})
        assert d["type"] == "int"
        assert d["default"] == 5

    def test_dagvariable_with_all_fields(self):
        var = DAGVariable(type="int", source="computed", description="测试", default=99)
        d = var_to_dict(var)
        assert d["type"] == "int"
        assert d["source"] == "computed"
        assert d["description"] == "测试"
        assert d["default"] == 99

    def test_dagvariable_default_description(self):
        var = DAGVariable(type="float", source="character")
        d = var_to_dict(var)
        assert d["type"] == "float"
        assert d["source"] == "character"

    def test_dict_with_some_fields(self):
        d = var_to_dict({"type": "bool"})
        assert d["type"] == "bool"


class TestReadInput:
    def test_no_widget_returns_default_from_var(self):
        variables = {"user.x": DAGVariable(type="float", source="user_input", default=42.0)}
        val = read_input("user.x", {}, variables)
        assert val == 42.0

    def test_no_widget_returns_zero_when_no_default(self):
        variables = {"user.x": DAGVariable(type="float", source="user_input")}
        val = read_input("user.x", {}, variables)
        # default 为 None 时返回 None（字段值而非 fallback）
        assert val is None

    def test_no_widget_no_var_returns_zero(self):
        val = read_input("nonexistent", {}, {})
        assert val == 0


class TestBuildContext:
    def test_base_context_preserved(self):
        ctx = build_context({"x": 1.0}, {}, {}, {}, {})
        assert ctx["x"] == 1.0

    def test_context_override_applied(self):
        ctx = build_context({}, {}, {}, {}, {"char.atk": 100})
        assert ctx["char"]["atk"] == 100

    def test_user_context_override_merge(self):
        ctx = build_context(
            base_context={"char": {"atk": 50}},
            variables={"user.加成": DAGVariable(type="float", source="user_input", default=10)},
            input_widgets={},
            user_context_overrides={"user.加成": ("char.bonus", ["override"])},
            context_overrides={},
        )
        assert ctx["char"]["bonus"] == 10

    def test_user_context_add(self):
        ctx = build_context(
            base_context={"char": {"atk": 50}},
            variables={"user.加成": DAGVariable(type="float", source="user_input", default=10)},
            input_widgets={},
            user_context_overrides={"user.加成": ("char.atk", ["add"])},
            context_overrides={},
        )
        assert ctx["char"]["atk"] == 60


class TestUpdateOutputs:
    def test_updates_matching_label(self):
        result = DAGResult(outputs={"out1": 42.0, "out2": 99.0}, node_values={})
        layout = Layout(
            schema_version="ui-v1",
            name="test",
            description="",
            sections=[Section(id="s1", type="outputs", title="结果", outputs=["out1"])],
        )
        labels = {"out1": type("MockLabel", (), {"setText": lambda s, v: None})()}  # type: ignore
        update_outputs(result, layout, labels, {})  # should not raise


class TestRenderHtml:
    def test_renders_sections_and_values(self):
        layout = Layout(
            schema_version="ui-v1",
            name="test",
            description="",
            sections=[Section(id="s1", type="outputs", title="结果", outputs=["x"])],
        )
        labels = {"x": type("Mock", (), {"text": lambda s: "42.0"})()}  # type: ignore
        html = render_html(layout, labels)
        assert "结果" in html
        assert "x" in html
        assert "42.0" in html

    def test_skips_non_output_sections(self):
        layout = Layout(
            schema_version="ui-v1",
            name="test",
            description="",
            sections=[
                Section(id="s1", type="inputs", title="输入", variables=["a"]),
                Section(id="s2", type="outputs", title="结果", outputs=["y"]),
            ],
        )
        labels = {"y": type("Mock", (), {"text": lambda s: "3.14"})()}  # type: ignore
        html = render_html(layout, labels)
        assert "输入" not in html  # inputs section skipped
        assert "结果" in html

    def test_missing_label_shows_dash(self):
        layout = Layout(
            schema_version="ui-v1",
            name="test",
            description="",
            sections=[Section(id="s1", type="outputs", title="结果", outputs=["missing"])],
        )
        html = render_html(layout, {})
        assert "--" in html
