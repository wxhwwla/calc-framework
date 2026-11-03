#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""终末地 DAG 主图构建（P2-07 从 ``config.py`` 拆出）。

6 块架构（ADR-0011 §3.2）：属性块 / 攻击力块 / 暴击块 / 基础伤害块 /
增益减益块 / 环境乘区块，通过 CallNode 链式绑定串联。
"""

from __future__ import annotations

from calc_framework.dag.schema import DAGGraph, DAGOutput

from ._subgraph_builders import (
    _make_ability_bonus_subgraph,
    _make_base_damage_block_subgraph,
    _make_buff_debuff_block_subgraph,
    _make_crit_zone_subgraph,
    _make_environment_block_subgraph,
    _make_final_attack_subgraph,
    _make_single_hit_damage_subgraph,
)
from .config_nodes import _make_nodes
from .config_variables import _make_variables


def _make_outputs() -> dict[str, DAGOutput]:
    """构建主图输出表。"""
    return {
        "能力值加成": DAGOutput(node="block1_ability", label="能力值加成"),
        "最终攻击力": DAGOutput(node="block2_attack", label="最终攻击力", is_primary=True),
        "最终伤害": DAGOutput(node="block6_env", label="最终伤害", is_primary=True),
        "暴击区": DAGOutput(node="block3_crit", label="暴击区"),
        "伤害加成区": DAGOutput(node="zone_dmg_bonus", label="伤害加成区"),
        "伤害减免区": DAGOutput(node="zone_dmg_reduc", label="伤害减免区"),
        "增幅区": DAGOutput(node="zone_amp", label="增幅区"),
        "虚弱区": DAGOutput(node="zone_weak", label="虚弱区"),
        "庇护区": DAGOutput(node="zone_shelter", label="庇护区"),
        "脆弱区": DAGOutput(node="zone_fragile", label="脆弱区"),
        "易伤区": DAGOutput(node="zone_vuln", label="易伤区"),
        "防御区": DAGOutput(node="block6_env.defense_reduction", label="防御区"),
        "失衡易伤区": DAGOutput(node="zone_imbal", label="失衡易伤区"),
        "抗性区": DAGOutput(node="zone_res", label="抗性区"),
        "非主控减伤区": DAGOutput(node="zone_ncr", label="非主控减伤区"),
        "连击增伤区": DAGOutput(node="zone_combo", label="连击增伤区"),
        "特殊乘区": DAGOutput(node="zone_special", label="特殊乘区"),
        "基础伤害区": DAGOutput(node="block4_base", label="基础伤害区"),
        "力量最终值": DAGOutput(node="attr_力量_total", label="力量最终值"),
        "敏捷最终值": DAGOutput(node="attr_敏捷_total", label="敏捷最终值"),
        "智识最终值": DAGOutput(node="attr_智识_total", label="智识最终值"),
        "意志最终值": DAGOutput(node="attr_意志_total", label="意志最终值"),
        "基础生命值": DAGOutput(node="char_base_hp", label="基础生命值"),
        "基础防御力": DAGOutput(node="char_base_def", label="基础防御力"),
        "武器精炼主能力值加成": DAGOutput(node="weapon_refine_main_attr", label="武器精炼主能力值加成"),
        "武器精炼附加攻击力加成": DAGOutput(node="weapon_refine_add_atk", label="武器精炼附加攻击力加成"),
    }


def _make_master_graph() -> DAGGraph:
    """构建主 DAG 图：6 块架构（属性/攻击力/暴击/基础伤害/增益减益/环境乘区）。"""
    return DAGGraph(
        schema_version="dag-v1",
        name="终末地伤害公式（完整版）",
        description=(
            "终末地 15 乘区完整伤害公式 DAG。"
            "6 块架构（ADR-0011）：属性块/攻击力块/暴击块/"
            "基础伤害块/增益减益块/环境乘区块。"
        ),
        variables=_make_variables(),
        subgraphs={
            "ability_bonus": _make_ability_bonus_subgraph(),
            "final_attack": _make_final_attack_subgraph(),
            "single_hit_damage": _make_single_hit_damage_subgraph(),
            "crit_zone": _make_crit_zone_subgraph(),
            "base_damage_block": _make_base_damage_block_subgraph(),
            "buff_debuff_block": _make_buff_debuff_block_subgraph(),
            "environment_block": _make_environment_block_subgraph(),
        },
        nodes=_make_nodes(),
        outputs=_make_outputs(),
    )
