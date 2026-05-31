#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""GraphCompiler 测试：graph_editor 格式 → DAGGraph 格式。"""

from calc_framework.graph_editor.compiler import compile_graph
from calc_framework.graph_editor.schema import (
    GraphDocument,
    GraphEdge,
    GraphLayout,
    GraphNode,
    NodeConfig,
    SectionDef,
)
from calc_framework.dag.schema import (
    BinaryNode as DAGBinaryNode,
    UnaryNode as DAGUnaryNode,
    ConditionNode as DAGConditionNode,
    ConstNode as DAGConstNode,
    VarNode as DAGVarNode,
    UserInputNode as DAGUserInputNode,
)
from calc_framework.dag.engine import evaluate_graph


class TestCompileSimple:
    def test_compile_const_node(self) -> None:
        doc = GraphDocument(
            name="常量测试",
            nodes=[GraphNode(id="n1", type="const", config=NodeConfig(value=42.0))],
            layout=GraphLayout(sections=[SectionDef(id="s1", title="结果", output_nodes=["n1"])]),
        )
        dag = compile_graph(doc)
        assert isinstance(dag.nodes["n1"], DAGConstNode)
        assert dag.nodes["n1"].value == 42.0
        assert dag.outputs["n1"].label == "n1"  # 未设 label 时回退到 node_id

    def test_compile_var_node(self) -> None:
        doc = GraphDocument(
            name="变量测试",
            nodes=[GraphNode(id="v1", type="var", config=NodeConfig(path="character.基础攻击"))],
            layout=GraphLayout(sections=[]),
        )
        dag = compile_graph(doc)
        assert isinstance(dag.nodes["v1"], DAGVarNode)
        assert dag.nodes["v1"].path == "character.基础攻击"
        # external_variables 应自动生成
        assert "character.基础攻击" in dag.variables

    def test_compile_binary_addition(self) -> None:
        doc = GraphDocument(
            name="加法",
            nodes=[
                GraphNode(id="a", type="const", config=NodeConfig(value=10)),
                GraphNode(id="b", type="const", config=NodeConfig(value=20)),
                GraphNode(id="sum", type="binary", op="+", label="求和"),
            ],
            edges=[
                GraphEdge(from_node="a", from_port=0, to_node="sum", to_port=0),
                GraphEdge(from_node="b", from_port=0, to_node="sum", to_port=1),
            ],
            layout=GraphLayout(sections=[SectionDef(id="s1", title="结果", output_nodes=["sum"])]),
        )
        dag = compile_graph(doc)
        assert isinstance(dag.nodes["sum"], DAGBinaryNode)
        assert dag.nodes["sum"].op == "+"
        assert dag.nodes["sum"].lhs == "a"
        assert dag.nodes["sum"].rhs == "b"

        res = evaluate_graph(dag, {})
        assert res.outputs["sum"] == 30.0

    def test_compile_unary_floor(self) -> None:
        doc = GraphDocument(
            name="向下取整",
            nodes=[
                GraphNode(id="v", type="const", config=NodeConfig(value=3.7)),
                GraphNode(id="r", type="unary", op="floor", label="取整"),
            ],
            edges=[GraphEdge(from_node="v", from_port=0, to_node="r", to_port=0)],
            layout=GraphLayout(sections=[SectionDef(id="s1", title="结果", output_nodes=["r"])]),
        )
        dag = compile_graph(doc)
        assert isinstance(dag.nodes["r"], DAGUnaryNode)
        assert dag.nodes["r"].op == "floor"
        assert dag.nodes["r"].input == "v"

        res = evaluate_graph(dag, {})
        assert res.outputs["r"] == 3.0

    def test_compile_user_input(self) -> None:
        doc = GraphDocument(
            name="用户输入",
            nodes=[
                GraphNode(id="ui", type="user_input",
                          config=NodeConfig(default=50.0, min=0, max=100, step=1)),
            ],
            layout=GraphLayout(sections=[]),
        )
        dag = compile_graph(doc)
        assert isinstance(dag.nodes["ui"], DAGUserInputNode)
        assert dag.nodes["ui"].default == 50.0

    def test_compile_condition(self) -> None:
        doc = GraphDocument(
            name="条件",
            nodes=[
                GraphNode(id="cond", type="const", config=NodeConfig(value=1.0)),
                GraphNode(id="t", type="const", config=NodeConfig(value=100)),
                GraphNode(id="f", type="const", config=NodeConfig(value=0)),
                GraphNode(id="choice", type="condition", label="选择"),
            ],
            edges=[
                GraphEdge(from_node="cond", from_port=0, to_node="choice", to_port=0),
                GraphEdge(from_node="t", from_port=0, to_node="choice", to_port=1),
                GraphEdge(from_node="f", from_port=0, to_node="choice", to_port=2),
            ],
            layout=GraphLayout(sections=[SectionDef(id="s1", title="结果", output_nodes=["choice"])]),
        )
        dag = compile_graph(doc)
        assert isinstance(dag.nodes["choice"], DAGConditionNode)
        assert dag.nodes["choice"].cond == "cond"
        assert dag.nodes["choice"].true_val == "t"
        assert dag.nodes["choice"].false_val == "f"

        res = evaluate_graph(dag, {})
        assert res.outputs["choice"] == 100.0


