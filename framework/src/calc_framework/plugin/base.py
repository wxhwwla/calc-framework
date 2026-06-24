# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""插件基类和元信息。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PluginMeta:
    """插件元信息。"""

    name: str

    version: str = "1.0.0"

    description: str = ""

    dependencies: list[str] = field(default_factory=list)

    author: str = ""


class BasePlugin(ABC):
    """插件基类。



    子类需实现 ``on_load()`` 返回插件数据（变量声明、子图、函数等）。

    """

    @property
    @abstractmethod
    def meta(self) -> PluginMeta:
        """meta。"""
        ...

    def on_load(self) -> dict[str, Any]:
        """返回插件加载时注册到框架的数据。



        ［可选重写］返回格式::



            {

                "variables": { "var_name": {"type": "float", "source": "computed", ...} },

                "subgraph": {"nodes": {...}, "outputs": {...}},

                "functions": {"fn_name": callable},

                "templates": {"tpl_name": {"parameters": [...], "nodes": {...}, ...}},

            }

        """

        return {}

    def on_unload(self) -> None:
        """插件卸载时的清理工作。"""

    def on_adapter_attach(self, adapter: Any) -> None:
        """当适配器加载此插件时调用（可选重写）。"""
