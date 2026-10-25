# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""文件操作 — 从编辑器中收集/加载状态，保存/打开 graph.json 文件。"""

from __future__ import annotations

import json
from pathlib import Path

from calc_framework.ui.i18n import tr

from .graph_editor_widget import GraphEditorWidget
from .ports import PortDirection
from .schema import (
    GraphDocument,
    GraphLayout,
    SectionDef,
    validate,
)
from .serializer import document_from_json, document_to_json


def collect_document(widget: GraphEditorWidget) -> GraphDocument:
    """从编辑器状态收集 GraphDocument。"""

    nodes = widget.graph_nodes()

    edges = widget.graph_wires()

    # 自动收集所有 output 节点作为默认输出

    output_nodes = [n.id for n in nodes if n.type == "output"]

    sections = (
        [SectionDef(id="outputs", title=tr("desktop.graphEditor.nodeTypeOutput"), output_nodes=output_nodes, columns=1)]
        if output_nodes
        else []
    )

    return GraphDocument(
        name=tr("desktop.graphEditor.untitled"),
        nodes=nodes,
        edges=edges,
        layout=GraphLayout(sections=sections),
    )


def load_document(doc: GraphDocument, widget: GraphEditorWidget) -> None:
    """将 GraphDocument 加载到编辑器。"""

    widget.clear_scene()

    for node in doc.nodes:
        widget.add_graph_node(node)

    for edge in doc.edges:
        src_ports = widget.node_ports(edge.from_node)
        tgt_ports = widget.node_ports(edge.to_node)

        if src_ports and tgt_ports:
            # from_port 是输出端口索引，to_port 是输入端口索引
            src_outputs = [p for p in src_ports if p.direction == PortDirection.OUTPUT]
            tgt_inputs = [p for p in tgt_ports if p.direction == PortDirection.INPUT]

            if src_outputs and tgt_inputs:
                from_idx = min(edge.from_port, len(src_outputs) - 1)
                to_idx = min(edge.to_port, len(tgt_inputs) - 1)
                widget.add_wire(src_outputs[from_idx], tgt_inputs[to_idx])


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
