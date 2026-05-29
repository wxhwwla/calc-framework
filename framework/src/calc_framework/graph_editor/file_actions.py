"""文件操作 — 从编辑器中收集/加载状态，保存/打开 graph.json 文件。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from calc_framework.graph_editor.graph_editor_widget import GraphEditorWidget
from calc_framework.graph_editor.layout_panel import LayoutPanel
from calc_framework.graph_editor.schema import (
    GraphDocument,
    GraphEdge,
    GraphLayout,
    GraphNode,
    NodeConfig,
    SectionDef,
    validate,
)
from calc_framework.graph_editor.serializer import document_from_json, document_to_json


def collect_document(widget: GraphEditorWidget, panel: LayoutPanel) -> GraphDocument:
    """从编辑器状态收集 GraphDocument。"""
    nodes = widget.graph_nodes()
    edges = widget.graph_wires()
    sections = panel.sections()

    return GraphDocument(
        name="未命名",
        nodes=nodes,
        edges=edges,
        layout=GraphLayout(sections=sections),
    )


def load_document(doc: GraphDocument, widget: GraphEditorWidget, panel: LayoutPanel) -> None:
    """将 GraphDocument 加载到编辑器。"""
    widget.clear_scene()
    panel.clear_all()

    # 加载节点
    for node in doc.nodes:
        widget.add_graph_node(node)

    # 加载排版
    panel.set_sections(doc.layout.sections)

    # 加载连线（需要节点项已存在）
    for edge in doc.edges:
        src_ports = widget.node_ports(edge.from_node)
        tgt_ports = widget.node_ports(edge.to_node)
        if src_ports and tgt_ports:
            from_port = min(edge.from_port, len(src_ports) - 1)
            to_port = min(edge.to_port, len(tgt_ports) - 1)
            widget.add_wire(src_ports[from_port], tgt_ports[to_port])


def save_graph_file(doc: GraphDocument, path: Path) -> None:
    """保存 GraphDocument 到 JSON 文件。"""
    data = document_to_json(doc)
    path.write_text(data, encoding="utf-8")


def open_graph_file(path: Path) -> GraphDocument:
    """从 JSON 文件加载 GraphDocument。"""
    data = json.loads(path.read_text(encoding="utf-8"))
    doc = document_from_json(data)
    validate(doc)
    return doc
