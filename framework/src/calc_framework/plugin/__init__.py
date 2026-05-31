# SPDX-License-Identifier: AGPL-3.0
"""插件模块化系统 — 可插拔的游戏机制组件。

插件可以通过 ``PluginRegistry`` 注册，提供 DAG 子图、自定义函数、
变量声明和生命周期钩子。

内置插件在首次导入时自动注册。"""

from __future__ import annotations

from calc_framework.plugin.base import BasePlugin, PluginMeta
from calc_framework.plugin.builtin import register_builtin_plugins
from calc_framework.plugin.registry import PluginRegistry, get_registry, list_plugins

# 自动注册内置插件
register_builtin_plugins()

__all__ = [
    "BasePlugin",
    "PluginMeta",
    "PluginRegistry",
    "get_registry",
    "list_plugins",
]
