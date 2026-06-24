#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""DAG 引擎异常类。"""

from __future__ import annotations

from ..errors import CalcFrameworkError


class DAGError(CalcFrameworkError):
    """DAG 引擎所有异常的基类。"""


class DAGCompileError(DAGError):
    """DAG 编译期错误（schema 校验失败、JSON 解析失败、表达式解析失败等）。"""

    def __init__(self, message: str, *, node_id: str | None = None) -> None:
        super().__init__(message)
        self.node_id = node_id


class DAGSecurityError(DAGError):
    """AST 沙箱安全违规（表达式使用了白名单外的语法）。"""

    def __init__(self, message: str, *, offending_node: str | None = None) -> None:
        super().__init__(message)
        self.offending_node = offending_node


class DAGRuntimeError(DAGError):
    """DAG 运行时错误（除零、变量未找到等）。"""


class DAGCycleError(DAGError):
    """DAG 存在循环依赖。"""
