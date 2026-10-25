# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
通用 JSON 数据懒加载器。

消除各游戏适配器中重复的「全局缓存 + get + reload」模式。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Generic, TypeVar

T = TypeVar("T")


class JsonDataLoader(Generic[T]):
    """通用 JSON 数据懒加载器，带内存缓存。

    将「检查 None → 加载 → 缓存 → 返回」模式封装为可复用组件。

    Usage::

        # 定义加载逻辑
        def _load_characters() -> list[dict]:
            return load_json_file("data/characters.json", strict=True)

        # 创建加载器
        characters = JsonDataLoader(_load_characters)

        # 使用
        data = characters.get()       # 首次调用 → 加载 → 缓存
        data = characters.get()       # 后续调用 → 直接返回缓存
        characters.reload()           # 清除缓存，下次 get() 重新加载
        assert not characters.loaded  # reload 后为 False
    """

    def __init__(self, load_func: Callable[[], T]):
        """创建懒加载器。

        Args:
            load_func: 零参数加载函数，在首次 get() 时调用。
                       应返回要缓存的数据。
        """
        self._load = load_func
        self._cache: T | None = None
        self._loaded: bool = False

    @property
    def loaded(self) -> bool:
        """缓存是否已填充（上次 reload 后是否已调用过 get）。"""
        return self._loaded

    def get(self) -> T:
        """获取数据（首次调用时加载并缓存）。

        Returns:
            缓存的数据（首次调用时从 load_func 加载）
        """
        if not self._loaded:
            self._cache = self._load()
            self._loaded = True
        return self._cache  # type: ignore[return-value]

    def reload(self) -> None:
        """清除缓存，下次 get() 将重新加载。"""
        self._cache = None
        self._loaded = False
