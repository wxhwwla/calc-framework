#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""Schema 校验器 — 使用 data_pipeline 的 schema_check 验证 JSON 数据。

在隔离环境中执行校验，不会修改任何真实数据文件。
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from tools.data_pipeline.schema import EntitySchema
from tools.data_pipeline.validators.schema_check import (
    validate as _validate_entity,
    validate_all as _validate_all,
    SchemaError,
)


@dataclass
class EntityError:
    """单个实体的校验错误。"""
    index: int
    name: str
    errors: List[str]


@dataclass
class ValidationResult:
    """完整校验结果。"""
    entities: List[EntityError] = field(default_factory=list)
    parse_error: Optional[str] = None

    @property
    def passed(self) -> bool:
        if self.parse_error:
            return False
        return all(not e.errors for e in self.entities)

    @property
    def total_entities(self) -> int:
        return len(self.entities)

    @property
    def total_errors(self) -> int:
        return sum(len(e.errors) for e in self.entities)


class Validator:
    """Schema 校验器。

    使用 data_pipeline 的 schema_check 模块校验 EntitySchema 格式的数据。
    支持从文件或内存数据校验。
    """
    __test__ = False  # 防止 pytest 自动发现

    def validate_file(self, path: str | Path) -> ValidationResult:
        """读取并校验 JSON 文件。

        Args:
            path: JSON 文件路径

        Returns:
            ValidationResult 包含所有校验错误
        """
        try:
            data = self._load_json(path)
        except ValueError as e:
            return ValidationResult(parse_error=str(e))

        return self.validate(data)

    def validate(self, data: List[Dict[str, Any]]) -> ValidationResult:
        """校验内存中的 EntitySchema 列表。

        Args:
            data: 实体列表（EntitySchema）

        Returns:
            ValidationResult 包含所有校验错误
        """
        if not data:
            return ValidationResult(entities=[
                EntityError(index=0, name="(空)", errors=["数据列表为空"]),
            ])

        results = _validate_all(data, strict=True)
        entities = []
        for idx, errs in results:
            name = data[idx].get("名称", f"[{idx}]") if idx < len(data) else f"[{idx}]"
            entities.append(EntityError(
                index=idx,
                name=str(name),
                errors=errs,
            ))

        return ValidationResult(entities=entities)

    @staticmethod
    def _load_json(path: str | Path) -> List[Dict[str, Any]]:
        """读取 JSON 文件并解析为实体列表。"""
        path = Path(path)
        if not path.exists():
            raise ValueError(f"文件不存在: {path}")

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            return [data]
        if isinstance(data, list):
            if not data:
                return []
            if isinstance(data[0], dict):
                return data

        raise ValueError(
            f"不支持的 JSON 格式：顶层须为对象或对象数组，"
            f"实际类型 {type(data).__name__}"
        )
