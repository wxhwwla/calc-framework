# SPDX-License-Identifier: AGPL-3.0
"""graph.json 序列化/反序列化。"""

from __future__ import annotations

import json
from typing import Any, cast

from calc_framework.graph_editor.schema import (
    GraphDocument,
    GraphEdge,
    GraphLayout,
    GraphNode,
    NodeConfig,
    NodeType,
    SectionDef,
)


def document_to_dict(doc: GraphDocument) -> dict[str, Any]:
    """将 GraphDocument 导出为字典（即 JSON 对象）。"""
    return {
        "schema_version": doc.schema_version,
        "name": doc.name,
        "description": doc.description,
        "external_variables": dict(doc.external_variables),
        "nodes": [n.to_dict() for n in doc.nodes],
        "edges": [
            {
                "id": e.id,
                "from_node": e.from_node,
                "from_port": e.from_port,
                "to_node": e.to_node,
                "to_port": e.to_port,
            }
            for e in doc.edges
        ],
        "layout": {
            "sections": [
                {
                    "id": s.id,
                    "title": s.title,
                    "output_nodes": list(s.output_nodes),
                    "columns": s.columns,
                }
                for s in doc.layout.sections
            ],
        },
    }


def document_to_json(doc: GraphDocument, *, indent: int = 2) -> str:
    """将 GraphDocument 序列化为 JSON 字符串。"""
    return json.dumps(document_to_dict(doc), ensure_ascii=False, indent=indent)


def document_from_json(data: dict[str, Any] | str) -> GraphDocument:
    """从字典或 JSON 字符串加载 GraphDocument。"""
    if isinstance(data, str):
        data = json.loads(data)

    nodes = [_node_from_dict(n) for n in data.get("nodes", [])]
    edges = [_edge_from_dict(e) for e in data.get("edges", [])]
    layout_raw = data.get("layout", {})
    sections = [_section_from_dict(s) for s in layout_raw.get("sections", [])]

    return GraphDocument(
        schema_version=data.get("schema_version", "calc-graph-v1"),
        name=data.get("name", ""),
        description=data.get("description", ""),
        external_variables=data.get("external_variables", {}),
        nodes=nodes,
        edges=edges,
        layout=GraphLayout(sections=sections),
    )


def _node_from_dict(d: dict[str, Any]) -> GraphNode:
    cfg_raw = d.get("config", {}) or {}
    config = NodeConfig.from_dict(cfg_raw)
    position = d.get("position")
    if position is None:
        position = {"x": 0.0, "y": 0.0}
    return GraphNode(
        id=d["id"],
        type=cast(NodeType, d.get("type", "const")),
        op=d.get("op"),
        label=d.get("label", ""),
        config=config,
        position={"x": float(position["x"]), "y": float(position["y"])},
    )


def _edge_from_dict(d: dict[str, Any]) -> GraphEdge:
    return GraphEdge(
        id=d.get("id", ""),
        from_node=d["from_node"],
        from_port=int(d.get("from_port", 0)),
        to_node=d["to_node"],
        to_port=int(d.get("to_port", 0)),
    )


def _section_from_dict(d: dict[str, Any]) -> SectionDef:
    return SectionDef(
        id=d["id"],
        title=d.get("title", ""),
        output_nodes=d.get("output_nodes", []),
        columns=d.get("columns", 1),
    )
