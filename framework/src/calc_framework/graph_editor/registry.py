"""节点类型注册表 — 管理所有可用的节点定义。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, cast

from calc_framework.graph_editor.schema import GraphNode, NodeConfig, NodeType


@dataclass
class NodeTypeDef:
    """注册表中的一条节点类型定义。"""
    type_id: str
    display_name: str
    category: str
    description: str = ""
    in_count: int = 0
    out_count: int = 0
    in_labels: list[str] = field(default_factory=list)
    out_labels: list[str] = field(default_factory=list)
    ops: list[tuple[str, str]] = field(default_factory=list)
    default_op: str | None = None
    default_config: NodeConfig = field(default_factory=NodeConfig)


Registry = dict[str, NodeTypeDef]


def _build_registry() -> Registry:
    """构建完整的节点类型注册表。"""
    r: Registry = {}

    r["const"] = NodeTypeDef(
        type_id="const",
        display_name="常量",
        category="基础",
        description="固定的数值常量",
        out_count=1,
        out_labels=["数值"],
        default_config=NodeConfig(value=0.0),
    )

    r["var"] = NodeTypeDef(
        type_id="var",
        display_name="变量引用",
        category="输入",
        description="引用外部变量的值",
        out_count=1,
        out_labels=["数值"],
        default_config=NodeConfig(path=""),
    )

    r["user_input"] = NodeTypeDef(
        type_id="user_input",
        display_name="用户输入",
        category="输入",
        description="运行时由用户输入的数值",
        out_count=1,
        out_labels=["数值"],
        default_config=NodeConfig(default=0.0, min=0.0, max=100.0, step=1.0),
    )

    r["unary"] = NodeTypeDef(
        type_id="unary",
        display_name="一元运算",
        category="基础",
        description="对单个值做数学运算",
        in_count=1,
        out_count=1,
        in_labels=["值"],
        out_labels=["结果"],
        ops=[
            ("neg", "取反"),
            ("floor", "向下取整"),
            ("ceil", "向上取整"),
            ("abs", "绝对值"),
            ("sqrt", "平方根"),
            ("ln", "自然对数"),
            ("log10", "常用对数"),
            ("sin", "正弦"),
            ("cos", "余弦"),
            ("tan", "正切"),
            ("asin", "反正弦"),
            ("acos", "反余弦"),
            ("atan", "反正切"),
        ],
        default_op="floor",
    )

    r["binary"] = NodeTypeDef(
        type_id="binary",
        display_name="二元运算",
        category="基础",
        description="对两个值做数学运算",
        in_count=2,
        out_count=1,
        in_labels=["左值", "右值"],
        out_labels=["结果"],
        ops=[
            ("+", "加法"),
            ("-", "减法"),
            ("*", "乘法"),
            ("/", "除法"),
            ("^", "乘方"),
            ("mod", "取模"),
            ("min", "取最小值"),
            ("max", "取最大值"),
        ],
        default_op="+",
    )

    r["condition"] = NodeTypeDef(
        type_id="condition",
        display_name="条件分支",
        category="基础",
        description="根据条件选择两个值之一",
        in_count=3,
        out_count=1,
        in_labels=["条件", "真值", "假值"],
        out_labels=["结果"],
    )

    r["output"] = NodeTypeDef(
        type_id="output",
        display_name="输出标记",
        category="输出",
        description="标记一个值为最终输出",
        in_count=1,
        out_count=0,
        in_labels=["值"],
    )

    return r


_registry: Registry | None = None


def get_registry() -> Registry:
    """返回全局注册表（单例）。"""
    global _registry
    if _registry is None:
        _registry = _build_registry()
    return _registry


def get_node_type_ids() -> list[str]:
    """返回所有已注册的类型 ID。"""
    return sorted(get_registry().keys())


def get_display_name(type_id: str) -> str:
    """返回节点类型的中文显示名。"""
    entry = get_registry().get(type_id)
    if entry is None:
        return type_id
    return entry.display_name


def get_category(type_id: str) -> str:
    """返回节点类型所属分类。"""
    entry = get_registry().get(type_id)
    if entry is None:
        return "其他"
    return entry.category


def get_nodes_by_category() -> dict[str, list[NodeTypeDef]]:
    """按分类分组返回所有节点类型。"""
    cats: dict[str, list[NodeTypeDef]] = {}
    for entry in get_registry().values():
        cat = entry.category
        if cat not in cats:
            cats[cat] = []
        cats[cat].append(entry)
    return cats


def create_default_node(type_id: str, node_id: str | None = None) -> GraphNode:
    """创建一个默认配置的节点实例。"""
    entry = get_registry().get(type_id)
    if entry is None:
        raise ValueError(f"未知节点类型: {type_id}")

    import uuid
    nid = node_id or f"node_{uuid.uuid4().hex[:8]}"

    return GraphNode(
        id=nid,
        type=cast(NodeType, type_id),
        op=entry.default_op,
        label=entry.display_name,
        config=NodeConfig(
            value=entry.default_config.value,
            path=entry.default_config.path,
            default=entry.default_config.default,
            min=entry.default_config.min,
            max=entry.default_config.max,
            step=entry.default_config.step,
        ),
    )
