#!/usr/bin/env python3
"""DAG 求值服务：加载、缓存与求值的统一入口。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from calc_framework.dag.debugger import StepDebugger
from calc_framework.dag.engine import BlockCache, DAGResult, evaluate_graph
from calc_framework.dag.sandbox import register_function as _register_sandbox_fn
from calc_framework.dag.schema import DAGGraph
from calc_framework.dag.serializer import dag_from_dict, load_dag


def _import_graph_editor() -> tuple[Any, Any]:
    """延迟导入 graph_editor 模块（避免循环依赖）。"""
    from calc_framework.graph_editor.compiler import compile_graph
    from calc_framework.graph_editor.schema import GraphDocument
    from calc_framework.graph_editor.serializer import document_from_json
    return compile_graph, document_from_json


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

    @classmethod
    def from_graph_document(cls, doc: Any) -> DAGService:
        """从 graph_editor 的 GraphDocument 编译并创建服务。"""
        compile_graph_fn, _ = _import_graph_editor()
        dag = compile_graph_fn(doc)
        return cls(dag)

    @classmethod
    def from_graph_file(cls, path: str | Path) -> DAGService:
        """从 graph_editor 格式的 graph.json 文件加载并创建服务。"""
        import json
        compile_graph_fn, document_from_json_fn = _import_graph_editor()
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        doc = document_from_json_fn(data)
        dag = compile_graph_fn(doc)
        return cls(dag)

    def evaluate(self, context: dict[str, Any]) -> DAGResult:
        """用给定上下文求值 DAG 图，返回包含所有输出值的 DAGResult。

        使用内部 BlockCache 实现块级缓存，相同输入跳过块内求值。
        """
        return evaluate_graph(self._dag, context, block_cache=self._block_cache)

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

    @property
    def block_cache(self) -> BlockCache:
        """返回内部 BlockCache 实例。"""
        return self._block_cache

    @property
    def dag(self) -> DAGGraph:
        """返回内部 DAG 图（只读）。"""
        return self._dag
