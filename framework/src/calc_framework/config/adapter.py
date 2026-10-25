#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""适配包加载器 — 从适配包目录读取 meta.json 并组装 DAG 服务。"""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from typing import Any

from ..dag.serializer import dag_from_dict
from ..dag.service import DAGService
from ..data.attr_schema import AttributeSchema
from ..logging import get_logger

logger = get_logger(__name__)


_SUPPORTED_SCHEMA_VERSIONS = frozenset({"dag-v1"})


def _promote_subgraph_user_inputs(dag: Any) -> None:
    """将子图中未连线的 user_input 参数提升为顶层 variables。

    子图 parameters 只在子图内部可见，但布局编辑器、ComputeSheet、Web API
    等外部消费者需要从顶层 variables 中发现可输入的变量。

    只有**未连线**的 user_input 参数才需要提升——已连线的参数由上游节点提供值。

    递归检查所有层级的 CallNode（包括嵌套子图内的 CallNode）。

    Args:
        dag: DAGGraph 实例，会被原地修改
    """
    # 递归收集所有 CallNode 的绑定信息
    # bindings[param_id] == "" 表示未连线，需要提升
    call_bindings: dict[str, dict[str, str]] = {}  # {subgraph_name: {param_id: target}}

    def _collect_bindings(nodes: dict) -> None:
        for node in nodes.values():
            if hasattr(node, "subgraph") and hasattr(node, "bindings"):
                call_bindings[node.subgraph] = node.bindings

    # 顶层 CallNode
    _collect_bindings(dag.nodes)

    # 嵌套子图内的 CallNode
    for sub_sg in dag.subgraphs.values():
        _collect_bindings(sub_sg.nodes)

    for sub_name, sub_sg in dag.subgraphs.items():
        bindings = call_bindings.get(sub_name, {})

        for param_id, param_var in sub_sg.parameters.items():
            if param_var.source != "user_input":
                continue

            # 已连线的参数由上游节点提供值，不需要用户输入
            if bindings.get(param_id, ""):
                continue

            # 优先使用节点标签，回退到节点 ID
            node_obj = sub_sg.nodes.get(param_id)
            node_label = getattr(node_obj, "label", "") or param_id

            var_path = _build_variable_path(sub_name, node_label)

            if var_path not in dag.variables:
                dag.variables[var_path] = type(param_var)(
                    type=param_var.type,
                    source="user_input",
                    description=param_var.description or f"{sub_name}.{node_label}",
                    default=param_var.default,
                    min=param_var.min,
                    max=param_var.max,
                )
                logger.debug("提升子图参数为顶层变量: %s → %s", f"{sub_name}.{node_label}", var_path)


def _build_variable_path(sub_name: str, param_id: str) -> str:
    """为提升的子图参数构建可读变量路径。

    Args:
        sub_name: 子图名称（如 ``@模拟计算/模拟计算_node_4674dc50``）
        param_id: 参数节点 ID（如 ``node_d69e9b24``）

    Returns:
        变量路径（如 ``模拟计算.node_d69e9b24``）
    """
    readable = sub_name.split("/", 1)[1] if "/" in sub_name else sub_name

    if "_node_" in readable:
        readable = readable.split("_node_")[0]

    readable = readable.lstrip("@")

    return f"{readable}.{param_id}"


class AdapterError(Exception):
    """适配器通用错误。"""


class AdapterNotFoundError(AdapterError):
    """适配器资源未找到。"""


class InvalidMetaError(AdapterError):
    """meta.json 格式或字段无效。"""


