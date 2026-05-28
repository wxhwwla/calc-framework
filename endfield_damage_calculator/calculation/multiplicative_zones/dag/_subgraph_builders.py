#!/usr/bin/env python3
"""DAG 子图构建器：终末地伤害公式各乘区的子图定义。"""

from __future__ import annotations

from calc_framework.dag.schema import (
    BinaryNode,
    ConstNode,
    DAGGraph,
    DAGOutput,
    DAGSubgraph,
    DAGVariable,
    ExprNode,
)


def make_ability_bonus_subgraph() -> DAGSubgraph:
    return DAGSubgraph(
        description="能力值加成 = 主能力最终值x0.005 + 副能力最终值x0.002",
        parameters={
            "main_flat": DAGVariable(type="float", source="computed", description="主能力平值"),
            "sub_flat": DAGVariable(type="float", source="computed", description="副能力平值"),
            "main_pct": DAGVariable(type="float", source="computed", description="主能力百分比加成"),
            "sub_pct": DAGVariable(type="float", source="computed", description="副能力百分比加成"),
        },
        nodes={
            "main_final": ExprNode(type="expr", expr="main_flat * (1 + main_pct / 100)",
                                    inputs={"main_flat": "main_flat", "main_pct": "main_pct"},
                                    label="主能力最终值"),
            "sub_final": ExprNode(type="expr", expr="sub_flat * (1 + sub_pct / 100)",
                                   inputs={"sub_flat": "sub_flat", "sub_pct": "sub_pct"},
                                   label="副能力最终值"),
            "main_contrib": ExprNode(type="expr", expr="main_final * 0.005",
                                      inputs={"main_final": "main_final"}, label="主能力贡献"),
            "sub_contrib": ExprNode(type="expr", expr="sub_final * 0.002",
                                     inputs={"sub_final": "sub_final"}, label="副能力贡献"),
            "ability_bonus": BinaryNode(type="binary", op="+", lhs="main_contrib", rhs="sub_contrib",
                                         label="能力值加成"),
        },
        outputs={"ability_bonus": DAGOutput(node="ability_bonus", label="能力值加成")},
    )


def make_final_attack_subgraph() -> DAGSubgraph:
    return DAGSubgraph(
        description="最终攻击力 = (角色基础+武器基础)x(1+攻击力%)+附加攻击+装备平值x(1+能力值加成)",
        parameters={
            "char_base_atk": DAGVariable(type="float", source="character", description="角色基础攻击力"),
            "weapon_base_atk": DAGVariable(type="float", source="weapon", description="武器基础攻击力"),
            "atk_bonus": DAGVariable(type="float", source="weapon", description="攻击力+ 加成%"),
            "additional_atk": DAGVariable(type="float", source="weapon", description="附加攻击力+ 平值"),
            "equip_flat_atk": DAGVariable(type="float", source="equipment", description="装备平铺攻击力"),
            "ability_bonus": DAGVariable(type="float", source="computed", description="能力值加成"),
        },
        nodes={
            "const_one": ConstNode(type="const", value=1.0),
            "base_atk": BinaryNode(type="binary", op="+", lhs="char_base_atk", rhs="weapon_base_atk",
                                    label="基础攻击力合计"),
            "atk_mult": BinaryNode(type="binary", op="+", lhs="atk_bonus", rhs="const_one",
                                    label="攻击力+ 乘数"),
            "atk_bonus_atk": BinaryNode(type="binary", op="*", lhs="base_atk", rhs="atk_mult",
                                          label="攻击加成攻击力"),
            "mid_atk": ExprNode(type="expr", expr="atk_bonus_atk + additional_atk + equip_flat_atk",
                                 inputs={"atk_bonus_atk": "atk_bonus_atk",
                                         "additional_atk": "additional_atk",
                                         "equip_flat_atk": "equip_flat_atk"},
                                 label="中间攻击力"),
            "ability_mult": BinaryNode(type="binary", op="+", lhs="const_one", rhs="ability_bonus",
                                        label="能力值乘数"),
            "final_atk": BinaryNode(type="binary", op="*", lhs="mid_atk", rhs="ability_mult",
                                     label="最终攻击力"),
        },
        outputs={"final_attack": DAGOutput(node="final_atk", label="最终攻击力", is_primary=True)},
    )


def make_single_hit_damage_subgraph() -> DAGSubgraph:
    zones = [
        "final_attack", "skill_multiplier", "crit_zone", "damage_bonus_zone",
        "damage_reduction", "amplification", "weakness", "shelter", "fragile",
        "vulnerability", "defense_zone", "imbalance_zone", "resistance_zone",
        "non_control_reduction", "combo_bonus", "special_zone",
    ]
    params = {p: DAGVariable(type="float", source="computed", description=p) for p in zones}
    nodes = {}
    nodes["zone_0"] = BinaryNode(type="binary", op="*", lhs="final_attack", rhs="skill_multiplier",
                                  label="基础伤害区")
    for i in range(2, len(zones)):
        prev = f"zone_{i-2}" if i > 2 else "zone_0"
        nodes[f"zone_{i-1}"] = BinaryNode(type="binary", op="*", lhs=prev, rhs=zones[i],
                                           label=f"x{zones[i]}")
    return DAGSubgraph(
        description="15 乘区连乘 -> 单段最终伤害",
        parameters=params, nodes=nodes,
        outputs={"final_damage": DAGOutput(node=f"zone_{len(zones)-2}", label="最终伤害", is_primary=True)},
    )


def make_defense_reduction_subgraph() -> DAGSubgraph:
    return DAGSubgraph(
        description="防御减伤 = 100 / (敌防 + 100)",
        parameters={"enemy_defense": DAGVariable(type="float", source="enemy", description="敌方防御值")},
        nodes={
            "c100": ConstNode(type="const", value=100.0),
            "def_plus_100": BinaryNode(type="binary", op="+", lhs="enemy_defense", rhs="c100",
                                        label="敌防+100"),
            "def_reduction": BinaryNode(type="binary", op="/", lhs="c100", rhs="def_plus_100",
                                         label="防御减伤"),
        },
        outputs={"defense_reduction": DAGOutput(node="def_reduction", label="防御减伤", is_primary=True)},
    )


def make_crit_zone_subgraph() -> DAGSubgraph:
    return DAGSubgraph(
        description="暴击区 = 1 + 暴击率 x (暴击伤害 - 1)",
        parameters={
            "crit_rate": DAGVariable(type="float", source="character", description="暴击率（小数）"),
            "crit_damage": DAGVariable(type="float", source="character", description="暴击伤害（小数）"),
        },
        nodes={
            "const_one": ConstNode(type="const", value=1.0),
            "crit_dmg_minus_1": BinaryNode(type="binary", op="-", lhs="crit_damage", rhs="const_one",
                                            label="暴击伤害 - 1"),
            "rate_times_dmg": BinaryNode(type="binary", op="*", lhs="crit_rate", rhs="crit_dmg_minus_1",
                                          label="暴击率 x (暴击伤害-1)"),
            "crit_zone": BinaryNode(type="binary", op="+", lhs="const_one", rhs="rate_times_dmg",
                                     label="暴击区"),
        },
        outputs={"crit_zone": DAGOutput(node="crit_zone", label="暴击区", is_primary=True)},
    )
