# SPDX-License-Identifier: AGPL-3.0
"""DAG 增量求值状态：跨求值调用追踪节点值变化。"""

from __future__ import annotations

import contextlib
import hashlib
import json
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from .schema import (
    BinaryNode,
    ConditionNode,
    DAGGraph,
    ExprNode,
    NodeType,
    UnaryNode,
)


def _node_dependencies(node: NodeType) -> list[str]:
    """返回节点的直接依赖节点 ID 列表（与 engine.py 同步）。"""

    if isinstance(node, UnaryNode):
        return [node.input]

    if isinstance(node, BinaryNode):
        return [node.lhs, node.rhs]

    if isinstance(node, ConditionNode):
        return [node.cond, node.true_val, node.false_val]

    if isinstance(node, ExprNode):
        return list(node.inputs.values())

    return []


@dataclass
class DAGState:
    """增量求值状态。



    保留上一次求值的节点值和上下文快照，用于检测变化并仅重算受影响节点。



    Attributes:

        node_values: 上一次求值的节点值快照。

        prev_flat_context: 上一次上下文的扁平字典快照。

        context_hash: 上一次上下文的状态哈希（用于快速判断是否变化）。

        evaluation_count: 已执行求值的次数。

    """

    node_values: dict[str, float] = field(default_factory=dict)

    prev_outputs: dict[str, float] = field(default_factory=dict)

    prev_flat_context: dict[str, float] = field(default_factory=dict)

    context_hash: int = 0

    evaluation_count: int = 0

    def reset(self) -> None:
        """重置状态，清空所有缓存的节点值和上下文。"""
        self.node_values.clear()
        self.prev_outputs.clear()
        self.prev_flat_context.clear()
        self.context_hash = 0
        self.evaluation_count = 0


def _json_stable_hash(value: str) -> float:
    """对字符串值生成稳定浮点哈希（用于扁平化上下文键）。"""
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
    digest = hashlib.sha256(raw).digest()[:8]
    return float(int.from_bytes(digest, "big"))


def flatten_context(context: dict[str, Any]) -> dict[str, float]:
    """将嵌套上下文展平为点分隔路径 → 值的扁平字典。



    例如 ``{"character": {"a": 3.0, "b": 4.0}}`` →

    ``{"character.a": 3.0, "character.b": 4.0}``

    """

    flat: dict[str, float] = {}

    _flatten_impl("", context, flat)

    return flat


def _flatten_impl(prefix: str, obj: Any, result: dict[str, float]) -> None:
    """递归展平嵌套字典。

    支持的类型：
    - ``dict``：递归展平子键
    - ``int | float``：直接存储
    - ``str | bool``：通过 JSON 序列化哈希为稳定数值键
    - ``list | tuple``：递归展平每个元素
    - ``None``：跳过
    - 其他类型：尝试 ``float()`` 转换，失败则跳过并记录日志
    """
    if isinstance(obj, dict):
        for key, val in obj.items():
            new_prefix = f"{prefix}.{key}" if prefix else key
            _flatten_impl(new_prefix, val, result)

    elif isinstance(obj, int | float):
        result[prefix] = float(obj)

    elif isinstance(obj, str):
        # 字符串通过 JSON 序列化生成稳定哈希键
        result[prefix] = _json_stable_hash(obj)

    elif isinstance(obj, bool):
        result[prefix] = 1.0 if obj else 0.0

    elif isinstance(obj, list | tuple):
        for i, item in enumerate(obj):
            item_prefix = f"{prefix}[{i}]"
            _flatten_impl(item_prefix, item, result)

    elif obj is None:
        pass

    else:
        with contextlib.suppress(TypeError, ValueError):
            result[prefix] = float(obj)


def compute_context_hash(context: dict[str, Any]) -> int:
    """计算上下文的稳定哈希，用于快速判断上下文是否变化。

    使用 hashlib.sha256 替代内置 ``hash()``，确保跨进程一致性。
    """
    flat = flatten_context(context)
    serialized = json.dumps(flat, sort_keys=True, ensure_ascii=False).encode("utf-8")
    digest = hashlib.sha256(serialized).digest()
    return int.from_bytes(digest[:8], "big")


def find_changed_paths(
    old_flat: dict[str, float],
    new_flat: dict[str, float],
) -> set[str]:
    """比较两个扁平上下文，返回值发生变化的路径集合。"""

    changed: set[str] = set()

    all_keys = set(old_flat) | set(new_flat)

    for key in all_keys:
        if old_flat.get(key) != new_flat.get(key):
            changed.add(key)

    return changed


def compute_affected_nodes(
    graph: DAGGraph,
    changed_paths: set[str],
) -> set[str]:
    """根据变化的上下文路径，找出图中直接受影响的 VarNode ID。



    Args:

        graph: DAG 图。

        changed_paths: 发生变化的上下文路径集合。



    Returns:

        直接受上下文变化影响的节点 ID（通常是 VarNode）。

    """

    if not changed_paths:
        return set()

    affected: set[str] = set()

    for nid, node in graph.nodes.items():
        if getattr(node, "type", None) == "var":
            path: str = getattr(node, "path", "")

            if path in changed_paths:
                affected.add(nid)

    return affected


def propagate_dirty(
    expanded_nodes: dict[str, NodeType],
    seed: set[str],
) -> set[str]:
    """从种子节点开始 BFS 传播脏标记到所有下游节点。



    Args:

        expanded_nodes: 展开后的节点集合（包含子图内联节点）。

        seed: 初始脏节点 ID 集合。



    Returns:

        所有需要重算的节点 ID（种子 + 所有下游节点）。

    """

    adj: dict[str, list[str]] = {}

    for nid in expanded_nodes:
        adj.setdefault(nid, [])

    for nid, node in expanded_nodes.items():
        refs = _node_dependencies(node)

        for ref in refs:
            if ref in adj:
                adj[ref].append(nid)

    dirty: set[str] = set(seed)

    queue: deque[str] = deque(seed)

    while queue:
        current = queue.popleft()

        for downstream in adj.get(current, []):
            if downstream not in dirty:
                dirty.add(downstream)

                queue.append(downstream)

    return dirty


def compute_required_nodes(
    expanded_nodes: dict[str, NodeType],
    output_refs: set[str],
) -> set[str]:
    """从输出引用节点反向遍历，找出所有"必要节点"（惰性求值用）。



    只有对输出有贡献的节点才会被包含在返回集中。



    Args:

        expanded_nodes: 展开后的全部节点。

        output_refs: 输出所引用的节点 ID 集合。



    Returns:

        对输出有贡献的必要节点 ID 集合。

    """

    rev_adj: dict[str, list[str]] = {}

    for nid in expanded_nodes:
        rev_adj.setdefault(nid, [])

    for nid, node in expanded_nodes.items():
        refs = _node_dependencies(node)

        rev_adj[nid].extend(refs)

    required: set[str] = set()

    queue: deque[str] = deque(output_refs)

    while queue:
        current = queue.popleft()

        if current in required:
            continue

        required.add(current)

        for dep in rev_adj.get(current, []):
            if dep not in required:
                queue.append(dep)

    return required
