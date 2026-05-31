#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""变量 Schema 校验 — 根据 DAG 声明的变量检查 DataContext 的完整性。"""

from typing import Any

from calc_framework.dag.schema import DAGGraph
from calc_framework.errors import CalcFrameworkError


class VariableValidationError(CalcFrameworkError):
    """变量校验失败。"""


def validate_variables(graph: DAGGraph, context: dict[str, Any]) -> None:
    """校验 graph 声明的所有变量在 context 中存在且类型正确。

    Raises:
        VariableValidationError: 变量缺失或类型不匹配
    """
    for var_path, var_def in graph.variables.items():
        value = _resolve_path(context, var_path)

        if value is None and var_def.default is not None:
            continue

        if value is None:
            raise VariableValidationError(
                f"变量 {var_path!r} 未在上下文中找到且无默认值"
            )

        _check_type(var_path, value, var_def.type)


def _resolve_path(context: dict[str, Any], path: str) -> Any:
    parts = path.split(".")
    cursor: Any = context
    for part in parts:
        if isinstance(cursor, dict):
            cursor = cursor.get(part)
        else:
            return None
        if cursor is None:
            return None
    return cursor


def _check_type(var_path: str, value: Any, expected: str) -> None:
    if expected == "float" and not isinstance(value, (int, float)):
        raise VariableValidationError(
            f"变量 {var_path!r} 类型不匹配: 期望 float, 实际 {type(value).__name__}"
        )
    if expected == "int":
        if isinstance(value, bool):
            raise VariableValidationError(
                f"变量 {var_path!r} 类型不匹配: 期望 int, 实际 bool"
            )
        if not isinstance(value, int):
            raise VariableValidationError(
                f"变量 {var_path!r} 类型不匹配: 期望 int, 实际 {type(value).__name__}"
            )
    if expected == "bool" and not isinstance(value, bool):
        raise VariableValidationError(
            f"变量 {var_path!r} 类型不匹配: 期望 bool, 实际 {type(value).__name__}"
        )
    if expected == "str" and not isinstance(value, str):
        raise VariableValidationError(
            f"变量 {var_path!r} 类型不匹配: 期望 str, 实际 {type(value).__name__}"
        )
