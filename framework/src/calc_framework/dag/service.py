#!/usr/bin/env python3
"""DAG 求值服务：加载、缓存与求值的统一入口。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from calc_framework.dag.engine import DAGResult, evaluate_graph
from calc_framework.dag.sandbox import register_function as _register_sandbox_fn
from calc_framework.dag.schema import DAGGraph
from calc_framework.dag.serializer import dag_from_dict, load_dag


class DAGService:
    """DAG 公式图的求值服务。

    封装加载、缓存与求值，提供三种构造方式：

    - ``DAGService(dag)`` — 从已构建的 DAGGraph 对象
    - ``DAGService.from_file(path)`` — 从 JSON 文件加载
    - ``DAGService.from_dict(data)`` — 从 dict 解析
    """

    def __init__(self, dag: DAGGraph):
        self._dag = dag

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
        """用给定上下文求值 DAG 图，返回包含所有输出值的 DAGResult。"""
        return evaluate_graph(self._dag, context)

    def register_function(self, name: str, fn: Any) -> None:
        """注册一个自定义函数到 DAG 表达式沙箱。

        注册后的函数可在 ``expr`` 节点的表达式中直接调用。
        """
        _register_sandbox_fn(name, fn)

    @property
    def dag(self) -> DAGGraph:
        """返回内部 DAG 图（只读）。"""
        return self._dag
