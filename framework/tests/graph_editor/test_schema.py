#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""GraphNode / GraphEdge / GraphDocument 数据模型测试。"""

import pytestfrom calc_framework.graph_editor.schema import (    GraphDocument,    GraphEdge,    GraphNode,    NodeConfig,    SectionDef,    ValidationError,    validate,)class TestGraphNode:
    def test_create_const_node(self) -> None:
        node = GraphNode(id="n1", type="const", label="测试常量", config=NodeConfig(value=42.0))
        assert node.id == "n1"
        assert node.type == "const"
        assert node.label == "测试常量"
        assert node.config.value == 42.0
        assert node.position is not None

    def test_create_binary_node(self) -> None:
        node = GraphNode(id="n2", type="binary", op="+", label="加法")
        assert node.type == "binary"
        assert node.op == "+"

    def test_create_var_node(self) -> None:
        node = GraphNode(id="n3", type="var", config=NodeConfig(path="character.基础攻击"))
        assert node.config.path == "character.基础攻击"

    def test_create_user_input_node(self) -> None:
        node = GraphNode(id="n4", type="user_input", config=NodeConfig(default=50.0, min=0, max=100, step=1))
        assert node.config.default == 50.0
        assert node.config.step == 1

    def test_unary_node_default_config(self) -> None:
        node = GraphNode(id="n5", type="unary", op="floor")
        assert node.config is not None

    def test_output_node(self) -> None:
        node = GraphNode(id="n6", type="output", label="最终伤害")
        assert node.type == "output"


class TestGraphEdge:
    def test_create_edge(self) -> None:
        edge = GraphEdge(from_node="n1", from_port=0, to_node="n2", to_port=0)
        assert edge.from_node == "n1"
        assert edge.to_node == "n2"

    def test_edge_default_id(self) -> None:
        edge = GraphEdge(from_node="a", from_port=0, to_node="b", to_port=0)
        assert edge.id is not None


class TestGraphDocument:
    def test_empty_document(self) -> None:
        doc = GraphDocument(name="空文档")
        assert doc.name == "空文档"
        assert doc.nodes == []
        assert doc.edges == []
        assert doc.layout.sections == []

    def test_document_with_nodes_and_edges(self) -> None:
        n1 = GraphNode(id="n1", type="const", config=NodeConfig(value=100))
        n2 = GraphNode(id="n2", type="var", config=NodeConfig(path="x"))
        n3 = GraphNode(id="n3", type="binary", op="+", label="sum")
        e1 = GraphEdge(from_node="n1", from_port=0, to_node="n3", to_port=0)
        e2 = GraphEdge(from_node="n2", from_port=0, to_node="n3", to_port=1)
        doc = GraphDocument(
            name="测试图",
            description="加法测试",
            nodes=[n1, n2, n3],
            edges=[e1, e2],
            external_variables={"x": {"type": "float", "source": "computed"}},
        )
        assert len(doc.nodes) == 3
        assert len(doc.edges) == 2
        assert "x" in doc.external_variables

    def test_document_with_layout(self) -> None:
        doc = GraphDocument(
            name="带排版",
            nodes=[GraphNode(id="o1", type="output")],
            layout=type("Layout", (), {"sections": [SectionDef(id="s1", title="结果", output_nodes=["o1"], columns=1)]})(),  # noqa: E501
        )
        assert doc.layout.sections[0].title == "结果"
        assert doc.layout.sections[0].output_nodes == ["o1"]


class TestValidation:
    def test_valid_minimal_doc(self) -> None:
        doc = GraphDocument(name="最小图")
        validate(doc)

    def test_duplicate_node_ids(self) -> None:
        doc = GraphDocument(
            name="重复节点",
            nodes=[GraphNode(id="n1"), GraphNode(id="n1")],
        )
        with pytest.raises(ValidationError, match="重复.*id"):
            validate(doc)

    def test_edge_refers_to_missing_node(self) -> None:
        doc = GraphDocument(
            name="缺节点",
            nodes=[GraphNode(id="n1")],
            edges=[GraphEdge(from_node="n1", from_port=0, to_node="n2", to_port=0)],
        )
        with pytest.raises(ValidationError, match="n2"):
            validate(doc)

    def test_edge_refers_to_missing_source_node(self) -> None:
        doc = GraphDocument(
            name="缺源节点",
            nodes=[GraphNode(id="n2")],
            edges=[GraphEdge(from_node="n1", from_port=0, to_node="n2", to_port=0)],
        )
        with pytest.raises(ValidationError, match="n1"):
            validate(doc)

    def test_unknown_node_type_rejected(self) -> None:
        doc = GraphDocument(
            name="未知类型",
            nodes=[GraphNode(id="n1", type="invalid_type")],
        )
        with pytest.raises(ValidationError, match="类型"):
            validate(doc)

    def test_missing_op_for_binary(self) -> None:
        doc = GraphDocument(
            name="缺运算",
            nodes=[GraphNode(id="n1", type="binary")],
        )
        with pytest.raises(ValidationError, match="op"):
            validate(doc)

    def test_missing_path_for_var(self) -> None:
        doc = GraphDocument(
            name="缺路径",
            nodes=[GraphNode(id="n1", type="var")],
        )
        with pytest.raises(ValidationError, match="path"):
            validate(doc)
