# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""终末地 DAG 配置拆分结构测试（P2-07）。"""

from __future__ import annotations

from pathlib import Path

_MODULE_NAMES = (
    "games.endfield.calc.dag_adapter.config",
    "games.endfield.calc.dag_adapter.config_variables",
    "games.endfield.calc.dag_adapter.config_nodes",
    "games.endfield.calc.dag_adapter.config_master_graph",
)


def _line_count(module_name: str) -> int:
    module = __import__(module_name, fromlist=["__file__"])
    return len(Path(module.__file__).read_text(encoding="utf-8").splitlines())


def test_config_modules_stay_within_target() -> None:
    for module_name in _MODULE_NAMES:
        assert _line_count(module_name) <= 400, module_name


def test_config_reexports_master_graph_builder() -> None:
    from games.endfield.calc.dag_adapter import config, config_master_graph

    assert config._make_master_graph is config_master_graph._make_master_graph


def test_generated_graph_keeps_public_outputs() -> None:
    from games.endfield.calc.dag_adapter.config import generate

    graph = generate()
    assert "最终伤害" in graph.outputs
    assert "block6_env" in graph.nodes
    assert set(graph.subgraphs) == {
        "ability_bonus",
        "final_attack",
        "single_hit_damage",
        "crit_zone",
        "base_damage_block",
        "buff_debuff_block",
        "environment_block",
    }
