#!/usr/bin/env python3
"""适配包加载器 — 从适配包目录读取 meta.json 并组装 DAG 服务。"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from calc_framework.dag.serializer import dag_from_dict
from calc_framework.dag.service import DAGService

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

    @property
    def meta(self) -> dict[str, Any]:
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
