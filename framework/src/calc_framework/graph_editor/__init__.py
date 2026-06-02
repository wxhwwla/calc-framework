# SPDX-License-Identifier: AGPL-3.0
"""DAG 图编辑器 — 可视化编辑、复合节点、包管理、编译导出。

用法::

    from calc_framework.graph_editor import (
        GraphEditorWidget, GraphDocument, GraphNode, GraphEdge,
        compile_graph, dag_service_from_graph_document,
        get_registry, get_nodes_by_category, create_default_node,
    )
"""

from calc_framework.graph_editor.compiler import (
    compile_graph,
    dag_service_from_graph_document,
    dag_service_from_graph_file,
)
from calc_framework.graph_editor.file_actions import (
    collect_document,
    load_document,
    open_graph_file,
    save_graph_file,
)
from calc_framework.graph_editor.graph_editor_widget import GraphEditorWidget
from calc_framework.graph_editor.package_manager import (
    CompositePortDef,
    CompositeTypeDef,
    PackageManager,
)
from calc_framework.graph_editor.registry import (
    NodeTypeDef,
    create_default_node,
    get_nodes_by_category,
    get_registry,
)
from calc_framework.graph_editor.schema import (
    GraphDocument,
    GraphEdge,
    GraphLayout,
    GraphNode,
    NodeConfig,
    SectionDef,
)
from calc_framework.graph_editor.serializer import (
    document_from_json,
    document_to_dict,
    document_to_json,
)

__all__ = [
    "CompositePortDef",
    "CompositeTypeDef",
    "GraphDocument",
    "GraphEdge",
    "GraphEditorWidget",
    "GraphLayout",
    "GraphNode",
    "NodeConfig",
    "NodeTypeDef",
    "PackageManager",
    "SectionDef",
    "collect_document",
    "compile_graph",
    "create_default_node",
    "dag_service_from_graph_document",
    "dag_service_from_graph_file",
    "document_from_json",
    "document_to_dict",
    "document_to_json",
    "get_nodes_by_category",
    "get_registry",
    "load_document",
    "open_graph_file",
    "save_graph_file",
]
