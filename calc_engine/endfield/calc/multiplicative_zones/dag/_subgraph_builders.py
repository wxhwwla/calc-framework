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
    DAGVariable,
    ExprNode,
)


def _make_ability_bonus_subgraph() -> DAGSubgraph:
    return DAGSubgraph(
        description="能力值加成 = 主能力最终值×0.005 + 副能力最终值×0.002",
        parameters={
            "main_flat": DAGVariable(
                type="float", source="computed",
                description="主能力平值（基础 + 武器平值加成 + 信赖）",
            ),
            "sub_flat": DAGVariable(
                type="float", source="computed",
                description="副能力平值（基础 + 武器平值加成）",
            ),
            "main_pct": DAGVariable(
                type="float", source="computed",
                description="主能力百分比加成（主能力+% + 全能力+%）",
            ),
            "sub_pct": DAGVariable(
                type="float", source="computed",
                description="副能力百分比加成（副能力+% + 全能力+%）",
            ),
        },
        nodes={
            "main_final": ExprNode(
                type="expr",
                expr="main_flat * (1 + main_pct / 100)",
                inputs={"main_flat": "main_flat", "main_pct": "main_pct"},
                label="主能力最终值",
                description="平值 × (1 + 百分比/100)",
            ),
            "sub_final": ExprNode(
                type="expr",
                expr="sub_flat * (1 + sub_pct / 100)",
                inputs={"sub_flat": "sub_flat", "sub_pct": "sub_pct"},
                label="副能力最终值",
                description="平值 × (1 + 百分比/100)",
            ),
            "main_contrib": ExprNode(
                type="expr",
                expr="main_final * 0.005",
                inputs={"main_final": "main_final"},
                label="主能力贡献",
            ),
            "sub_contrib": ExprNode(
                type="expr",
                expr="sub_final * 0.002",
                inputs={"sub_final": "sub_final"},
                label="副能力贡献",
            ),
            "ability_bonus": BinaryNode(
                type="binary",
                op="+",
                lhs="main_contrib",
                rhs="sub_contrib",
                label="能力值加成",
            ),
        },
        outputs={
            "ability_bonus": DAGOutput(node="ability_bonus", label="能力值加成"),
        },
    )


def _make_final_attack_subgraph() -> DAGSubgraph:
    return DAGSubgraph(
        description="最终攻击力 = (角色基础+武器基础)×(1+攻击力+) + 附加攻击 + 装备平值 × (1+能力值加成)",
        parameters={
            "char_base_atk": DAGVariable(type="float", source="character", description="角色基础攻击力"),
            "weapon_base_atk": DAGVariable(type="float", source="weapon", description="武器基础攻击力"),
            "atk_bonus": DAGVariable(
                type="float", source="weapon",
                description="攻击力+ 加成值（已换算为小数，如 0.15 表示 15%）",
            ),
            "additional_atk": DAGVariable(type="float", source="weapon", description="附加攻击力+ 平值"),
            "equip_flat_atk": DAGVariable(type="float", source="equipment", description="装备平铺攻击力"),
            "ability_bonus": DAGVariable(type="float", source="computed", description="能力值加成"),
        },
        nodes={
            "const_one": ConstNode(type="const", value=1.0),
            "base_atk": BinaryNode(
                type="binary",
                op="+",
                lhs="char_base_atk",
                rhs="weapon_base_atk",
                label="基础攻击力合计",
            ),
            "atk_mult": BinaryNode(
                type="binary",
                op="+",
                lhs="atk_bonus",
                rhs="const_one",
                label="攻击力+ 乘数",
            ),
            "atk_bonus_atk": BinaryNode(
                type="binary",
                op="*",
                lhs="base_atk",
                rhs="atk_mult",
                label="攻击加成攻击力",
            ),
            "mid_atk": ExprNode(
                type="expr",
                expr="atk_bonus_atk + additional_atk + equip_flat_atk",
                inputs={
                    "atk_bonus_atk": "atk_bonus_atk",
                    "additional_atk": "additional_atk",
                    "equip_flat_atk": "equip_flat_atk",
                },
                label="中间攻击力",
            ),
            "ability_mult": BinaryNode(
                type="binary",
                op="+",
                lhs="const_one",
                rhs="ability_bonus",
                label="能力值乘数",
            ),
            "final_atk": BinaryNode(
                type="binary",
                op="*",
                lhs="mid_atk",
                rhs="ability_mult",
                label="最终攻击力",
            ),
        },
        outputs={
            "final_attack": DAGOutput(node="final_atk", label="最终攻击力", is_primary=True),
        },
    )


