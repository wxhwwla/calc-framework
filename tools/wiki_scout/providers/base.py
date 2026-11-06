# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""数据源 provider 基类 — fetch 与 parse 分离，便于离线测试与重复解析。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..fetcher import Fetcher


class BaseProvider(ABC):
    """Wiki 数据源 provider。

    子类需要实现：
    - `fetch`：只负责抓取原始响应，返回可 JSON 序列化的 dict。
    - `parse`：只依赖 `fetch` 的结果，不访问网络。

    这样测试可以用离线夹具直接验证 `parse`，也支持先抓取、后反复解析。
    """

    name: str = ""
    description: str = ""

    @abstractmethod
    def fetch(
        self,
        fetcher: Fetcher,
        *,
        limit: int | None = None,
        refresh: bool = False,
    ) -> dict[str, Any]:
        """抓取原始数据。"""

    @abstractmethod
    def parse(self, raw: dict[str, Any]) -> dict[str, Any]:
        """把原始数据解析为标准化输出。"""

    def run(
        self,
        fetcher: Fetcher,
        *,
        limit: int | None = None,
        refresh: bool = False,
    ) -> dict[str, Any]:
        """抓取并解析。"""
        return self.parse(self.fetch(fetcher, limit=limit, refresh=refresh))
