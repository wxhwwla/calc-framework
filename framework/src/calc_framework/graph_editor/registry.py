# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""节点类型注册表 — 管理所有可用的节点定义。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import cast

from .package_manager import CompositeTypeDef, PackageManager
from .schema import GraphNode, NodeConfig, NodeType


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
        ops=[
            ("if", "如果"),
            ("max", "取最大值"),
            ("min", "取最小值"),
        ],
        default_op="if",
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

_composite_registry: dict[str, CompositeTypeDef] = {}

_package_manager: PackageManager | None = None


def get_package_manager() -> PackageManager:
    """返回全局包管理器（单例）。"""

    global _package_manager

    if _package_manager is None:
        _package_manager = PackageManager()

    return _package_manager


def register_composite_type(tdef: CompositeTypeDef) -> None:
    """注册一个复合节点类型。"""

    _composite_registry[tdef.type_id] = tdef


def get_composite_type_ids() -> list[str]:
    """返回所有已注册的复合节点类型 ID。"""

    return sorted(_composite_registry.keys())


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

    if entry is not None:
        return entry.display_name

    ct = _composite_registry.get(type_id)

    if ct is not None:
        return ct.display_name

    return type_id


def get_category(type_id: str) -> str:
    """返回节点类型所属分类。"""

    entry = get_registry().get(type_id)

    if entry is not None:
        return entry.category

    if type_id in _composite_registry:
        return "包"

    return "其他"


def get_nodes_by_category() -> dict[str, list[NodeTypeDef]]:
    """按分类分组返回所有节点类型（含复合节点）。"""

    cats: dict[str, list[NodeTypeDef]] = {}

    for entry in get_registry().values():
        cat = entry.category

        if cat not in cats:
            cats[cat] = []

        cats[cat].append(entry)

    # 复合节点归入"包"

    if _composite_registry:
        cat = "包"

        if cat not in cats:
            cats[cat] = []

        for type_id, ct in sorted(_composite_registry.items()):
            pseudo = NodeTypeDef(
                type_id=type_id,
                display_name=ct.display_name,
                category="包",
                description=f"来自包 [{ct.package_name}] 的复合节点",
                in_count=ct.in_count,
                out_count=ct.out_count,
                in_labels=ct.in_labels,
                out_labels=ct.out_labels,
            )

            cats[cat].append(pseudo)

    return cats


def create_default_node(type_id: str, node_id: str | None = None) -> GraphNode:
    """创建一个默认配置的节点实例。"""

    import uuid

    nid = node_id or f"node_{uuid.uuid4().hex[:8]}"

    # 复合节点

    ct = _composite_registry.get(type_id)

    if ct is not None:
        return GraphNode(
            id=nid,
            type=cast(NodeType, "composite"),
            op=type_id,
            label=ct.display_name,
            config=NodeConfig(
                source_graph=ct.source_graph_json,
                package_name=ct.package_name,
            ),
        )

    # 内置节点

    entry = get_registry().get(type_id)

    if entry is None:
        raise ValueError(f"未知节点类型: {type_id}")

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