class TestCompilerOutputs:
    def test_output_nodes_from_sections(self) -> None:
        doc = GraphDocument(
            name="输出映射",
            nodes=[
                GraphNode(id="n1", type="const", label="攻击力", config=NodeConfig(value=1000)),
                GraphNode(id="n2", type="const", label="倍率", config=NodeConfig(value=2.0)),
            ],
            layout=GraphLayout(sections=[
                SectionDef(id="s1", title="攻击区", output_nodes=["n1"]),
                SectionDef(id="s2", title="最终", output_nodes=["n2"]),
            ]),
        )
        dag = compile_graph(doc)
        assert "n1" in dag.outputs
        assert dag.outputs["n1"].label == "攻击力"
        assert "n2" in dag.outputs

    def test_var_declared_as_external(self) -> None:
        doc = GraphDocument(
            name="变量声明",
            external_variables={
                "character.攻击": {"type": "float", "source": "character"},
                "enemy.防御": {"type": "float", "source": "enemy"},
            },
            nodes=[
                GraphNode(id="v1", type="var", config=NodeConfig(path="character.攻击")),
                GraphNode(id="v2", type="var", config=NodeConfig(path="enemy.防御")),
            ],
            layout=GraphLayout(sections=[]),
        )
        dag = compile_graph(doc)
        assert "character.攻击" in dag.variables
        assert dag.variables["character.攻击"].source == "character"
        assert "enemy.防御" in dag.variables


class TestCompileAndEvaluate:
    def test_chain_computation(self) -> None:
        """(10 + 20) * 3 = 90"""
        doc = GraphDocument(
            name="链式计算",
            nodes=[
                GraphNode(id="a", type="const", config=NodeConfig(value=10)),
                GraphNode(id="b", type="const", config=NodeConfig(value=20)),
                GraphNode(id="c", type="const", config=NodeConfig(value=3)),
                GraphNode(id="add", type="binary", op="+"),
                GraphNode(id="mul", type="binary", op="*"),
            ],
            edges=[
                GraphEdge(from_node="a", from_port=0, to_node="add", to_port=0),
                GraphEdge(from_node="b", from_port=0, to_node="add", to_port=1),
                GraphEdge(from_node="add", from_port=0, to_node="mul", to_port=0),
                GraphEdge(from_node="c", from_port=0, to_node="mul", to_port=1),
            ],
            layout=GraphLayout(sections=[SectionDef(id="s1", title="结果", output_nodes=["mul"])]),
        )
        dag = compile_graph(doc)
        res = evaluate_graph(dag, {})
        assert res.outputs["mul"] == 90.0

    def test_ceil_div(self) -> None:
        """ceil(100 / 30) = 4"""
        doc = GraphDocument(
            name="向上取整除法",
            nodes=[
                GraphNode(id="a", type="const", config=NodeConfig(value=100)),
                GraphNode(id="b", type="const", config=NodeConfig(value=30)),
                GraphNode(id="div", type="binary", op="/"),
                GraphNode(id="ceil", type="unary", op="ceil"),
            ],
            edges=[
                GraphEdge(from_node="a", from_port=0, to_node="div", to_port=0),
                GraphEdge(from_node="b", from_port=0, to_node="div", to_port=1),
                GraphEdge(from_node="div", from_port=0, to_node="ceil", to_port=0),
            ],
            layout=GraphLayout(sections=[SectionDef(id="s1", title="结果", output_nodes=["ceil"])]),
        )
        dag = compile_graph(doc)
        res = evaluate_graph(dag, {})
        assert res.outputs["ceil"] == 4.0

    def test_evaluate_with_variable_context(self) -> None:
        doc = GraphDocument(
            name="变量求值",
            external_variables={"x": {"type": "float", "source": "computed"}},
            nodes=[
                GraphNode(id="x_node", type="var", config=NodeConfig(path="x")),
                GraphNode(id="result", type="binary", op="*",
                          config=NodeConfig(), label="结果"),
            ],
            edges=[
                GraphEdge(from_node="x_node", from_port=0, to_node="result", to_port=0),
                GraphEdge(from_node="x_node", from_port=0, to_node="result", to_port=1),
            ],
            layout=GraphLayout(sections=[SectionDef(id="s1", title="结果", output_nodes=["result"])]),
        )
        dag = compile_graph(doc)
        res = evaluate_graph(dag, {"x": 7.0})
        assert res.outputs["result"] == 49.0


class TestEdgeCases:
    def test_compile_empty_document(self) -> None:
        doc = GraphDocument(name="空")
        dag = compile_graph(doc)
        assert len(dag.nodes) == 0
        assert len(dag.outputs) == 0
        assert dag.name == "空"

    def test_compile_const_label_falls_back(self) -> None:
        doc = GraphDocument(
            name="回退",
            nodes=[GraphNode(id="n1", type="const", config=NodeConfig(value=5))],
            layout=GraphLayout(sections=[SectionDef(id="s1", title="", output_nodes=["n1"])]),
        )
        dag = compile_graph(doc)
        assert dag.nodes["n1"].label == "常量"

    def test_missing_edge_target_skipped(self) -> None:
        doc = GraphDocument(
            name="缺失边",
            nodes=[GraphNode(id="a", type="const", config=NodeConfig(value=1))],
            edges=[GraphEdge(from_node="a", from_port=0, to_node="missing", to_port=0)],
            layout=GraphLayout(sections=[]),
        )
        dag = compile_graph(doc)
        assert len(dag.nodes) == 1
