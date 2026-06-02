# SPDX-License-Identifier: AGPL-3.0
"""GraphCompiler — 将 graph_editor 的 GraphDocument 编译为 DAGGraph。"""



from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..dag.service import DAGService

from ..dag.schema import (
    BinaryNode,
    CallNode,
    ConditionNode,
    ConstNode,
    DAGGraph,
    DAGOutput,
    DAGSubgraph,
    DAGVariable,
    UnaryNode,
    UserInputNode,
    VarNode,
)
from .schema import (
    GraphDocument,
    GraphNode,
)
from .serializer import document_from_json


def compile_graph(doc: GraphDocument) -> DAGGraph:

    """将可视化编辑器格式编译为 DAG 引擎格式。"""

    # ── 1. 构建端口→节点映射 ──

    port_inputs: dict[tuple[str, int], str] = {}

    for edge in doc.edges:

        port_inputs[(edge.to_node, edge.to_port)] = edge.from_node



    # ── 2. 编译节点（含复合节点） ──

    dag_nodes: dict[str, Any] = {}

    subgraphs: dict[str, DAGSubgraph] = {}

    for node in doc.nodes:

        if node.type == "output":

            continue

        dag_n = _compile_single_node(node, port_inputs)

        if node.type == "composite" and dag_n is not None and isinstance(dag_n, CallNode):

            # 递归编译子图

            sub_name = dag_n.subgraph

            if sub_name not in subgraphs:

                sub_doc = _parse_sub_graph(node.config.source_graph)

                if sub_doc is not None:

                    sub_dag = compile_graph(sub_doc)

                    # 提取参数（user_input 节点）

                    params: dict[str, DAGVariable] = {}

                    for sub_node in sub_doc.nodes:

                        if sub_node.type == "user_input":

                            params[sub_node.id] = DAGVariable(

                                type="float",

                                source="user_input",

                                default=sub_node.config.default,

                                min=sub_node.config.min,

                                max=sub_node.config.max,

                            )

                    # 输出：自动检测 output 节点，解析到其输入源

                    sub_outputs: dict[str, DAGOutput] = {}

                    sub_port_inputs: dict[tuple[str, int], str] = {}

                    for e in sub_doc.edges:

                        sub_port_inputs[(e.to_node, e.to_port)] = e.from_node

                    for sub_node in sub_doc.nodes:

                        if sub_node.type == "output":

                            resolved = sub_port_inputs.get((sub_node.id, 0))

                            actual_node = resolved if resolved and resolved in sub_dag.nodes else sub_node.id

                            sub_outputs[sub_node.id] = DAGOutput(

                                node=actual_node,

                                label=sub_node.label or sub_node.id,

                            )

                    subgraphs[sub_name] = DAGSubgraph(

                        description=sub_doc.description,

                        parameters=params,

                        nodes=sub_dag.nodes,

                        outputs=sub_outputs,

                    )

            dag_nodes[node.id] = dag_n

        elif dag_n is not None:

            dag_nodes[node.id] = dag_n



    # ── 3. 编译变量声明 ──

    variables: dict[str, DAGVariable] = {}

    for path_str, raw in doc.external_variables.items():

        variables[path_str] = DAGVariable(

            type=str(raw.get("type", "float")),

            source=str(raw.get("source", "computed")),

            description=str(raw.get("description", "")),

        )

    for node in doc.nodes:

        if node.type == "var" and node.config.path:

            if node.config.path not in variables:

                variables[node.config.path] = DAGVariable(type="float", source="computed")



    # ── 4. 编译输出 ──

    outputs: dict[str, DAGOutput] = {}

    # 4a. 从 sections 收集输出（向后兼容旧文件）

    for sec in doc.layout.sections:

        for node_id in sec.output_nodes:

            resolved = _resolve_output_node(node_id, port_inputs, doc)

            if resolved and resolved not in outputs:

                src_node = next((n for n in doc.nodes if n.id == node_id), None)

                label = src_node.label if src_node and src_node.label else resolved

                outputs[resolved] = DAGOutput(node=resolved, label=label)

    # 4b. 自动检测 output 节点（新方式）

    for node in doc.nodes:

        if node.type == "output":

            resolved = port_inputs.get((node.id, 0))

            if resolved and resolved not in outputs:

                label = node.label if node.label else resolved

                outputs[resolved] = DAGOutput(node=resolved, label=label)



    return DAGGraph(

        schema_version="dag-v1",

        name=doc.name,

        description=doc.description,

        variables=variables,

        subgraphs=subgraphs,

        nodes=dag_nodes,

        outputs=outputs,

    )





def _parse_sub_graph(source_graph: str) -> GraphDocument | None:

    """解析复合节点中的子图 JSON 字符串。"""

    if not source_graph:

        return None

    try:

        data = json.loads(source_graph)

        return document_from_json(data)

    except Exception:

        return None





def _resolve_output_node(node_id: str, port_inputs: dict[tuple[str, int], str], doc: GraphDocument) -> str | None:

    """解析输出节点。"""

    src_node = next((n for n in doc.nodes if n.id == node_id), None)

    if src_node is None:

        return None

    if src_node.type != "output":

        return node_id

    source = port_inputs.get((node_id, 0))

    return source





def _compile_single_node(node: GraphNode, port_inputs: dict[tuple[str, int], str]) -> Any:

    """编译单个 GraphNode 为 DAG NodeType。"""

    cfg = node.config



    if node.type == "const":

        return ConstNode(value=cfg.value, label=node.label or "常量")



    if node.type == "var":

        return VarNode(path=cfg.path, label=node.label or "变量引用")



    if node.type == "user_input":

        return UserInputNode(

            default=cfg.default, min=cfg.min, max=cfg.max, step=cfg.step,

            label=node.label or "用户输入",

        )



    if node.type == "unary":

        inp = port_inputs.get((node.id, 0), "")

        return UnaryNode(op=node.op or "floor", input=inp, label=node.label or "一元运算")



    if node.type == "binary":

        lhs = port_inputs.get((node.id, 0), "")

        rhs = port_inputs.get((node.id, 1), "")

        return BinaryNode(op=node.op or "+", lhs=lhs, rhs=rhs, label=node.label or "二元运算")



    if node.type == "condition":

        cond = port_inputs.get((node.id, 0), "")

        true_val = port_inputs.get((node.id, 1), "")

        false_val = port_inputs.get((node.id, 2), "")

        return ConditionNode(cond=cond, true_val=true_val, false_val=false_val, label=node.label or "条件分支")



    if node.type == "composite":

        if not cfg.source_graph:

            raise ValueError(f"复合节点 {node.id} 缺少 source_graph 配置")

        # 解析子图以获取参数

        sub_doc = _parse_sub_graph(cfg.source_graph)

        if sub_doc is None:

            raise ValueError(f"复合节点 {node.id} 的 source_graph 解析失败")

        # 构建绑定：子图的 user_input → 父图的输入

        bindings: dict[str, str] = {}

        input_idx = 0

        for sub_node in sub_doc.nodes:

            if sub_node.type == "user_input":

                # 父图的哪个节点连到了这个复合节点的 input_idx 端口？

                parent_input = port_inputs.get((node.id, input_idx), "")

                bindings[sub_node.id] = parent_input

                input_idx += 1

        sub_name = node.op or "sub"

        return CallNode(

            subgraph=sub_name,

            bindings=bindings,

            label=node.label or "复合节点",

        )



    raise ValueError(f"未知节点类型: {node.type}")


# from dag_service_factory.py
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

