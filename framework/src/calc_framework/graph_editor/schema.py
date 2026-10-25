# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""可视化公式计算图 — 数据模型定义。"""

from dataclasses import dataclass, field
from typing import Any, Literal

from ..errors import CalcFrameworkError

# ── 支持的所有节点类型 ──────────────────────────

NodeType = Literal["const", "var", "user_input", "unary", "binary", "condition", "output", "composite"]


VALID_NODE_TYPES: set[str] = {"const", "var", "user_input", "unary", "binary", "condition", "output", "composite"}


# 基础包一元运算

UNARY_OPS: set[str] = {"neg", "floor", "ceil", "abs", "sqrt"}

# 扩展包一元运算（注册后加入）

UNARY_OPS_EXT: set[str] = {"ln", "log10", "sin", "cos", "tan"}


# 基础包二元运算

BINARY_OPS: set[str] = {"+", "-", "*", "/", "^", "mod", "min", "max"}


class ValidationError(CalcFrameworkError):
    """graph.json 校验失败。"""


@dataclass
class NodeConfig:
    """节点类型相关的配置参数。"""

    value: float = 0.0

    path: str = ""

    default: float = 0.0

    min: float = 0.0

    max: float = 100.0

    step: float = 1.0

    source_graph: str = ""

    package_name: str = ""

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {}

        if self.value != 0.0:
            d["value"] = self.value

        if self.path:
            d["path"] = self.path

        if self.default != 0.0:
            d["default"] = self.default

        if self.min != 0.0:
            d["min"] = self.min

        if self.max != 100.0:
            d["max"] = self.max

        if self.step != 1.0:
            d["step"] = self.step

        if self.source_graph:
            d["source_graph"] = self.source_graph

        if self.package_name:
            d["package_name"] = self.package_name

        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "NodeConfig":
        return cls(
            value=d.get("value", 0.0),
            path=d.get("path", ""),
            default=d.get("default", 0.0),
            min=d.get("min", 0.0),
            max=d.get("max", 100.0),
            step=d.get("step", 1.0),
            source_graph=d.get("source_graph", ""),
            package_name=d.get("package_name", ""),
        )


@dataclass
class GraphNode:
    """计算图中的一个节点。"""

    id: str

    type: NodeType = "const"

    op: str | None = None

    label: str = ""

    config: NodeConfig = field(default_factory=NodeConfig)

    position: dict[str, float] = field(default_factory=lambda: {"x": 0.0, "y": 0.0})

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "id": self.id,
            "type": self.type,
            "label": self.label,
            "position": dict(self.position),
        }

        if self.op is not None:
            d["op"] = self.op

        cfg = self.config.to_dict()

        if cfg:
            d["config"] = cfg

        return d


@dataclass
class GraphEdge:
    """节点之间的连线。"""

    from_node: str

    from_port: int = 0

    to_node: str = ""

    to_port: int = 0

    id: str = ""


@dataclass
class SectionDef:
    """排版中的一节，指定哪些输出节点放入此节。"""

    id: str

    title: str = ""

    output_nodes: list[str] = field(default_factory=list)

    columns: int = 1


@dataclass
class GraphLayout:
    """显示排版信息。"""

    sections: list[SectionDef] = field(default_factory=list)


@dataclass
class GraphDocument:
    """完整的计算图文档（一个 JSON 文件）。"""

    schema_version: str = "calc-graph-v1"

    name: str = ""

    description: str = ""

    external_variables: dict[str, Any] = field(default_factory=dict)

    nodes: list[GraphNode] = field(default_factory=list)

    edges: list[GraphEdge] = field(default_factory=list)

    layout: GraphLayout = field(default_factory=GraphLayout)


def validate(doc: GraphDocument) -> None:
    """校验 GraphDocument 的完整性。"""

    seen_ids: set[str] = set()

    for node in doc.nodes:
        if node.id in seen_ids:
            raise ValidationError(f"重复的节点 id: {node.id}")

        seen_ids.add(node.id)

        if node.type not in VALID_NODE_TYPES:
            raise ValidationError(f"未知节点类型: {node.type}，有效值: {sorted(VALID_NODE_TYPES)}")

        if node.type == "binary" and node.op is None:
            raise ValidationError(f"二元节点 {node.id} 缺少 op 字段")

        if node.type == "binary" and node.op not in BINARY_OPS:
            raise ValidationError(f"二元节点 {node.id} 不支持的操作: {node.op}，有效值: {sorted(BINARY_OPS)}")

        if node.type == "unary" and node.op is None:
            raise ValidationError(f"一元节点 {node.id} 缺少 op 字段")

        valid_unary = UNARY_OPS | UNARY_OPS_EXT

        if node.type == "unary" and node.op not in valid_unary:
            raise ValidationError(f"一元节点 {node.id} 不支持的操作: {node.op}")

        if node.type == "var" and not node.config.path:
            raise ValidationError(f"变量引用节点 {node.id} 缺少 path 配置")

    all_node_ids = {n.id for n in doc.nodes}

    for edge in doc.edges:
        if edge.from_node not in all_node_ids:
            raise ValidationError(f"连线 from_node '{edge.from_node}' 不存在")

        if edge.to_node not in all_node_ids:
            raise ValidationError(f"连线 to_node '{edge.to_node}' 不存在")
