# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""插件系统单元测试。"""

from __future__ import annotations

import pytest

from calc_framework.dag.engine import evaluate_graph
from calc_framework.dag.serializer import dag_from_dict
from calc_framework.dag.service import DAGService
from calc_framework.plugin import list_plugins
from calc_framework.plugin.builtin import CritPlugin, DistanceDecayPlugin, DodgePlugin
from calc_framework.plugin.registry import PluginRegistry


class TestPluginRegistry:
    def test_register_and_list(self):
        reg = PluginRegistry()

        plugin = CritPlugin()

        reg.register(plugin)

        assert "crit_handler" in reg.list()

        reg.clear()

    def test_register_twice_no_error(self):
        reg = PluginRegistry()

        reg.register(CritPlugin())

        reg.register(CritPlugin())  # should not raise

        assert len(reg.list()) == 1

        reg.clear()

    def test_get_plugin(self):
        reg = PluginRegistry()

        plugin = CritPlugin()

        reg.register(plugin)

        assert reg.get("crit_handler") is plugin

        assert reg.get("nonexistent") is None

        reg.clear()

    def test_unregister(self):
        reg = PluginRegistry()

        reg.register(CritPlugin())

        reg.unregister("crit_handler")

        assert "crit_handler" not in reg.list()

        reg.clear()


class TestBuiltinPlugins:
    def test_crit_plugin_meta(self):
        plugin = CritPlugin()

        assert plugin.meta.name == "crit_handler"

        assert plugin.meta.version == "1.0.0"

    def test_crit_plugin_variables(self):
        plugin = CritPlugin()

        data = plugin.on_load()

        assert "character.crit_rate" in data["variables"]

        assert "character.crit_dmg" in data["variables"]

    def test_crit_plugin_template(self):
        plugin = CritPlugin()

        data = plugin.on_load()

        assert "crit_basic" in data["templates"]

        tpl = data["templates"]["crit_basic"]

        assert "parameters" in tpl

        assert "output_node" in tpl

    def test_dodge_plugin_meta(self):
        plugin = DodgePlugin()

        assert plugin.meta.name == "dodge_handler"

    def test_dodge_plugin_template(self):
        plugin = DodgePlugin()

        data = plugin.on_load()

        assert "dodge_check" in data["templates"]

    def test_distance_decay_plugin_meta(self):
        plugin = DistanceDecayPlugin()

        assert plugin.meta.name == "distance_decay"

    def test_distance_decay_plugin_template(self):
        plugin = DistanceDecayPlugin()

        data = plugin.on_load()

        assert "linear_distance_decay" in data["templates"]


class TestBuiltinRegistration:
    def test_builtins_registered(self):
        names = list_plugins()

        assert "crit_handler" in names

        assert "dodge_handler" in names

        assert "distance_decay" in names


class TestPluginApplyToAdapter:
    def _make_svc(self):
        from calc_framework.dag.serializer import dag_from_dict

        graph = dag_from_dict(
            {
                "schema_version": "dag-v1",
                "name": "test",
                "nodes": {"dummy": {"type": "const", "value": 0}},
                "outputs": {"dummy": {"node": "dummy", "label": "dummy"}},
            }
        )

        return DAGService(dag=graph)

    def test_apply_crit_plugin_variables(self):
        """插件 apply 不修改 DAGGraph 的 variables（变量由适配器声明）。"""

        reg = PluginRegistry()

        plugin = CritPlugin()

        reg.register(plugin)

        svc = self._make_svc()

        reg.apply_to_adapter(["crit_handler"], svc)

        graph = svc.dag

        assert "dummy" in graph.nodes

    def test_apply_crit_plugin_template_can_be_expanded(self):
        reg = PluginRegistry()

        reg.register(CritPlugin())

        reg.apply_to_adapter(["crit_handler"], self._make_svc())

        dag_json = {
            "schema_version": "dag-v1",
            "name": "test_crit_plugin",
            "variables": {
                "character.crit_rate": {"type": "float", "source": "character", "default": 0.05},
                "character.crit_dmg": {"type": "float", "source": "character", "default": 0.5},
                "user_input.is_crit": {"type": "bool", "source": "user_input", "default": False},
            },
            "nodes": {
                "crit": {
                    "template": "crit_basic",
                    "bindings": {
                        "crit_rate": "character.crit_rate",
                        "crit_dmg": "character.crit_dmg",
                        "is_crit": "user_input.is_crit",
                    },
                },
            },
            "outputs": {
                "暴击倍率": {"node": "crit", "label": "暴击倍率"},
            },
        }

        graph = dag_from_dict(dag_json)

        ctx = {"character": {"crit_rate": 0.05, "crit_dmg": 0.5}, "user_input": {"is_crit": True}}

        result = evaluate_graph(graph, ctx)

        assert result.outputs["暴击倍率"] == pytest.approx(1.5)

        reg.clear()

    def test_apply_dodge_plugin(self):
        reg = PluginRegistry()

        reg.register(DodgePlugin())

        reg.apply_to_adapter(["dodge_handler"], self._make_svc())

        dag_json = {
            "schema_version": "dag-v1",
            "name": "test_dodge",
            "variables": {
                "character.accuracy": {"type": "float", "source": "character", "default": 0.9},
                "enemy.dodge_rate": {"type": "float", "source": "enemy", "default": 0.2},
            },
            "nodes": {
                "dodge_check": {
                    "template": "dodge_check",
                    "bindings": {"accuracy": "character.accuracy", "dodge_rate": "enemy.dodge_rate"},
                },
            },
            "outputs": {
                "命中率": {"node": "dodge_check", "label": "命中率"},
            },
        }

        graph = dag_from_dict(dag_json)

        ctx = {"character": {"accuracy": 0.9}, "enemy": {"dodge_rate": 0.2}}

        result = evaluate_graph(graph, ctx)

        # max(0, 0.9 - 0.2) = 0.7

        assert result.outputs["命中率"] == pytest.approx(0.7)

        reg.clear()
