#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""适配包加载器 — 从适配包目录读取 meta.json 并组装 DAG 服务。"""



from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from typing import Any

from calc_framework.dag.serializer import dag_from_dict
from calc_framework.dag.service import DAGService
from calc_framework.data.attr_schema import AttributeSchema
from calc_framework.logging import get_logger

logger = get_logger(__name__)



_SUPPORTED_SCHEMA_VERSIONS = frozenset({"dag-v1"})





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

        logger.info("适配包加载成功: %s (schema=%s, version=%s)",

                      self._adapter_dir.name,

                      self._meta.get("schema_version", "?"),

                      self._meta.get("version", "?"))



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

        return fn



        """从点分隔的导入路径加载自定义函数。"""
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

            raise AdapterNotFoundError(

                f"适配器目录缺少 meta.json: {self._adapter_dir}"

            )

        raw = meta_path.read_text(encoding="utf-8")

        return json.loads(raw)

    def _validate_meta(self) -> None:

        sv = self._meta.get("schema_version", "")

        if sv not in _SUPPORTED_SCHEMA_VERSIONS:

            raise InvalidMetaError(

                f"不支持的 schema_version: {sv!r}（支持: {sorted(_SUPPORTED_SCHEMA_VERSIONS)}）"

            )

        entry = self._meta.get("entry_dag", "")

        if not entry:

            raise InvalidMetaError("meta.json 缺少必需的 entry_dag 字段")

        dag_path = self._adapter_dir / entry

        if not dag_path.is_file():

            raise AdapterNotFoundError(
                f"entry_dag 文件未找到: {dag_path}"
            )

    def _load_dag(self) -> DAGService:

        entry = self._meta["entry_dag"]

        dag_path = self._adapter_dir / entry

        if not dag_path.is_file():

            raise AdapterNotFoundError(

                f"entry_dag 文件未找到: {dag_path}"

            )

        raw = dag_path.read_text(encoding="utf-8")

        data = json.loads(raw)

        dag = dag_from_dict(data)

        return DAGService(dag)

