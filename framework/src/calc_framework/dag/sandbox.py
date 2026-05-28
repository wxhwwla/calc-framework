#!/usr/bin/env python3
"""AST 沙箱：解析表达式字符串并在白名单约束下安全求值。"""

from __future__ import annotations

import ast
import math
from typing import Any

from .errors import DAGCompileError, DAGRuntimeError, DAGSecurityError
from calc_framework.logging import get_logger

logger = get_logger(__name__)

_SAFE_BUILTINS: dict[str, Any] = {
    "floor": math.floor,
    "ceil": math.ceil,
    "abs": abs,
    "sqrt": math.sqrt,
    "min": min,
    "max": max,
}

_SAFE_NODE_TYPES: frozenset[type] = frozenset({
    ast.Constant,
    ast.Name,
    ast.UnaryOp,
    ast.BinOp,
    ast.Call,
    ast.Expression,
    ast.Load,
})

_SAFE_UNARY_OPS: frozenset[type] = frozenset({ast.USub})

_SAFE_BIN_OPS: frozenset[type] = frozenset({ast.Add, ast.Sub, ast.Mult, ast.Div})

_GLOBAL_FUNCTIONS: dict[str, Any] = {}


def register_function(name: str, fn: Any) -> None:
    """注册一个自定义函数到 DAG 表达式沙箱。

    注册后的函数可在 DAG ``expr`` 节点的表达式中直接调用，
    例如 ``my_func(a, b)``。

    参数:
        name: 函数名（在表达式中使用的标识符）
        fn: 可调用对象，接收位置参数并返回数值

     Raises:
        ValueError: 函数名与内置函数冲突
    """
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
    return frozenset(_SAFE_BUILTINS) | frozenset(_GLOBAL_FUNCTIONS)


def _check_node(node: ast.AST) -> None:
    """递归校验 AST 节点树是否符合白名单。"""
    tp = type(node)
    if tp is ast.Call:
        func_node = node.func
        if not isinstance(func_node, ast.Name):
            logger.warning("安全违规: 尝试调用非命名函数 %s", type(func_node).__name__)
            raise DAGSecurityError(
                f"不允许调用非命名函数: {type(func_node).__name__}",
                offending_node=type(func_node).__name__,
            )
        if func_node.id not in _all_allowed_names():
            logger.warning("安全违规: 未授权的函数调用 %s", func_node.id)
            raise DAGSecurityError(
                f"未授权的函数调用: {func_node.id}",
                offending_node=f"Call:{func_node.id}",
            )
        for arg in node.args:
            _check_node(arg)
        return

    if tp not in _SAFE_NODE_TYPES:
        logger.warning("安全违规: 禁止的语法 %s", tp.__name__)
        raise DAGSecurityError(
            f"表达式使用了禁止的语法: {tp.__name__}",
            offending_node=tp.__name__,
        )

    if tp is ast.UnaryOp:
        if type(node.op) not in _SAFE_UNARY_OPS:
            logger.warning("安全违规: 禁止的一元运算符 %s", type(node.op).__name__)
            raise DAGSecurityError(
                f"禁止的一元运算符: {type(node.op).__name__}",
                offending_node=type(node.op).__name__,
            )
        _check_node(node.operand)
    elif tp is ast.BinOp:
        if type(node.op) not in _SAFE_BIN_OPS:
            logger.warning("安全违规: 禁止的二元运算符 %s", type(node.op).__name__)
            raise DAGSecurityError(
                f"禁止的二元运算符: {type(node.op).__name__}",
                offending_node=type(node.op).__name__,
            )
        _check_node(node.left)
        _check_node(node.right)
    elif tp is ast.Expression:
        _check_node(node.body)


def _eval_node(node: ast.AST, scope: dict[str, float]) -> float:
    """在给定 scope 中递归求值 AST 节点。"""
    if isinstance(node, ast.Constant):
        return float(node.value)
    if isinstance(node, ast.Name):
        val = scope.get(node.id)
        if val is None:
            raise DAGRuntimeError(f"变量未定义: {node.id}")
        return float(val)
    if isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand, scope)
        if isinstance(node.op, ast.USub):
            return -operand
        raise DAGRuntimeError(f"不支持的一元运算符: {type(node.op).__name__}")
    if isinstance(node, ast.BinOp):
        lhs = _eval_node(node.left, scope)
        rhs = _eval_node(node.right, scope)
        try:
            if isinstance(node.op, ast.Add):
                return lhs + rhs
            if isinstance(node.op, ast.Sub):
                return lhs - rhs
            if isinstance(node.op, ast.Mult):
                return lhs * rhs
            if isinstance(node.op, ast.Div):
                return lhs / rhs
        except ZeroDivisionError:
            raise DAGRuntimeError("除零错误")
        raise DAGRuntimeError(f"不支持的二元运算符: {type(node.op).__name__}")
    if isinstance(node, ast.Call):
        func_name = node.func.id
        args = [_eval_node(a, scope) for a in node.args]
        all_funcs = {**_SAFE_BUILTINS, **_GLOBAL_FUNCTIONS}
        fn = all_funcs.get(func_name)
        if fn is None:
            raise DAGRuntimeError(f"未注册的函数: {func_name}")
        try:
            return float(fn(*args))
        except (ValueError, ZeroDivisionError) as e:
            raise DAGRuntimeError(f"函数 {func_name} 执行错误: {e}")
    if isinstance(node, ast.Expression):
        return _eval_node(node.body, scope)
    raise DAGRuntimeError(f"不支持的节点类型: {type(node).__name__}")


def parse_expr(expr_str: str) -> ast.Expression:
    """解析表达式字符串为白名单校验过的 AST 树。

    Raises:
        DAGCompileError: 表达式语法错误
        DAGSecurityError: 表达式使用了白名单外的语法
    """
    expr_str = expr_str.strip()
    if not expr_str:
        raise DAGCompileError("表达式为空")
    try:
        tree = ast.parse(expr_str, mode="eval")
    except SyntaxError as e:
        logger.warning("表达式语法错误: %s — %r", e, expr_str[:80])
        raise DAGCompileError(f"表达式语法错误: {e}")
    _check_node(tree)
    return tree


def validate_expr(expr_str: str) -> None:
    """校验表达式（不执行求值）。

    Raises:
        DAGCompileError: 表达式语法错误
        DAGSecurityError: 表达式使用了白名单外的语法
    """
    parse_expr(expr_str)


def evaluate(tree: ast.Expression, scope: dict[str, float]) -> float:
    """在白名单 scope 中求值已解析的 AST 表达式。

    Args:
        tree: parse_expr 返回的已验证 AST
        scope: 变量名 → 浮点数的映射

    Returns:
        表达式计算结果

    Raises:
        DAGRuntimeError: 运行时错误（变量缺失、除零等）
    """
    return _eval_node(tree, scope)
