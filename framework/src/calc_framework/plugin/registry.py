# SPDX-License-Identifier: AGPL-3.0
"""插件注册表。"""

from __future__ import annotations

from typing import Any

from calc_framework.dag.service import DAGService
from calc_framework.dag.templates import register_template
from calc_framework.logging import get_logger
from calc_framework.plugin.base import BasePlugin, PluginMeta

logger = get_logger(__name__)

_registry: PluginRegistry | None = None


def get_registry() -> PluginRegistry:
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
    return _registry


def list_plugins() -> list[str]:
    return get_registry().list()


class PluginRegistry:
    """全局插件注册表（单例）。

    通过 ``get_registry()`` 获取，通过 ``register()`` 注册插件。
    """

    def __init__(self) -> None:
        self._plugins: dict[str, BasePlugin] = {}

    def register(self, plugin: BasePlugin) -> None:
        meta = plugin.meta
        if meta.name in self._plugins:
            logger.warning("插件 %s 已注册，跳过", meta.name)
            return
        self._plugins[meta.name] = plugin
        logger.info("插件已注册: %s v%s", meta.name, meta.version)

    def unregister(self, name: str) -> None:
        if name in self._plugins:
            self._plugins[name].on_unload()
            del self._plugins[name]
            logger.info("插件已卸载: %s", name)

    def list(self) -> list[str]:
        return sorted(self._plugins.keys())

    def get(self, name: str) -> BasePlugin | None:
        return self._plugins.get(name)

    def apply_to_adapter(self, plugin_names: list[str], dag_service: DAGService) -> None:
        """将指定插件应用到适配器的 DAGService 上。

        每个插件的 ``on_adapter_attach()`` 被调用，同时将插件的
        变量声明、函数、模板注册到适配器。
        """
        applied: list[str] = []
        for name in plugin_names:
            plugin = self._plugins.get(name)
            if plugin is None:
                logger.warning("插件 %s 未注册，跳过", name)
                continue
            data = plugin.on_load()
            self._apply_plugin_data(data, dag_service, plugin.meta)
            plugin.on_adapter_attach(dag_service)
            applied.append(name)
            logger.info("插件已应用到适配器: %s", name)
        return

    @staticmethod
    def _apply_plugin_data(data: dict[str, Any], dag_service: DAGService, meta: PluginMeta) -> None:
        vars_data = data.get("variables", {})
        for vname, vdef in vars_data.items():
            if hasattr(dag_service, "register_variable"):
                dag_service.register_variable(vname, vdef)

        funcs = data.get("functions", {})
        for fname, fn in funcs.items():
            dag_service.register_function(fname, fn)

        templates = data.get("templates", {})
        for tname, tdef in templates.items():
            try:
                register_template(
                    tname,
                    parameters=tdef.get("parameters", []),
                    nodes=tdef.get("nodes", {}),
                    output_node=tdef.get("output_node", ""),
                    description=tdef.get("description", meta.description),
                )
            except Exception as exc:
                logger.warning("注册模板 %s 失败: %s", tname, exc)

    def clear(self) -> None:
        for plugin in list(self._plugins.values()):
            plugin.on_unload()
        self._plugins.clear()