def _make_single_hit_damage_subgraph() -> DAGSubgraph:
    params = {}
    nodes = {}

    zones = [
        "final_attack",
        "skill_multiplier",
        "crit_zone",
        "damage_bonus_zone",
        "damage_reduction",
        "amplification",
        "weakness",
        "shelter",
        "fragile",
        "vulnerability",
        "defense_zone",
        "imbalance_zone",
        "resistance_zone",
        "non_control_reduction",
        "combo_bonus",
        "special_zone",
    ]

    for param_name in zones:
        params[param_name] = DAGVariable(
            type="float",
            source="computed",
            description=param_name,
        )

    nodes["zone_0"] = BinaryNode(
        type="binary", op="*",
        lhs="final_attack", rhs="skill_multiplier",
        label="基础伤害区",
    )

    for i in range(2, len(zones)):
        prev_id = f"zone_{i-2}" if i > 2 else "zone_0"
        param_name = zones[i]
        node_id = f"zone_{i-1}"
        nodes[node_id] = BinaryNode(
            type="binary", op="*",
            lhs=prev_id, rhs=param_name,
            label=f"×{param_name}",
        )

    return DAGSubgraph(
        description="15 乘区连乘 → 单段最终伤害。基础伤害区 = final_attack × skill_multiplier",
        parameters=params,
        nodes=nodes,
        outputs={
            "final_damage": DAGOutput(
                node=f"zone_{len(zones) - 2}",
                label="最终伤害",
                is_primary=True,
            ),
        },
    )


def _make_defense_reduction_subgraph() -> DAGSubgraph:
    return DAGSubgraph(
        description="防御减伤 = 100 / (敌防 + 100)",
        parameters={
            "enemy_defense": DAGVariable(
                type="float", source="enemy",
                description="敌方防御值",
            ),
        },
        nodes={
            "c100": ConstNode(type="const", value=100.0),
            "def_plus_100": BinaryNode(
                type="binary", op="+", lhs="enemy_defense", rhs="c100",
                label="敌防+100",
            ),
            "def_reduction": BinaryNode(
                type="binary", op="/", lhs="c100", rhs="def_plus_100",
                label="防御减伤",
            ),
        },
        outputs={
            "defense_reduction": DAGOutput(
                node="def_reduction", label="防御减伤", is_primary=True,
            ),
        },
    )


def _make_crit_zone_subgraph() -> DAGSubgraph:
    return DAGSubgraph(
        description="暴击区 = 1 + 暴击率 × (暴击伤害 - 1)",
        parameters={
            "crit_rate": DAGVariable(
                type="float", source="character",
                description="暴击率（小数，如 0.05 = 5%）",
            ),
            "crit_damage": DAGVariable(
                type="float", source="character",
                description="暴击伤害（小数，如 0.5 = 50%）",
            ),
        },
        nodes={
            "const_one": ConstNode(type="const", value=1.0),
            "crit_dmg_minus_1": BinaryNode(
                type="binary", op="-", lhs="crit_damage", rhs="const_one",
                label="暴击伤害 - 1",
            ),
            "rate_times_dmg": BinaryNode(
                type="binary", op="*", lhs="crit_rate", rhs="crit_dmg_minus_1",
                label="暴击率 × (暴击伤害 - 1)",
            ),
            "crit_zone": BinaryNode(
                type="binary", op="+", lhs="const_one", rhs="rate_times_dmg",
                label="暴击区",
            ),
        },
        outputs={
            "crit_zone": DAGOutput(node="crit_zone", label="暴击区", is_primary=True),
        },
    )


def _make_base_damage_block_subgraph() -> DAGSubgraph:
    return DAGSubgraph(
        description="基础伤害块 = 最终攻击力 × 技能倍率 × 暴击区",
        parameters={
            "final_attack": DAGVariable(
                type="float", source="computed", description="最终攻击力",
            ),
            "skill_mult": DAGVariable(
                type="float", source="computed", description="技能倍率",
            ),
            "crit_zone": DAGVariable(
                type="float", source="computed", description="暴击区乘数",
            ),
        },
        nodes={
            "zone_base": BinaryNode(
                type="binary", op="*",
                lhs="final_attack", rhs="skill_mult",
                label="基础伤害区",
            ),
            "damage_after_crit": BinaryNode(
                type="binary", op="*",
                lhs="zone_base", rhs="crit_zone",
                label="×暴击区",
            ),
        },
        outputs={
            "damage_after_crit": DAGOutput(
                node="damage_after_crit", label="暴击后伤害", is_primary=True,
            ),
        },
    )


