#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""DAG 求值服务：加载、缓存与求值的统一入口。"""



from __future__ import annotations

from pathlib import Path
from typing import Any

from calc_framework.dag.debugger import StepDebugger
from calc_framework.dag.engine import BlockCache, DAGResult, evaluate_graph
from calc_framework.dag.sandbox import register_function as _register_sandbox_fn
from calc_framework.dag.schema import DAGGraph
from calc_framework.dag.serializer import dag_from_dict, load_dag
from calc_framework.dag.state import DAGState


class DAGService:

    """DAG 公式图的求值服务。



    封装加载、缓存与求值，提供三种构造方式：



    - ``DAGService(dag)`` — 从已构建的 DAGGraph 对象

    - ``DAGService.from_file(path)`` — 从 JSON 文件加载

    - ``DAGService.from_dict(data)`` — 从 dict 解析

    """



    def __init__(self, dag: DAGGraph):

        self._dag = dag

        self._block_cache = BlockCache()

        self._dag_state = DAGState()



    @classmethod

    def from_file(cls, path: str | Path) -> DAGService:

        """从 DAG JSON 文件加载并创建服务。"""

        dag = load_dag(Path(path))

        return cls(dag)



    @classmethod

    def from_dict(cls, data: dict[str, Any]) -> DAGService:

        """从 dict 解析 DAG 并创建服务。"""

        dag = dag_from_dict(data)

        return cls(dag)



    def evaluate(self, context: dict[str, Any]) -> DAGResult:

        """用给定上下文求值 DAG 图，返回包含所有输出值的 DAGResult。



        使用内部 BlockCache 实现块级缓存，相同输入跳过块内求值。

        使用内部 DAGState 实现增量求值，仅重算上下文变化的节点。

        """

        return evaluate_graph(

            self._dag,

            context,

            block_cache=self._block_cache,

            dag_state=self._dag_state,

        )



    def register_function(self, name: str, fn: Any) -> None:

        """注册一个自定义函数到 DAG 表达式沙箱。



        注册后的函数可在 ``expr`` 节点的表达式中直接调用。

        """

        _register_sandbox_fn(name, fn)



    def step_debug(self, context: dict[str, Any]) -> StepDebugger:

        """创建分步调试器，逐步执行 DAG 图节点。



        返回 ``StepDebugger`` 实例，支持 ``step()`` / ``run_all()`` /

        ``run_to()`` / ``reset()`` 等操作。



        用法::



            debugger = svc.step_debug(context)

            while not debugger.finished:

                result = debugger.step()

                print(result.node_id, result.value)

        """

        return StepDebugger(self._dag, context)



    def invalidate_block_cache(self, block_id: str | None = None) -> None:

        """使块级缓存失效。



        Args:

            block_id: 指定块 ID，为 None 时清除全部缓存。

        """

        if block_id is None:

            self._block_cache.invalidate_all()

        else:

            self._block_cache.invalidate(block_id)



    def reset_state(self) -> None:

        """重置增量求值状态（强制下次全量求值）。"""

        self._dag_state = DAGState()

        self._block_cache = BlockCache()



    @property

    def block_cache(self) -> BlockCache:

        """返回内部 BlockCache 实例。"""

        return self._block_cache



    @property

    def dag_state(self) -> DAGState:

        """返回内部 DAGState 实例。"""

        return self._dag_state



    @property

    def dag(self) -> DAGGraph:

        """返回内部 DAG 图（只读）。"""

        return self._dag

