#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""DAG 沙箱表达式求值器 — 白名单配置。

存放 `_SAFE_BUILTINS`、`_SAFE_NODE_TYPES`、`_SAFE_UNARY_OPS`、`_SAFE_BIN_OPS`、
`_GLOBAL_FUNCTIONS` 及函数注册 API。
"""

from __future__ import annotations

import ast
import math
from typing import Any

from calc_framework.logging import get_logger

logger = get_logger(__name__)


_SAFE_BUILTINS: dict[str, Any] = {
    "floor": math.floor,
    "ceil": math.ceil,
    "abs": abs,
    "sqrt": math.sqrt,
    "min": min,
    "max": max,
    "sum": lambda *args: sum(args),
    "avg": lambda *args: sum(args) / len(args) if args else 0.0,
    "count": lambda *args: float(len(args)),
    # "integral" 由 sandbox.py 导入后添加（避免循环依赖）
}

_SAFE_NODE_TYPES: frozenset[type] = frozenset(
    {
        ast.Constant,
        ast.Name,
        ast.UnaryOp,
        ast.BinOp,
        ast.Call,
        ast.Expression,
        ast.Load,
    }
)

_SAFE_UNARY_OPS: frozenset[type] = frozenset({ast.USub})

_SAFE_BIN_OPS: frozenset[type] = frozenset({ast.Add, ast.Sub, ast.Mult, ast.Div})

_GLOBAL_FUNCTIONS: dict[str, Any] = {}


def register_function(name: str, fn: Any) -> None:
    """注册一个自定义函数到 DAG 表达式沙箱。"""
    if name in _SAFE_BUILTINS:
        raise ValueError(f"函数名 {name!r} 与内置函数冲突")
    _GLOBAL_FUNCTIONS[name] = fn
    logger.info("注册自定义函数: %s", name)


def unregister_function(name: str) -> None:
    """移除已注册的自定义函数。"""
    _GLOBAL_FUNCTIONS.pop(name, None)
    logger.info("移除自定义函数: %s", name)


def clear_functions() -> None:
    """清空所有已注册的自定义函数。"""
    _GLOBAL_FUNCTIONS.clear()
    logger.debug("清空所有自定义函数")


def list_functions() -> list[str]:
    """返回所有可用函数名列表（内置 + 自定义）。"""
    return sorted(_SAFE_BUILTINS) + sorted(_GLOBAL_FUNCTIONS)


def _all_allowed_names() -> frozenset[str]:
    """返回所有允许的函数名集合。"""
    return frozenset(_SAFE_BUILTINS) | frozenset(_GLOBAL_FUNCTIONS)
