# -*- coding: utf-8 -*-
"""适配器包验证器 — 检查生成的适配器文件是否正确。"""

from __future__ import annotations

from typing import Any


class ValidationResult:
    """验证结果。"""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)

    def summary(self) -> str:
        lines = []
        if self.errors:
            lines.append(f"❌ {len(self.errors)} 个错误:")
            for e in self.errors:
                lines.append(f"   - {e}")
        if self.warnings:
            lines.append(f"⚠️ {len(self.warnings)} 个警告:")
            for w in self.warnings:
                lines.append(f"   - {w}")
        if self.is_valid:
            lines.append("✅ 验证通过")
        return "\n".join(lines)


def validate_meta(meta: dict[str, Any], result: ValidationResult) -> None:
    """验证 meta.json。"""
    required = ["name", "schema_version", "entry_dag"]
    for field in required:
        if field not in meta:
            result.add_error(f"meta.json 缺少必填字段: {field}")

    if "entry_dag" in meta:
        dag_file = meta["entry_dag"]
        if not isinstance(dag_file, str) or not dag_file.endswith(".dag.json"):
            result.add_error(f"entry_dag 格式异常: {dag_file}")


def validate_dag(dag: dict[str, Any], result: ValidationResult) -> None:
    """验证 DAG JSON。"""
    if "nodes" not in dag:
        result.add_error("DAG 缺少 nodes 字段")
        return

    if "outputs" not in dag:
        result.add_warning("DAG 缺少 outputs 字段")
        return

    nodes = dag["nodes"]
    outputs = dag.get("outputs", {})
    variables = dag.get("variables", {})

    # 检查所有 var 节点引用的变量是否存在
    for nid, node in nodes.items():
        if node["type"] == "var":
            path = node.get("path", "")
            if path not in variables:
                result.add_error(f"节点 '{nid}' 引用了未声明的变量 '{path}'")

    # 检查所有 output 引用的 node 是否存在
    for oname, output in outputs.items():
        node_ref = output.get("node", "")
        if node_ref and node_ref not in nodes:
            result.add_error(f"输出 '{oname}' 引用了不存在的节点 '{node_ref}'")

    # 检查 binary 节点引用的 lhs/rhs
    for nid, node in nodes.items():
        if node["type"] == "binary":
            for ref in ["lhs", "rhs"]:
                ref_id = node.get(ref, "")
                if ref_id and ref_id not in nodes:
                    result.add_error(f"节点 '{nid}' 的 {ref} 引用了不存在的节点 '{ref_id}'")


def validate_attr_schema(schema: dict[str, Any], result: ValidationResult) -> None:
    """验证 attr_schema.json。"""
    if "attributes" not in schema and "fields" in schema:
        result.add_warning("attr_schema 使用了旧版 'fields' 格式，建议改用 'attributes'")
    elif "attributes" not in schema:
        result.add_error("attr_schema 缺少 attributes 字段")


def validate_layout(layout: dict[str, Any], dag_outputs: dict[str, Any], result: ValidationResult) -> None:
    """验证 layout.json 与 DAG 的一致性。"""
    if "sections" not in layout:
        result.add_warning("layout.json 缺少 sections 字段")
        return

    for section in layout["sections"]:
        if section.get("type") == "outputs":
            for out_name in section.get("outputs", []):
                if out_name not in dag_outputs:
                    result.add_error(f"layout 引用了 DAG 中不存在的输出 '{out_name}'")


def validate_adapter(
    meta: dict[str, Any] | None,
    dag: dict[str, Any] | None,
    attr_schema: dict[str, Any] | None,
    layout: dict[str, Any] | None,
) -> ValidationResult:
    """全量验证适配器包。"""
    result = ValidationResult()

    if meta:
        validate_meta(meta, result)
    else:
        result.add_error("缺少 meta.json")

    if dag:
        validate_dag(dag, result)

    if attr_schema:
        validate_attr_schema(attr_schema, result)

    if layout and dag:
        validate_layout(layout, dag.get("outputs", {}), result)

    return result