def _make_buff_debuff_block_subgraph() -> DAGSubgraph:
    return DAGSubgraph(
        description="增益/减益块：7 个乘区连乘（伤害加成/减免/增幅/虚弱/庇护/脆弱/易伤）",
        parameters={
            "damage_after_crit": DAGVariable(
                type="float", source="computed", description="暴击后伤害",
            ),
            "zone_dmg_bonus": DAGVariable(
                type="float", source="computed", description="伤害加成区",
            ),
            "zone_dmg_reduc": DAGVariable(
                type="float", source="computed", description="伤害减免区",
            ),
            "zone_amp": DAGVariable(
                type="float", source="computed", description="增幅区",
            ),
            "zone_weak": DAGVariable(
                type="float", source="computed", description="虚弱区",
            ),
            "zone_shelter": DAGVariable(
                type="float", source="computed", description="庇护区",
            ),
            "zone_fragile": DAGVariable(
                type="float", source="computed", description="脆弱区",
            ),
            "zone_vuln": DAGVariable(
                type="float", source="computed", description="易伤区",
            ),
        },
        nodes={
            "z0": BinaryNode(
                type="binary", op="*",
                lhs="damage_after_crit", rhs="zone_dmg_bonus",
                label="×伤害加成区",
            ),
            "z1": BinaryNode(
                type="binary", op="*",
                lhs="z0", rhs="zone_dmg_reduc",
                label="×伤害减免区",
            ),
            "z2": BinaryNode(
                type="binary", op="*",
                lhs="z1", rhs="zone_amp",
                label="×增幅区",
            ),
            "z3": BinaryNode(
                type="binary", op="*",
                lhs="z2", rhs="zone_weak",
                label="×虚弱区",
            ),
            "z4": BinaryNode(
                type="binary", op="*",
                lhs="z3", rhs="zone_shelter",
                label="×庇护区",
            ),
            "z5": BinaryNode(
                type="binary", op="*",
                lhs="z4", rhs="zone_fragile",
                label="×脆弱区",
            ),
            "z6": BinaryNode(
                type="binary", op="*",
                lhs="z5", rhs="zone_vuln",
                label="×易伤区",
            ),
        },
        outputs={
            "damage_after_buff": DAGOutput(
                node="z6", label="增益减益后伤害", is_primary=True,
            ),
        },
    )


def _make_environment_block_subgraph() -> DAGSubgraph:
    return DAGSubgraph(
        description="环境乘区块：防御减伤 + 失衡/抗性/非主控减伤/连击增伤/特殊乘区连乘",
        parameters={
            "damage_after_buff": DAGVariable(
                type="float", source="computed", description="增益减益后伤害",
            ),
            "enemy_defense": DAGVariable(
                type="float", source="enemy", description="敌方防御值",
            ),
            "zone_imbal": DAGVariable(
                type="float", source="computed", description="失衡易伤区",
            ),
            "zone_res": DAGVariable(
                type="float", source="computed", description="抗性区",
            ),
            "zone_ncr": DAGVariable(
                type="float", source="computed", description="非主控减伤区",
            ),
            "zone_combo": DAGVariable(
                type="float", source="computed", description="连击增伤区",
            ),
            "zone_special": DAGVariable(
                type="float", source="computed", description="特殊乘区",
            ),
        },
        nodes={
            "c100": ConstNode(type="const", value=100.0),
            "def_plus_100": BinaryNode(
                type="binary", op="+",
                lhs="enemy_defense", rhs="c100",
                label="敌防+100",
            ),
            "def_mult": BinaryNode(
                type="binary", op="/",
                lhs="c100", rhs="def_plus_100",
                label="防御减伤",
            ),
            "z0": BinaryNode(
                type="binary", op="*",
                lhs="damage_after_buff", rhs="def_mult",
                label="×防御区",
            ),
            "z1": BinaryNode(
                type="binary", op="*",
                lhs="z0", rhs="zone_imbal",
                label="×失衡易伤区",
            ),
            "z2": BinaryNode(
                type="binary", op="*",
                lhs="z1", rhs="zone_res",
                label="×抗性区",
            ),
            "z3": BinaryNode(
                type="binary", op="*",
                lhs="z2", rhs="zone_ncr",
                label="×非主控减伤区",
            ),
            "z4": BinaryNode(
                type="binary", op="*",
                lhs="z3", rhs="zone_combo",
                label="×连击增伤区",
            ),
            "z5": BinaryNode(
                type="binary", op="*",
                lhs="z4", rhs="zone_special",
                label="×特殊乘区=最终伤害",
            ),
        },
        outputs={
            "final_damage": DAGOutput(
                node="z5", label="最终伤害", is_primary=True,
            ),
            "defense_reduction": DAGOutput(
                node="def_mult", label="防御减伤",
            ),
        },
    )


