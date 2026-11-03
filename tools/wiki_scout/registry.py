# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""Provider 注册表 — 新增数据源只需在 providers 包中 import 一次。"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .providers.base import BaseProvider

_PROVIDERS: dict[str, type[BaseProvider]] = {}


def register_provider(cls: type[BaseProvider]) -> type[BaseProvider]:
    """注册 provider 类（可作装饰器使用）。"""
    if not cls.name:
        raise ValueError(f"{cls.__name__} 缺少 name")
    _PROVIDERS[cls.name] = cls
    return cls


def get_provider(name: str) -> BaseProvider:
    """按名称实例化 provider。"""
    cls = _PROVIDERS.get(name)
    if cls is None:
        available = "、".join(sorted(_PROVIDERS)) or "（无）"
        raise KeyError(f"未知 provider: {name}；可用: {available}")
    return cls()


def list_providers() -> dict[str, str]:
    """返回 {名称: 描述}。"""
    return {name: cls.description for name, cls in sorted(_PROVIDERS.items())}
