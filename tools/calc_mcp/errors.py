# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""MCP 工具错误边界。

工具内部异常不直接抛给模型，而是转换为 ``{ok: false, error, code}``，
同时把堆栈写入 stderr 日志。
"""

from __future__ import annotations

import functools
import logging
from collections.abc import Callable
from typing import Any

from .build import BuildError
from .discovery import DiscoveryError
from .package import PackageError
from .safety import ScopeError
from .spec import SpecError
from .verify import VerifyError

logger = logging.getLogger(__name__)

_KNOWN_CODES: dict[type[BaseException], str] = {
    ScopeError: "SCOPE",
    DiscoveryError: "DISCOVERY",
    SpecError: "SPEC",
    BuildError: "BUILD",
    VerifyError: "VERIFY",
    PackageError: "PACKAGE",
    FileNotFoundError: "NOT_FOUND",
    FileExistsError: "ALREADY_EXISTS",
    OSError: "IO",
    ValueError: "INVALID_INPUT",
}


def register_error_code(exc_type: type[BaseException], code: str) -> None:
    """登记异常类型对应的稳定错误码。"""
    _KNOWN_CODES[exc_type] = code


def tool_error_boundary(fn: Callable[..., Any]) -> Callable[..., Any]:
    """包装工具函数，捕获异常并返回结构化错误。"""

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            code = "INTERNAL"
            for exc_type, candidate in _KNOWN_CODES.items():
                if isinstance(exc, exc_type):
                    code = candidate
                    break
            if code == "INTERNAL":
                logger.exception("MCP 工具 %s 执行失败", fn.__name__)
            else:
                logger.warning("MCP 工具 %s 返回业务错误: %s", fn.__name__, exc)
            return {"ok": False, "error": str(exc) or type(exc).__name__, "code": code}

    return wrapper
