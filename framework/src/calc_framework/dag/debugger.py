# SPDX-License-Identifier: AGPL-3.0
"""DAG 分步调试器 — 逐步执行节点、查看中间值。



用法::



    from calc_framework.dag.debugger import StepDebugger



    debugger = StepDebugger(dag_graph, context)

    while not debugger.finished:

        result = debugger.step()

        print(result.node_id, result.value)



    # 带断点的全自动模式

    debugger.reset()

    debugger.add_breakpoint("some_node")

    results = debugger.run_all()  # 停在断点处

"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

from calc_framework.dag.engine import _apply_defaults, _eval_single_node, topological_sort
from calc_framework.dag.schema import DAGGraph
from calc_framework.dag.subgraph import expand_subgraphs
from calc_framework.logging import get_logger

logger = get_logger(__name__)


class StepStatus(Enum):
    """单步执行结果状态。"""

    STEPPED = auto()

    BREAKPOINT = auto()


@dataclass
class StepResult:
    """单步执行的结果。"""

    node_id: str

    value: float

    status: StepStatus

    node_type: str = ""


@dataclass
class NodeInfo:
    """节点元信息（类型 + 标签 + 描述）。"""

    type: str = ""

    label: str = ""

    description: str = ""


class StepDebugger:
    """DAG 分步调试器。



    构造后自动展开子图并拓扑排序，然后可通过 ``step()`` /

    ``run_to()`` / ``run_all()`` 逐步或批量求值。

    """

    def __init__(self, dag: DAGGraph, context: dict[str, Any]) -> None:
        self._dag = dag

        self._context = _apply_defaults(dag, context)

        self._expanded = expand_subgraphs(dag)

        self._execution_order = topological_sort(self._expanded)

        self._total = len(self._execution_order)

        self._node_values: dict[str, float] = {}

        self._current_index = 0

        self._breakpoints: set[str] = set()

    # ── 执行控制 ────────────────────────────────────────

    def step(self) -> StepResult | None:
        """执行下一个节点。所有节点执行完毕时返回 ``None``。"""

        if self._current_index >= self._total:
            return None

        nid = self._execution_order[self._current_index]

        node = self._expanded.nodes[nid]

        value = _eval_single_node(node, self._node_values, self._context)

        self._node_values[nid] = value

        self._current_index += 1

        is_breakpoint = nid in self._breakpoints

        status = StepStatus.BREAKPOINT if is_breakpoint else StepStatus.STEPPED

        result = StepResult(
            node_id=nid,
            value=value,
            status=status,
            node_type=type(node).__name__.replace("Node", "").lower(),
        )

        logger.debug("调试器 step: %s = %s (%s)", nid, value, status.name)

        return result

    def run_to(self, node_id: str) -> list[StepResult]:
        """执行直到指定节点（含该节点）。遇到断点即停止。



        Raises:

            ValueError: 节点不在执行顺序中（可能已被展开为子图节点）

        """

        if node_id not in self._execution_order:
            raise ValueError(f"节点 {node_id!r} 不在执行顺序中")

        results: list[StepResult] = []

        while self._current_index < self._total:
            nid = self._execution_order[self._current_index]

            result = self.step()

            if result is not None:
                results.append(result)

                if result.status == StepStatus.BREAKPOINT:
                    break

            if nid == node_id:
                break

        return results

    def run_all(self) -> list[StepResult]:
        """执行所有剩余节点。遇到断点即停止。"""

        results: list[StepResult] = []

        while not self.finished:
            result = self.step()

            if result is None:
                break

            results.append(result)

            if result.status == StepStatus.BREAKPOINT:
                break

        return results

    def reset(self) -> None:
        """重置执行状态到初始。"""

        self._node_values = {}

        self._current_index = 0

        logger.debug("调试器已重置")

    # ── 断点 ────────────────────────────────────────────

    def add_breakpoint(self, node_id: str) -> None:
        """在指定节点设置断点。"""

        self._breakpoints.add(node_id)

        logger.debug("断点已设置: %s", node_id)

    def remove_breakpoint(self, node_id: str) -> None:
        """移除指定节点的断点。"""

        self._breakpoints.discard(node_id)

    def list_breakpoints(self) -> list[str]:
        """返回当前所有断点列表。"""

        return sorted(self._breakpoints)

    def clear_breakpoints(self) -> None:
        """清除所有断点。"""

        self._breakpoints.clear()

    # ── 查询 ────────────────────────────────────────────

    @property
    def finished(self) -> bool:
        """是否所有节点已执行完毕。"""

        return self._current_index >= self._total

    @property
    def progress(self) -> tuple[int, int]:
        """(已执行节点数, 总节点数)"""

        return (self._current_index, self._total)

    @property
    def node_values(self) -> dict[str, float]:
        """当前已执行的节点值。"""

        return dict(self._node_values)

    @property
    def outputs(self) -> dict[str, float]:
        """已完成的输出值（仅全部执行完成后有完整数据）。"""

        result: dict[str, float] = {}

        for oid, odef in self._expanded.outputs.items():
            ref = odef.node

            if ref in self._node_values:
                result[oid] = self._node_values[ref]

        return result

    def peek(self) -> str | None:
        """查看下一个待执行节点 ID，无可执行节点时返回 ``None``。"""

        if self._current_index >= self._total:
            return None

        return self._execution_order[self._current_index]

    def get_node_info(self, node_id: str) -> NodeInfo | None:
        """获取节点的元信息（类型/标签/描述）。"""

        expanded = self._expanded

        if node_id not in expanded.nodes:
            return None

        node = expanded.nodes[node_id]

        return NodeInfo(
            type=type(node).__name__.replace("Node", "").lower(),
            label=getattr(node, "label", ""),
            description=getattr(node, "description", ""),
        )

    @property
    def execution_order(self) -> list[str]:
        """全部节点的执行顺序（只读）。"""

        return list(self._execution_order)
