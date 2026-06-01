#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""DAG 子图构建函数。

现有子图: ability_bonus / final_attack / single_hit_damage / crit_zone
块子图（Phase 1 乘区块化）: base_damage_block / buff_debuff_block / environment_block
见 ADR-0011 §3.2。

注意：所有 lhs / rhs / input 必须为字符串节点名引用，不能使用内嵌节点。
DAG 引擎 + 序列化器 + 校验器均不支持内嵌节点（str | NodeType 是未实现的遗留类型）。
常量通过 ConstNode 定义为子图内部节点，不作为参数。
"""

from __future__ import annotations

from calc_framework.dag.schema import BinaryNode as B
from calc_framework.dag.schema import ConstNode as C
from calc_framework.dag.schema import DAGOutput, DAGSubgraph, DAGVariable


def _make_ability_bonus_subgraph() -> DAGSubgraph:
    return DAGSubgraph(
        description="能力值加成 15%+6% 公式",
        parameters={
            "main_flat": DAGVariable(type="float", source="computed", description="主能力平值"),
            "sub_flat": DAGVariable(type="float", source="computed", description="副能力平值"),
            "main_pct": DAGVariable(type="float", source="computed", description="主能力百分比"),
            "sub_pct": DAGVariable(type="float", source="computed", description="副能力百分比"),
        },
        nodes={
            "const_100": C(value=100.0),
            "const_1": C(value=1.0),
            "const_0005": C(value=0.005),
            "const_0002": C(value=0.002),
            "n_main_pct_div": B(op="/", lhs="main_pct", rhs="const_100"),
            "n_main_mul": B(op="+", lhs="const_1", rhs="n_main_pct_div"),
            "n_main": B(op="*", lhs="main_flat", rhs="n_main_mul",
                        label="主能力*(1+主能力%/100)"),
            "n_sub_pct_div": B(op="/", lhs="sub_pct", rhs="const_100"),
            "n_sub_mul": B(op="+", lhs="const_1", rhs="n_sub_pct_div"),
            "n_sub": B(op="*", lhs="sub_flat", rhs="n_sub_mul",
                       label="副能力*(1+副能力%/100)"),
            "n_main_x_0005": B(op="*", lhs="n_main", rhs="const_0005"),
            "n_sub_x_0002": B(op="*", lhs="n_sub", rhs="const_0002"),
            "result": B(op="+", lhs="n_main_x_0005", rhs="n_sub_x_0002",
                        label="能力值加成 = main*0.005 + sub*0.002"),
        },
        outputs={
            "能力值加成": DAGOutput(node="result", label="能力值加成"),
        },
    )


def _make_final_attack_subgraph() -> DAGSubgraph:
    return DAGSubgraph(
        description="最终攻击力 = 中间*(1+能力值加成)",
        parameters={
            "char_base_atk": DAGVariable(type="float", source="character", description="角色基础攻击力"),
            "weapon_base_atk": DAGVariable(type="float", source="weapon", description="武器基础攻击力"),
            "atk_bonus": DAGVariable(type="float", source="weapon", description="攻击力+ 小数加成"),
            "additional_atk": DAGVariable(type="float", source="weapon", description="附加攻击力+ 平值"),
            "equip_flat_atk": DAGVariable(type="float", source="equipment", description="装备平铺攻击力"),
            "ability_bonus": DAGVariable(type="float", source="computed", description="能力值加成"),
        },
        nodes={
            "const_1": C(value=1.0),
            "n_base_atk": B(op="+", lhs="char_base_atk", rhs="weapon_base_atk",
                            label="基础攻击力 = 角色+武器"),
            "n_add_one": B(op="+", lhs="const_1", rhs="atk_bonus"),
            "n_atk_bonus_part": B(op="*", lhs="n_add_one", rhs="n_base_atk",
                                  label="攻击加成攻击力 = 基础*(1+攻击力+)"),
            "n_add_atk_equip": B(op="+", lhs="additional_atk", rhs="equip_flat_atk"),
            "n_mid_atk": B(op="+", lhs="n_atk_bonus_part", rhs="n_add_atk_equip",
                          label="中间攻击力 = 攻击加成攻击力+附加+装备"),
            "n_ability_one": B(op="+", lhs="const_1", rhs="ability_bonus"),
            "result": B(op="*", lhs="n_mid_atk", rhs="n_ability_one",
                        label="最终攻击力 = 中间*(1+能力值加成)"),
        },
        outputs={
            "最终攻击力": DAGOutput(node="result", label="最终攻击力"),
        },
    )


def _make_single_hit_damage_subgraph() -> DAGSubgraph:
    return DAGSubgraph(
        description="单段伤害 = 最终攻击力 * 技能倍率",
        parameters={
            "final_attack": DAGVariable(type="float", source="computed", description="最终攻击力"),
            "skill_mult": DAGVariable(type="float", source="computed", description="技能倍率"),
        },
        nodes={
            "result": B(op="*", lhs="final_attack", rhs="skill_mult",
                        label="单段伤害 = 最终攻击力 * 技能倍率"),
        },
        outputs={
            "单段伤害": DAGOutput(node="result", label="单段伤害"),
        },
    )


def _make_crit_zone_subgraph() -> DAGSubgraph:
    return DAGSubgraph(
        description="暴击区 = 1 + 暴击率*(暴击伤害-1)",
        parameters={
            "crit_rate": DAGVariable(type="float", source="character", description="暴击率"),
            "crit_damage": DAGVariable(type="float", source="character", description="暴击伤害"),
        },
        nodes={
            "const_1": C(value=1.0),
            "n_crit_dmg_minus_one": B(op="-", lhs="crit_damage", rhs="const_1"),
            "n_crit_part": B(op="*", lhs="crit_rate", rhs="n_crit_dmg_minus_one"),
            "result": B(op="+", lhs="const_1", rhs="n_crit_part",
                        label="暴击区 = 1 + 暴击率*(暴击伤害-1)"),
        },
        outputs={
            "暴击区": DAGOutput(node="result", label="暴击区"),
        },
    )


def _make_base_damage_block_subgraph() -> DAGSubgraph:
    return DAGSubgraph(
        description="基础伤害块 = 最终攻击力 * 技能倍率 * 暴击区",
        parameters={
            "final_attack": DAGVariable(type="float", source="computed", description="最终攻击力"),
            "skill_mult": DAGVariable(type="float", source="computed", description="技能倍率"),
            "crit_zone": DAGVariable(type="float", source="computed", description="暴击区"),
        },
        nodes={
            "n_single_hit": B(op="*", lhs="final_attack", rhs="skill_mult",
                              label="单段基础伤害"),
            "result": B(op="*", lhs="n_single_hit", rhs="crit_zone",
                        label="暴击后伤害 = 单段基础 * 暴击区"),
        },
        outputs={
            "暴击后伤害": DAGOutput(node="result", label="暴击后伤害"),
        },
    )


def _make_buff_debuff_block_subgraph() -> DAGSubgraph:
    return DAGSubgraph(
        description="增益减益块：7 乘区连乘",
        parameters={
            "damage_after_crit": DAGVariable(type="float", source="computed", description="暴击后伤害"),
            "zone_dmg_bonus": DAGVariable(type="float", source="computed", description="伤害加成区"),
            "zone_dmg_reduc": DAGVariable(type="float", source="computed", description="伤害减免区"),
            "zone_amp": DAGVariable(type="float", source="computed", description="增幅区"),
            "zone_weak": DAGVariable(type="float", source="computed", description="虚弱区"),
            "zone_shelter": DAGVariable(type="float", source="computed", description="庇护区"),
            "zone_fragile": DAGVariable(type="float", source="computed", description="脆弱区"),
            "zone_vuln": DAGVariable(type="float", source="computed", description="易伤区"),
        },
        nodes={
            "n_6": B(op="*", lhs="zone_vuln", rhs="zone_fragile"),
            "n_5": B(op="*", lhs="zone_shelter", rhs="n_6"),
            "n_4": B(op="*", lhs="zone_weak", rhs="n_5"),
            "n_3": B(op="*", lhs="zone_amp", rhs="n_4"),
            "n_2": B(op="*", lhs="zone_dmg_reduc", rhs="n_3"),
            "mult": B(op="*", lhs="zone_dmg_bonus", rhs="n_2", label="7 乘区连乘"),
            "result": B(op="*", lhs="damage_after_crit", rhs="mult",
                        label="增益减益后伤害"),
        },
        outputs={
            "增益减益后伤害": DAGOutput(node="result", label="增益减益后伤害"),
        },
    )


def _make_environment_block_subgraph() -> DAGSubgraph:
    return DAGSubgraph(
        description="环境乘区块：防御减伤 * 失衡易伤 * 抗性 * 非主控减伤 * 连击增伤 * 特殊乘区",
        parameters={
            "damage_after_buff": DAGVariable(type="float", source="computed", description="增益减益后伤害"),
            "enemy_defense": DAGVariable(type="float", source="enemy", description="敌方防御值"),
            "zone_imbal": DAGVariable(type="float", source="computed", description="失衡易伤区"),
            "zone_res": DAGVariable(type="float", source="computed", description="抗性区"),
            "zone_ncr": DAGVariable(type="float", source="computed", description="非主控减伤区"),
            "zone_combo": DAGVariable(type="float", source="computed", description="连击增伤区"),
            "zone_special": DAGVariable(type="float", source="computed", description="特殊乘区"),
        },
        nodes={
            "const_100": C(value=100.0),
            "n_def_add": B(op="+", lhs="const_100", rhs="enemy_defense"),
            "defense_reduction": B(op="/", lhs="const_100", rhs="n_def_add",
                                   label="防御减伤 = 100/(100+防)"),
            "n_env_6": B(op="*", lhs="zone_special", rhs="zone_combo"),
            "n_env_5": B(op="*", lhs="zone_ncr", rhs="n_env_6"),
            "n_env_4": B(op="*", lhs="zone_res", rhs="n_env_5"),
            "n_env_3": B(op="*", lhs="zone_imbal", rhs="n_env_4"),
            "env_mult": B(op="*", lhs="defense_reduction", rhs="n_env_3",
                          label="环境 6 乘区连乘"),
            "result": B(op="*", lhs="damage_after_buff", rhs="env_mult",
                        label="最终伤害"),
        },
        outputs={
            "最终伤害": DAGOutput(node="result", label="最终伤害"),
            "防御区": DAGOutput(node="defense_reduction", label="防御区"),
        },
    )
