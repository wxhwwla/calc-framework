# SPDX-License-Identifier: AGPL-3.0
"""DAG 模板库单元测试。"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from calc_framework.dag.engine import evaluate_graph
from calc_framework.dag.sandbox import register_function, unregister_function
from calc_framework.dag.serializer import dag_from_dict
from calc_framework.dag.templates import (
    TemplateError,
    clear_templates,
    expand_template_refs,
    get_template,
    list_templates,
    register_template,
    unregister_template,
)


@pytest.fixture(autouse=True)
def reset_templates():
    """每个测试前重置模板注册表（保留内置模板）。"""

    clear_templates()

    from calc_framework.dag.templates import _register_builtin_templates

    _register_builtin_templates()

    yield


class TestTemplateRegistration:
    def test_register_and_list(self):
        register_template("test_tpl", parameters=["x"], nodes={"out": {"type": "const", "value": 42}}, output_node="out")

        assert "test_tpl" in list_templates()

    def test_register_twice_raises(self):
        register_template("dup", parameters=[], nodes={"out": {"type": "const", "value": 1}}, output_node="out")

        with pytest.raises(TemplateError, match="已注册"):
            register_template("dup", parameters=[], nodes={"out": {"type": "const", "value": 2}}, output_node="out")

    def test_register_empty_name_raises(self):
        with pytest.raises(TemplateError, match="模板名无效"):
            register_template("", parameters=[], nodes={"n": {"type": "const", "value": 1}}, output_node="n")

    def test_register_empty_nodes_raises(self):
        with pytest.raises(TemplateError, match="没有节点"):
            register_template("empty", parameters=[], nodes={}, output_node="x")

    def test_register_invalid_output_node_raises(self):
        with pytest.raises(TemplateError, match="不在 nodes 中"):
            register_template("bad", parameters=[], nodes={"a": {"type": "const", "value": 1}}, output_node="b")

    def test_unregister(self):
        register_template("t", parameters=[], nodes={"n": {"type": "const", "value": 1}}, output_node="n")

        unregister_template("t")

        assert "t" not in list_templates()

    def test_get_template_not_found_raises(self):
        with pytest.raises(TemplateError, match="未注册"):
            get_template("nonexistent")

    def test_get_template_returns_copy(self):
        register_template("t", parameters=[], nodes={"n": {"type": "const", "value": 1}}, output_node="n")

        t1 = get_template("t")

        t2 = get_template("t")

        t1["nodes"]["n"]["value"] = 99

        assert t2["nodes"]["n"]["value"] == 1


class TestExpandTemplateRefs:
    def test_no_templates_passthrough(self):
        raw = {"nodes": {"a": {"type": "const", "value": 1}}}

        result = expand_template_refs(raw)

        assert result["nodes"]["a"]["type"] == "const"

    def test_expand_simple_template(self):
        register_template(
            "double",
            parameters=["input_val"],
            nodes={
                "out": {"type": "binary", "op": "*", "lhs": "$input_val", "rhs": "const_2"},
                "const_2": {"type": "const", "value": 2},
            },
            output_node="out",
        )

        raw = {
            "nodes": {
                "my_double": {"template": "double", "bindings": {"input_val": "src_node"}},
                "src_node": {"type": "const", "value": 5},
            }
        }

        result = expand_template_refs(raw)

        nodes = result["nodes"]

        # my_double should be replaced by the output node

        assert "my_double" in nodes

        assert nodes["my_double"]["type"] == "binary"

        assert nodes["my_double"]["lhs"] == "src_node"

        assert nodes["my_double"]["rhs"] == "my_double_const_2"

        assert nodes["my_double_const_2"]["type"] == "const"

        assert nodes["my_double_const_2"]["value"] == 2

    def test_multiple_template_instances(self):
        register_template("pass", parameters=["val"], nodes={"out": {"type": "var", "path": "$val"}}, output_node="out")

        raw = {
            "nodes": {
                "a": {"template": "pass", "bindings": {"val": "x"}},
                "b": {"template": "pass", "bindings": {"val": "y"}},
                "x": {"type": "const", "value": 1},
                "y": {"type": "const", "value": 2},
            }
        }

        result = expand_template_refs(raw)

        assert result["nodes"]["a"]["path"] == "x"

        assert result["nodes"]["b"]["path"] == "y"

    def test_template_label_propagates(self):
        register_template("labeled", parameters=["v"], nodes={"out": {"type": "var", "path": "$v"}}, output_node="out")

        raw = {
            "nodes": {
                "calc": {"template": "labeled", "bindings": {"v": "src"}, "label": "我的计算"},
                "src": {"type": "const", "value": 1},
            }
        }

        result = expand_template_refs(raw)

        assert result["nodes"]["calc"].get("label") == "我的计算"

    def test_unknown_template_raises(self):
        raw = {"nodes": {"a": {"template": "not_registered", "bindings": {}}}}

        with pytest.raises(TemplateError, match="未注册"):
            expand_template_refs(raw)

    def test_unknown_binding_raises(self):
        register_template("simple", parameters=["x"], nodes={"out": {"type": "const", "value": 1}}, output_node="out")

        raw = {"nodes": {"a": {"template": "simple", "bindings": {"y": "val"}}}}

        with pytest.raises(TemplateError, match="没有参数"):
            expand_template_refs(raw)

    def test_edge_binding_references_external(self):
        register_template("ref", parameters=["src"], nodes={"out": {"type": "var", "path": "$src"}}, output_node="out")

        raw = {
            "nodes": {
                "t_node": {"template": "ref", "bindings": {"src": "character.ATK"}},
            }
        }

        result = expand_template_refs(raw)

        # $src should be replaced with "character.ATK" (external context path, not a node ID)

        assert result["nodes"]["t_node"]["path"] == "character.ATK"

    def test_inputs_dict_binding(self):
        register_template(
            "expr_tpl",
            parameters=["a", "b"],
            nodes={"out": {"type": "expr", "expr": "a + b", "inputs": {"a": "$a", "b": "$b"}}},
            output_node="out",
        )

        raw = {
            "nodes": {
                "sum": {"template": "expr_tpl", "bindings": {"a": "node_x", "b": "node_y"}},
                "node_x": {"type": "const", "value": 3},
                "node_y": {"type": "const", "value": 4},
            }
        }

        result = expand_template_refs(raw)

        inputs = result["nodes"]["sum"]["inputs"]

        assert inputs["a"] == "node_x"

        assert inputs["b"] == "node_y"


class TestBuiltinTemplates:
    """验证内置模板的展开结果。"""

    def test_defense_reduction_structure(self):
        raw = {
            "nodes": {
                "def": {"template": "defense_reduction", "bindings": {"defense": "enemy_def", "scale": "half"}},
                "enemy_def": {"type": "const", "value": 100},
                "half": {"type": "const", "value": 0.5},
            }
        }

        result = expand_template_refs(raw)

        assert "def" in result["nodes"]

    @pytest.mark.parametrize(
        "name",
        [
            "defense_reduction",
            "crit_multiplier",
            "clamp_to_range",
            "percent_of",
            "attribute_scaling",
        ],
    )
    def test_builtin_templates_registered(self, name):
        assert name in list_templates()

    def test_defense_reduction_e2e(self):
        register_function("percent_of", lambda v, t: v / t if t else 0.0)

        register_function("clamp", lambda v, mn, mx: max(mn, min(mx, v)))

        try:
            dag_json = {
                "schema_version": "dag-v1",
                "name": "test_defense",
                "variables": {
                    "enemy.DEF": {"type": "float", "source": "enemy", "default": 100},
                },
                "nodes": {
                    "enemy_def_val": {"type": "var", "path": "enemy.DEF"},
                    "half_const": {"type": "const", "value": 0.5},
                    "def_reduc": {
                        "template": "defense_reduction",
                        "bindings": {"defense": "enemy_def_val", "scale": "half_const"},
                    },
                },
                "outputs": {
                    "最终减伤": {"node": "def_reduc", "label": "最终减伤"},
                },
            }

            graph = dag_from_dict(dag_json)

            ctx = {"enemy": {"DEF": 100}}

            result = evaluate_graph(graph, ctx)

            # 100 / (100 + 100 * 0.5) = 100 / 150 = 0.666...

            assert result.outputs["最终减伤"] == pytest.approx(0.6666667, rel=1e-4)

        finally:
            unregister_function("percent_of")

            unregister_function("clamp")

    def test_crit_multiplier_e2e(self):
        dag_json = {
            "schema_version": "dag-v1",
            "name": "test_crit",
            "variables": {
                "character.crit_rate": {"type": "float", "source": "character", "default": 0.05},
                "character.crit_dmg": {"type": "float", "source": "character", "default": 0.5},
                "user_input.is_crit": {"type": "bool", "source": "user_input", "default": False},
            },
            "nodes": {
                "crit_calc": {
                    "template": "crit_multiplier",
                    "bindings": {
                        "crit_rate": "character.crit_rate",
                        "crit_dmg": "character.crit_dmg",
                        "is_crit": "user_input.is_crit",
                    },
                },
            },
            "outputs": {
                "暴击倍率": {"node": "crit_calc", "label": "暴击倍率"},
            },
        }

        graph = dag_from_dict(dag_json)

        ctx = {
            "character": {"crit_rate": 0.05, "crit_dmg": 0.5},
            "user_input": {"is_crit": False},
        }

        result = evaluate_graph(graph, ctx)

        assert result.outputs["暴击倍率"] == pytest.approx(1.0)

        ctx["user_input"]["is_crit"] = True

        result = evaluate_graph(graph, ctx)

        assert result.outputs["暴击倍率"] == pytest.approx(1.5)

    def test_clamp_to_range_e2e(self):
        register_function("clamp", lambda v, mn, mx: max(mn, min(mx, v)))

        try:
            dag_json = {
                "schema_version": "dag-v1",
                "name": "test_clamp",
                "variables": {},
                "nodes": {
                    "big_val": {"type": "const", "value": 99999},
                    "min_v": {"type": "const", "value": 0},
                    "max_v": {"type": "const", "value": 100},
                    "clamped": {
                        "template": "clamp_to_range",
                        "bindings": {"value": "big_val", "min_val": "min_v", "max_val": "max_v"},
                    },
                },
                "outputs": {
                    "钳制结果": {"node": "clamped", "label": "钳制结果"},
                },
            }

            graph = dag_from_dict(dag_json)

            result = evaluate_graph(graph, {})

            assert result.outputs["钳制结果"] == pytest.approx(100.0)

        finally:
            unregister_function("clamp")

    def test_percent_of_e2e(self):
        register_function("percent_of", lambda v, t: v / t if t else 0.0)

        try:
            dag_json = {
                "schema_version": "dag-v1",
                "name": "test_percent",
                "variables": {},
                "nodes": {
                    "val": {"type": "const", "value": 30},
                    "tot": {"type": "const", "value": 200},
                    "pct": {
                        "template": "percent_of",
                        "bindings": {"value": "val", "total": "tot"},
                    },
                },
                "outputs": {
                    "比例": {"node": "pct", "label": "比例"},
                },
            }

            graph = dag_from_dict(dag_json)

            result = evaluate_graph(graph, {})

            assert result.outputs["比例"] == pytest.approx(0.15)

        finally:
            unregister_function("percent_of")

    def test_attribute_scaling_e2e(self):
        dag_json = {
            "schema_version": "dag-v1",
            "name": "test_scaling",
            "variables": {},
            "nodes": {
                "growth": {
                    "template": "attribute_scaling",
                    "bindings": {
                        "base": "const_base",
                        "growth": "const_growth",
                        "level": "const_lv",
                        "offset": "const_off",
                        "divisor": "const_div",
                    },
                },
                "const_base": {"type": "const", "value": 100},
                "const_growth": {"type": "const", "value": 5},
                "const_lv": {"type": "const", "value": 80},
                "const_off": {"type": "const", "value": 0},
                "const_div": {"type": "const", "value": 1},
            },
            "outputs": {
                "成长值": {"node": "growth", "label": "成长值"},
            },
        }

        graph = dag_from_dict(dag_json)

        result = evaluate_graph(graph, {})

        # 100 + floor((5 * (80 - 1) + 0) / 1) = 100 + 395 = 495

        assert result.outputs["成长值"] == pytest.approx(495.0)


class TestTemplateIntegration:
    """模板与 DAG 子图/适配器的集成测试。"""

    def test_template_plus_regular_nodes(self):
        dag_json = {
            "schema_version": "dag-v1",
            "name": "mixed",
            "variables": {
                "character.ATK": {"type": "float", "source": "character", "default": 100},
            },
            "nodes": {
                "atk_val": {"type": "var", "path": "character.ATK"},
                "const_0_5": {"type": "const", "value": 0.5},
                "def_reduc": {
                    "template": "defense_reduction",
                    "bindings": {"defense": "atk_val", "scale": "const_0_5"},
                },
                "double_check": {"type": "binary", "op": "*", "lhs": "def_reduc", "rhs": "atk_val"},
            },
            "outputs": {
                "减伤比": {"node": "def_reduc", "label": "减伤比"},
                "验证": {"node": "double_check", "label": "验证"},
            },
        }

        graph = dag_from_dict(dag_json)

        ctx = {"character": {"ATK": 100}}

        result = evaluate_graph(graph, ctx)

        # def_reduc = 100 / (100 + 100*0.5) = 0.6667

        assert result.outputs["减伤比"] == pytest.approx(0.6666667, rel=1e-4)

        # double_check = def_reduc * ATK = 0.6667 * 100 = 66.67

        assert result.outputs["验证"] == pytest.approx(66.66667, rel=1e-4)

    def test_template_in_subgraph_expanded(self):
        """模板在子图中也应正常展开。"""

        dag_json = {
            "schema_version": "dag-v1",
            "name": "subgraph_with_template",
            "variables": {},
            "nodes": {
                "val": {"type": "const", "value": 200},
                "half": {"type": "const", "value": 0.5},
                "def_block": {
                    "template": "defense_reduction",
                    "bindings": {"defense": "val", "scale": "half"},
                },
            },
            "outputs": {
                "结果": {"node": "def_block", "label": "结果"},
            },
        }

        graph = dag_from_dict(dag_json)

        result = evaluate_graph(graph, {})

        # 100 / (100 + 200*0.5) = 100/200 = 0.5

        assert result.outputs["结果"] == pytest.approx(0.5)

    def test_load_dag_from_file_with_templates(self):
        register_function("percent_of", lambda v, t: v / t if t else 0.0)

        try:
            data = {
                "schema_version": "dag-v1",
                "name": "file_test",
                "variables": {},
                "nodes": {
                    "a": {"type": "const", "value": 10},
                    "b": {"type": "const", "value": 40},
                    "result": {
                        "template": "percent_of",
                        "bindings": {"value": "a", "total": "b"},
                    },
                },
                "outputs": {
                    "比例": {"node": "result", "label": "比例"},
                },
            }

            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
                json.dump(data, f)

                fpath = f.name

            try:
                from calc_framework.dag.serializer import load_dag

                graph = load_dag(fpath)

                result = evaluate_graph(graph, {})

                assert result.outputs["比例"] == pytest.approx(0.25)

            finally:
                Path(fpath).unlink(missing_ok=True)

        finally:
            unregister_function("percent_of")

    def test_clear_templates_removes_builtins(self):
        assert "defense_reduction" in list_templates()

        clear_templates()

        assert list_templates() == []
