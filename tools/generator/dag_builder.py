"""DAG 节点构建器 — 从公式描述生成 DAG JSON。"""

from __future__ import annotations

from typing import Any


def build_simple_formula(
    variables: list[dict[str, Any]],
    formula_steps: list[dict[str, Any]],
    outputs: list[dict[str, str]],
) -> dict[str, Any]:
    """构建简单公式 DAG。

    Args:
        variables: 变量列表，每项 {name, type, source, default, description}
        formula_steps: 公式步骤，每项 {id, op, lhs, rhs, label}
            op: "+" | "-" | "*" | "/" | "condition" | "expr"
            lhs/rhs: 变量名或其他 step id
        outputs: 输出列表，每项 {name, node, label, is_primary}

    Returns:
        DAG JSON dict
    """
    dag: dict[str, Any] = {
        "schema_version": "dag-v1",
        "name": "",
        "variables": {},
        "subgraphs": {},
        "nodes": {},
        "outputs": {},
    }

    # 添加变量
    for var in variables:
        var_name = var["name"]
        dag["variables"][var_name] = {
            "type": var.get("type", "float"),
            "source": var.get("source", "user_input"),
            "default": var.get("default", 0),
            "description": var.get("description", ""),
        }

    # 添加节点
    var_nodes: dict[str, str] = {}  # variable name → node id
    for var in variables:
        node_id = f"var_{var['name']}"
        var_nodes[var["name"]] = node_id
        dag["nodes"][node_id] = {
            "type": "var",
            "path": var["name"],
            "label": var.get("description", var["name"]),
        }

    for step in formula_steps:
        node_id = step["id"]
        op = step["op"]

        if op in ("+", "-", "*", "/"):
            lhs = var_nodes.get(step["lhs"], step["lhs"])
            rhs = var_nodes.get(step["rhs"], step["rhs"])
            dag["nodes"][node_id] = {
                "type": "binary",
                "op": op,
                "lhs": lhs,
                "rhs": rhs,
                "label": step.get("label", node_id),
            }
        elif op == "condition":
            dag["nodes"][node_id] = {
                "type": "condition",
                "cond": var_nodes.get(step["cond"], step["cond"]),
                "true_val": var_nodes.get(step["true_val"], step["true_val"]),
                "false_val": var_nodes.get(step["false_val"], step["false_val"]),
                "label": step.get("label", node_id),
            }
        elif op == "expr":
            dag["nodes"][node_id] = {
                "type": "expr",
                "expr": step["expr"],
                "inputs": {k: var_nodes.get(v, v) for k, v in step.get("input_map", {}).items()},
                "label": step.get("label", node_id),
            }

    # 添加输出
    for out in outputs:
        dag["outputs"][out["name"]] = {
            "node": var_nodes.get(out["node"], out["node"]),
            "label": out.get("label", out["name"]),
            "format": out.get("format", ""),
            "is_primary": out.get("is_primary", True),
        }

    return dag


def build_multi_zone_formula(
    base_variable: str,
    zones: list[dict[str, Any]],
    outputs: list[dict[str, str]],
) -> dict[str, Any]:
    """构建多乘区叠乘公式 DAG。

    Args:
        base_variable: 基准变量名（如 character.base_atk）
        zones: 乘区列表，每项 {id, label, nodes: [...], output_node}
        outputs: 输出列表

    Returns:
        DAG JSON dict
    """
    # 这是一个简化版的多乘区构建器
    # 完整版需要处理 subgraph 的嵌套
    dag = build_simple_formula(
        variables=[],
        formula_steps=[],
        outputs=outputs,
    )
    # 设置基本变量
    dag["variables"][base_variable] = {
        "type": "float",
        "source": base_variable.split(".")[0] if "." in base_variable else "character",
        "default": 100,
        "description": "基础值",
    }
    dag["nodes"]["base"] = {"type": "var", "path": base_variable, "label": "基础值"}

    prev_node = "base"
    for i, zone in enumerate(zones):
        zone_id = zone["id"]
        dag["nodes"][zone_id] = {
            "type": "binary",
            "op": "*",
            "lhs": prev_node,
            "rhs": f"zone_{zone_id}",
            "label": zone.get("label", zone_id),
        }
        # 乘区节点（简化：用常量占位，实际应由 AI 填充）
        dag["nodes"][f"zone_{zone_id}"] = {
            "type": "const",
            "value": 1.0,
            "label": f"{zone.get('label', zone_id)} 乘数",
        }
        prev_node = zone_id

    return dag


def dag_to_json(dag: dict[str, Any], name: str = "", description: str = "") -> str:
    """将 DAG dict 转为格式化的 JSON 字符串。"""
    if name:
        dag["name"] = name
    if description:
        dag["description"] = description
    import json

    return json.dumps(dag, ensure_ascii=False, indent=2)
