#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""DAGService 加载 graph.json 格式测试。"""

import tempfile
from pathlib import Path

from calc_framework.dag.service import DAGService
from calc_framework.graph_editor.dag_service_factory import (
    dag_service_from_graph_document,
    dag_service_from_graph_file,
)
from calc_framework.graph_editor.schema import (
    GraphDocument,
    GraphEdge,
    GraphLayout,
    GraphNode,
    NodeConfig,
    SectionDef,
)
from calc_framework.graph_editor.serializer import document_to_json


class TestGraphFileToDAGService:
    def test_from_graph_document_direct(self) -> None:
        doc = GraphDocument(
            name="graph.json 测试",
            nodes=[
                GraphNode(id="a", type="const", label="A", config=NodeConfig(value=10)),
                GraphNode(id="b", type="const", label="B", config=NodeConfig(value=20)),
                GraphNode(id="s", type="binary", op="+", label="求和"),
            ],
            edges=[
                GraphEdge(from_node="a", from_port=0, to_node="s", to_port=0),
                GraphEdge(from_node="b", from_port=0, to_node="s", to_port=1),
            ],
            layout=GraphLayout(sections=[SectionDef(id="r", title="结果", output_nodes=["s"])]),
        )
        svc = dag_service_from_graph_document(doc)
        res = svc.evaluate({})
        assert res.outputs["s"] == 30.0

    def test_from_graph_file(self) -> None:
        doc = GraphDocument(
            name="文件测试",
            nodes=[
                GraphNode(id="x", type="const", config=NodeConfig(value=7)),
                GraphNode(id="y", type="const", config=NodeConfig(value=6)),
                GraphNode(id="m", type="binary", op="*"),
            ],
            edges=[
                GraphEdge(from_node="x", from_port=0, to_node="m", to_port=0),
                GraphEdge(from_node="y", from_port=0, to_node="m", to_port=1),
            ],
            layout=GraphLayout(sections=[SectionDef(id="r", title="乘积", output_nodes=["m"])]),
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write(document_to_json(doc))
            f.flush()
            fname = Path(f.name)

        try:
            svc = dag_service_from_graph_file(fname)
            res = svc.evaluate({})
            assert res.outputs["m"] == 42.0
        finally:
            if fname.exists():
                fname.unlink()

    def test_graph_file_with_variables(self) -> None:
        doc = GraphDocument(
            name="变量",
            external_variables={"atk": {"type": "float", "source": "character"}},
            nodes=[
                GraphNode(id="atk_node", type="var", config=NodeConfig(path="atk")),
                GraphNode(id="mul", type="const", config=NodeConfig(value=2)),
                GraphNode(id="r", type="binary", op="*", label="乘积"),
            ],
            edges=[
                GraphEdge(from_node="atk_node", from_port=0, to_node="r", to_port=0),
                GraphEdge(from_node="mul", from_port=0, to_node="r", to_port=1),
            ],
            layout=GraphLayout(sections=[SectionDef(id="r", title="结果", output_nodes=["r"])]),
        )
        svc = dag_service_from_graph_document(doc)
        res = svc.evaluate({"atk": 500.0})
        assert res.outputs["r"] == 1000.0

    def test_graph_file_with_output_marker(self) -> None:
        """output 标记节点应正确回溯到源节点。"""
        doc = GraphDocument(
            name="输出标记",
            nodes=[
                GraphNode(id="val", type="const", label="值", config=NodeConfig(value=99)),
                GraphNode(id="out", type="output", label="最终输出"),
            ],
            edges=[
                GraphEdge(from_node="val", from_port=0, to_node="out", to_port=0),
            ],
            layout=GraphLayout(sections=[SectionDef(id="r", title="结果", output_nodes=["out"])]),
        )
        svc = dag_service_from_graph_document(doc)
        res = svc.evaluate({})
        assert res.outputs["val"] == 99.0

    def test_variables_declared_in_graph_file(self) -> None:
        doc = GraphDocument(
            name="声明",
            external_variables={
                "atk": {"type": "float", "source": "character", "description": "攻击力"},
            },
            nodes=[
                GraphNode(id="v", type="var", config=NodeConfig(path="atk")),
            ],
            layout=GraphLayout(sections=[SectionDef(id="r", title="结果", output_nodes=["v"])]),
        )
        svc = dag_service_from_graph_document(doc)
        assert "atk" in svc.dag.variables
        assert svc.dag.variables["atk"].source == "character"
