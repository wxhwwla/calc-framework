#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""DAG 子图构建函数。

现有子图: ability_bonus / final_attack / single_hit_damage / defense_reduction / crit_zone
块子图（Phase 1 乘区块化）: base_damage_block / buff_debuff_block / environment_block
见 ADR-0011 §3.2。
"""

from __future__ import annotations

from calc_framework.dag.schema import (
    BinaryNode,
    ConstNode,
    DAGOutput,
    DAGSubgraph,
)


def _make_ability_bonus_subgraph() -> DAGSubgraph:
    return DAGSubgraph(
        name="ability_bonus",
        inputs=["main_flat", "sub_flat", "main_pct", "sub_pct"],
        nodes={
            "main": BinaryNode(
                type="binary", op="*",
                lhs="main_flat",
                rhs=BinaryNode(
                    type="binary", op="+",
                    lhs=ConstNode(type="const", value=1.0),
                    rhs=BinaryNode(
                        type="binary", op="/",
                        lhs="main_pct",
                        rhs=ConstNode(type="const", value=100.0),
                    ),
                ),
                label="主能力*(1+主能力%/100)",
            ),
            "sub": BinaryNode(
                type="binary", op="*",
                lhs="sub_flat",
                rhs=BinaryNode(
                    type="binary", op="+",
                    lhs=ConstNode(type="const", value=1.0),
                    rhs=BinaryNode(
                        type="binary", op="/",
                        lhs="sub_pct",
                        rhs=ConstNode(type="const", value=100.0),
                    ),
                ),
                label="副能力*(1+副能力%/100)",
            ),
            "result": BinaryNode(
                type="binary", op="+",
                lhs=BinaryNode(
                    type="binary", op="*",
                    lhs="main",
                    rhs=ConstNode(type="const", value=0.005),
                ),
                rhs=BinaryNode(
                    type="binary", op="*",
                    lhs="sub",
                    rhs=ConstNode(type="const", value=0.002),
                ),
                label="能力值加成 = main*0.005 + sub*0.002",
            ),
        },
        outputs=[
            DAGOutput(node="result", label="能力值加成"),
        ],
    )


def _make_final_attack_subgraph() -> DAGSubgraph:
    return DAGSubgraph(
        name="final_attack",
        inputs=[
            "char_base_atk", "weapon_base_atk",
            "atk_bonus", "additional_atk", "equip_flat_atk",
            "ability_bonus",
        ],
        nodes={
            "base_atk": BinaryNode(
                type="binary", op="+",
                lhs="char_base_atk", rhs="weapon_base_atk",
                label="基础攻击力 = 角色+武器",
            ),
            "atk_bonus_part": BinaryNode(
                type="binary", op="*",
                lhs=BinaryNode(
                    type="binary", op="+",
                    lhs=ConstNode(type="const", value=1.0),
                    rhs="atk_bonus",
                ),
                rhs="base_atk",
                label="攻击加成攻击力 = 基础*(1+攻击力+)",
            ),
            "mid_atk": BinaryNode(
                type="binary", op="+",
                lhs="atk_bonus_part",
                rhs=BinaryNode(
                    type="binary", op="+",
                    lhs="additional_atk",
                    rhs="equip_flat_atk",
                ),
                label="中间攻击力 = 攻击加成攻击力+附加+装备",
            ),
            "result": BinaryNode(
                type="binary", op="*",
                lhs="mid_atk",
                rhs=BinaryNode(
                    type="binary", op="+",
                    lhs=ConstNode(type="const", value=1.0),
                    rhs="ability_bonus",
                ),
                label="最终攻击力 = 中间*(1+能力值加成)",
            ),
        },
        outputs=[
            DAGOutput(node="result", label="最终攻击力"),
        ],
    )


def _make_single_hit_damage_subgraph() -> DAGSubgraph:
    return DAGSubgraph(
        name="single_hit_damage",
        inputs=["final_attack", "skill_mult"],
        nodes={
            "result": BinaryNode(
                type="binary", op="*",
                lhs="final_attack", rhs="skill_mult",
                label="单段伤害 = 最终攻击力 * 技能倍率",
            ),
        },
        outputs=[
            DAGOutput(node="result", label="单段伤害"),
        ],
    )


def _make_crit_zone_subgraph() -> DAGSubgraph:
    return DAGSubgraph(
        name="crit_zone",
        inputs=["crit_rate", "crit_damage"],
        nodes={
            "result": BinaryNode(
                type="binary", op="+",
                lhs=ConstNode(type="const", value=1.0),
                rhs=BinaryNode(
                    type="binary", op="*",
                    lhs="crit_rate",
                    rhs=BinaryNode(
                        type="binary", op="-",
                        lhs="crit_damage",
                        rhs=ConstNode(type="const", value=1.0),
                    ),
                ),
                label="暴击区 = 1 + 暴击率*(暴击伤害-1)",
            ),
        },
        outputs=[
            DAGOutput(node="result", label="暴击区"),
        ],
    )


def _make_base_damage_block_subgraph() -> DAGSubgraph:
    """基础伤害块 = 最终攻击力 * 技能倍率 * 暴击区。"""
    return DAGSubgraph(
        name="base_damage_block",
        inputs=["final_attack", "skill_mult", "crit_zone"],
        nodes={
            "single_hit": BinaryNode(
                type="binary", op="*",
                lhs="final_attack", rhs="skill_mult",
                label="单段基础伤害",
            ),
            "result": BinaryNode(
                type="binary", op="*",
                lhs="single_hit", rhs="crit_zone",
                label="暴击后伤害 = 单段基础 * 暴击区",
            ),
        },
        outputs=[
            DAGOutput(node="result", label="暴击后伤害"),
        ],
    )


def _make_buff_debuff_block_subgraph() -> DAGSubgraph:
    """增益减益块 = 伤害加成 * 伤害减免 * 增幅 * 虚弱 * 庇护 * 脆弱 * 易伤 连乘。"""
    return DAGSubgraph(
        name="buff_debuff_block",
        inputs=[
            "damage_after_crit",
            "zone_dmg_bonus", "zone_dmg_reduc",
            "zone_amp", "zone_weak", "zone_shelter",
            "zone_fragile", "zone_vuln",
        ],
        nodes={
            "mult": BinaryNode(
                type="binary", op="*",
                lhs="zone_dmg_bonus",
                rhs=BinaryNode(
                    type="binary", op="*",
                    lhs="zone_dmg_reduc",
                    rhs=BinaryNode(
                        type="binary", op="*",
                        lhs="zone_amp",
                        rhs=BinaryNode(
                            type="binary", op="*",
                            lhs="zone_weak",
                            rhs=BinaryNode(
                                type="binary", op="*",
                                lhs="zone_shelter",
                                rhs=BinaryNode(
                                    type="binary", op="*",
                                    lhs="zone_fragile",
                                    rhs="zone_vuln",
                                ),
                            ),
                        ),
                    ),
                ),
                label="7 乘区连乘",
            ),
            "result": BinaryNode(
                type="binary", op="*",
                lhs="damage_after_crit",
                rhs="mult",
                label="增益减益后伤害",
            ),
        },
        outputs=[
            DAGOutput(node="result", label="增益减益后伤害"),
        ],
    )


def _make_environment_block_subgraph() -> DAGSubgraph:
    """环境乘区块 = 防御减伤 * 失衡易伤 * 抗性 * 非主控减伤 * 连击增伤 * 特殊乘区。"""
    return DAGSubgraph(
        name="environment_block",
        inputs=[
            "damage_after_buff",
            "enemy_defense",
            "zone_imbal", "zone_res", "zone_ncr",
            "zone_combo", "zone_special",
        ],
        nodes={
            "defense_reduction": BinaryNode(
                type="binary", op="/",
                lhs=ConstNode(type="const", value=100.0),
                rhs=BinaryNode(
                    type="binary", op="+",
                    lhs=ConstNode(type="const", value=100.0),
                    rhs="enemy_defense",
                ),
                label="防御减伤 = 100/(100+防)",
            ),
            "env_mult": BinaryNode(
                type="binary", op="*",
                lhs="defense_reduction",
                rhs=BinaryNode(
                    type="binary", op="*",
                    lhs="zone_imbal",
                    rhs=BinaryNode(
                        type="binary", op="*",
                        lhs="zone_res",
                        rhs=BinaryNode(
                            type="binary", op="*",
                            lhs="zone_ncr",
                            rhs=BinaryNode(
                                type="binary", op="*",
                                lhs="zone_combo",
                                rhs="zone_special",
                            ),
                        ),
                    ),
                ),
                label="环境 6 乘区连乘",
            ),
            "result": BinaryNode(
                type="binary", op="*",
                lhs="damage_after_buff",
                rhs="env_mult",
                label="最终伤害",
            ),
        },
        outputs=[
            DAGOutput(node="result", label="最终伤害"),
            DAGOutput(node="defense_reduction", label="防御区"),
        ],
    )
