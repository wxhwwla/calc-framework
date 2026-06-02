# SPDX-License-Identifier: AGPL-3.0
"""工厂函数 —— 从 graph_editor 格式构建 DAGService。"""

from pathlib import Path
from typing import Any

from ..dag.service import DAGService
from .compiler import compile_graph
from .serializer import document_from_json


def dag_service_from_graph_document(doc: Any) -> DAGService:
    """从 graph_editor 的 GraphDocument 编译并创建 DAGService。"""
    dag = compile_graph(doc)
    return DAGService(dag)


def dag_service_from_graph_file(path: str | Path) -> DAGService:
    """从 graph_editor 格式的 graph.json 文件加载并创建 DAGService。"""
    import json
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    doc = document_from_json(data)
    return dag_service_from_graph_document(doc)