class AdapterPackage:
    """游戏适配包。



    从一个包含 ``meta.json`` 的目录加载适配器配置，

    提供 DAGService、元信息和数据加载器。

    """

    def __init__(self, adapter_dir: str | Path):
        self._adapter_dir = Path(os.fspath(adapter_dir).rstrip("/\\"))

        self._meta: dict[str, Any] = self._load_meta()

        self._validate_meta()

        self._dag_service: DAGService | None = None

        self._attr_schema: AttributeSchema | None = None

        self._load_functions()

        self._load_attr_schema()

        logger.info(
            "适配包加载成功: %s (schema=%s, version=%s)",
            self._adapter_dir.name,
            self._meta.get("schema_version", "?"),
            self._meta.get("version", "?"),
        )

    def register_function(self, name: str, fn: Any) -> None:
        """注册一个自定义函数到适配包的 DAG 表达式沙箱。



        委托给 ``DAGService.register_function``，在适配包层面暴露。

        """

        self.dag_service.register_function(name, fn)

    @property
    def attr_schema(self) -> AttributeSchema | None:
        """attr_schema。"""
        return self._attr_schema

    def _load_attr_schema(self) -> None:
        """加载属性 schema 文件。"""
        ref = self._meta.get("attr_schema")

        if not ref:
            return

        schema_path = self._adapter_dir / ref

        if not schema_path.is_file():
            logger.warning("attr_schema 文件未找到: %s", schema_path)

            return

        try:
            raw = schema_path.read_text(encoding="utf-8")

            data = json.loads(raw)

            self._attr_schema = AttributeSchema.from_dict(data)

        except Exception as exc:
            logger.warning("加载 attr_schema 失败: %s", exc)

    def _load_functions(self) -> None:
        """从 ``meta.json`` 的 ``functions`` 字段加载自定义函数。



        ``meta.json`` 可选字段，格式::



            "functions": {

                "clamp": "functions.py",

                "calc_bonus": "extras/math.py"

            }



        key 为函数名（DAG 表达式中使用的标识符），

        value 为相对于适配包目录的 Python 文件路径。

        该文件**顶层定义**的同名函数将被注册到 DAG 沙箱。



        也支持点分隔的 Python 导入路径格式（当 value 不含 ``.py`` 时）：

            "my_func": "my_game.functions.my_func"

        """

        funcs: dict[str, str] = self._meta.get("functions", {})

        if not funcs:
            return

        for name, ref in funcs.items():
            try:
                if ref.endswith(".py"):
                    fn = self._load_function_from_file(name, ref)

                else:
                    fn = self._load_function_from_dotted(name, ref)

                self.dag_service.register_function(name, fn)

                logger.info("从 meta.json 加载自定义函数: %s -> %s", name, ref)

            except Exception as exc:
                logger.warning("加载自定义函数失败 %s -> %s: %s", name, ref, exc)

    def _load_function_from_file(self, name: str, file_path: str) -> Any:
        """从 .py 文件加载自定义函数。"""

        full_path = self._adapter_dir / file_path

        if not full_path.is_file():
            raise FileNotFoundError(f"函数文件未找到: {full_path}")

        spec = importlib.util.spec_from_file_location(f"_adapter_fn_{name}", full_path)

        if spec is None or spec.loader is None:
            raise ImportError(f"无法加载函数文件: {full_path}")

        mod = importlib.util.module_from_spec(spec)

        spec.loader.exec_module(mod)

        fn = getattr(mod, name)

        if not callable(fn):
            raise TypeError(f"{name} 不是可调用对象")

        """从点分隔的导入路径加载自定义函数。"""
        return fn

    def _load_function_from_dotted(self, name: str, dotted_path: str) -> Any:
        parts = dotted_path.rsplit(".", 1)

        if len(parts) != 2:
            raise ValueError(f"无效的导入路径: {dotted_path}")

        module_path, func_name = parts

        import importlib

        mod = importlib.import_module(module_path)

        fn = getattr(mod, func_name)

        if not callable(fn):
            raise TypeError(f"{func_name} 不是可调用对象")

        return fn

    @property
    def meta(self) -> dict[str, Any]:
        """meta。"""

        return dict(self._meta)

    @property
    def dag_service(self) -> DAGService:
        if self._dag_service is None:
            self._dag_service = self._load_dag()

        return self._dag_service

    def _load_meta(self) -> dict[str, Any]:
        meta_path = self._adapter_dir / "meta.json"

        if not meta_path.is_file():
            raise AdapterNotFoundError(f"适配器目录缺少 meta.json: {self._adapter_dir}")

        raw = meta_path.read_text(encoding="utf-8")

        return json.loads(raw)

    def _validate_meta(self) -> None:
        sv = self._meta.get("schema_version", "")

        if sv not in _SUPPORTED_SCHEMA_VERSIONS:
            raise InvalidMetaError(f"不支持的 schema_version: {sv!r}（支持: {sorted(_SUPPORTED_SCHEMA_VERSIONS)}）")

        entry = self._meta.get("entry_dag", "")

        if not entry:
            raise InvalidMetaError("meta.json 缺少必需的 entry_dag 字段")

        dag_path = self._adapter_dir / entry

        if not dag_path.is_file():
            raise AdapterNotFoundError(f"entry_dag 文件未找到: {dag_path}")

    def _load_dag(self) -> DAGService:
        entry = self._meta["entry_dag"]

        dag_path = self._adapter_dir / entry

        if not dag_path.is_file():
            raise AdapterNotFoundError(f"entry_dag 文件未找到: {dag_path}")

        raw = dag_path.read_text(encoding="utf-8")

        data = json.loads(raw)

        dag = dag_from_dict(data)

        # 提升子图 user_input 参数为顶层变量
        # 子图 parameters 只在子图内部可见，布局编辑器/ComputeSheet/Web API 需要顶层 variables
        _promote_subgraph_user_inputs(dag)

        return DAGService(dag)
