#!/usr/bin/env python3
"""终末地完整伤害公式 DAG JSON 配置文件生成脚本。

输出文件位于 ``framework/src/calc_framework/configs/endfield_full.dag.json``。

子图：
- ``ability_bonus``：能力值加成 = main_flat×(1+main_pct/100)×0.005 + sub_flat×(1+sub_pct/100)×0.002
- ``final_attack``：最终攻击力 = (char_atk+weapon_atk)×(1+atk_bonus)+add_atk+equip_atk×(1+ability_bonus)
- ``single_hit_damage``：15 乘区连乘 → 最终伤害

主图：扁平化调用三个子图的计算逻辑，直接使用已预处理的参数名。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_FRAMEWORK_DIR = Path(__file__).resolve().parents[4] / "framework"
_SRC_DIR = _FRAMEWORK_DIR / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from calc_framework.dag.schema import (
    BinaryNode,
    ConstNode,
    DAGGraph,
    DAGOutput,
    DAGSubgraph,
    DAGVariable,
    ExprNode,
    VarNode,
)
from calc_framework.dag.serializer import dag_to_dict

OUTPUT_PATH = _SRC_DIR / "calc_framework" / "configs" / "endfield_full.dag.json"


def _make_ability_bonus_subgraph() -> DAGSubgraph:
    return DAGSubgraph(
        description="能力值加成 = 主能力最终值×0.005 + 副能力最终值×0.002",
        parameters={
            "main_flat": DAGVariable(type="float", source="computed", description="主能力平值（基础 + 武器平值加成 + 信赖）"),
            "sub_flat": DAGVariable(type="float", source="computed", description="副能力平值（基础 + 武器平值加成）"),
            "main_pct": DAGVariable(type="float", source="computed", description="主能力百分比加成（主能力+% + 全能力+%）"),
            "sub_pct": DAGVariable(type="float", source="computed", description="副能力百分比加成（副能力+% + 全能力+%）"),
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
            "atk_bonus": DAGVariable(type="float", source="weapon", description="攻击力+ 加成值（已换算为小数，如 0.15 表示 15%）"),
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


def _make_master_graph() -> DAGGraph:
    return DAGGraph(
        schema_version="dag-v1",
        name="终末地伤害公式（完整版）",
        description="终末地 15 乘区完整伤害公式 DAG。子图含 ability_bonus / final_attack / single_hit_damage 用于独立校验；主图扁平求值。",
        variables={
            "角色.基础攻击": DAGVariable(type="float", source="character", description="角色基础攻击力"),
            "武器.基础攻击": DAGVariable(type="float", source="weapon", description="武器基础攻击力"),
            "武器.攻击力+": DAGVariable(type="float", source="weapon", description="攻击力+ 小数加成（0.15 = 15%）"),
            "武器.附加攻击力+": DAGVariable(type="float", source="weapon", description="附加攻击力+ 平值"),
            "装备.攻击力平值": DAGVariable(type="float", source="equipment", description="装备平铺攻击力", default=0.0),
            "computed.主能力平值加算": DAGVariable(type="float", source="computed", description="主能力平值全部来源"),
            "computed.副能力平值加算": DAGVariable(type="float", source="computed", description="副能力平值全部来源"),
            "computed.主能力百分比": DAGVariable(type="float", source="computed", description="主能力百分比加成"),
            "computed.副能力百分比": DAGVariable(type="float", source="computed", description="副能力百分比加成"),
            "computed.最终攻击力": DAGVariable(type="float", source="computed", description="最终攻击力（可由本 DAG 计算或外部传入）"),
            "computed.技能倍率": DAGVariable(type="float", source="computed", description="技能倍率"),
            "computed.暴击区": DAGVariable(type="float", source="computed", description="暴击区倍数"),
            "computed.伤害加成": DAGVariable(type="float", source="computed", description="伤害加成区 = 1+类型+技能+失衡+其他"),
            "computed.伤害减免": DAGVariable(type="float", source="computed", description="伤害减免区 = ∏(1-减免值)"),
            "computed.增幅": DAGVariable(type="float", source="computed", description="增幅区 = 1+Σ增幅值"),
            "computed.虚弱": DAGVariable(type="float", source="computed", description="虚弱区 = ∏(1-虚弱值)"),
            "computed.庇护": DAGVariable(type="float", source="computed", description="庇护区 = 1-max(庇护值)"),
            "computed.脆弱": DAGVariable(type="float", source="computed", description="脆弱区 = 1+Σ脆弱值"),
            "computed.易伤": DAGVariable(type="float", source="computed", description="易伤区 = 1+Σ易伤值"),
            "computed.防御": DAGVariable(type="float", source="computed", description="防御区 = 100/(100+敌防)"),
            "computed.失衡易伤": DAGVariable(type="float", source="computed", description="失衡易伤系数"),
            "computed.抗性": DAGVariable(type="float", source="computed", description="抗性区 = 1-抗性/100+无视/100"),
            "computed.非主控减伤": DAGVariable(type="float", source="computed", description="非主控减伤区 = ∏(1-值)"),
            "computed.连击增伤": DAGVariable(type="float", source="computed", description="连击增伤区 = 1+Σ值"),
            "computed.特殊乘区": DAGVariable(type="float", source="computed", description="特殊乘区 = ∏值"),
        },
        subgraphs={
            "ability_bonus": _make_ability_bonus_subgraph(),
            "final_attack": _make_final_attack_subgraph(),
            "single_hit_damage": _make_single_hit_damage_subgraph(),
        },
        nodes={
            "char_atk": VarNode(type="var", path="角色.基础攻击", label="角色攻击"),
            "weapon_atk": VarNode(type="var", path="武器.基础攻击", label="武器攻击"),
            "atk_bonus": VarNode(type="var", path="武器.攻击力+", label="攻击力+"),
            "add_atk": VarNode(type="var", path="武器.附加攻击力+", label="附加攻击"),
            "equip_atk": VarNode(type="var", path="装备.攻击力平值", label="装备攻击"),
            "main_flat": VarNode(type="var", path="computed.主能力平值加算", label="主能力平值"),
            "sub_flat": VarNode(type="var", path="computed.副能力平值加算", label="副能力平值"),
            "main_pct": VarNode(type="var", path="computed.主能力百分比", label="主能力%"),
            "sub_pct": VarNode(type="var", path="computed.副能力百分比", label="副能力%"),
            "const_one": ConstNode(type="const", value=1.0),
            "c0005": ConstNode(type="const", value=0.005),
            "c0002": ConstNode(type="const", value=0.002),
            "c100": ConstNode(type="const", value=100.0),

            "ability_final_main": ExprNode(
                type="expr", expr="main_flat * (1 + main_pct / 100)",
                inputs={"main_flat": "main_flat", "main_pct": "main_pct"},
                label="主能力最终值",
            ),
            "ability_final_sub": ExprNode(
                type="expr", expr="sub_flat * (1 + sub_pct / 100)",
                inputs={"sub_flat": "sub_flat", "sub_pct": "sub_pct"},
                label="副能力最终值",
            ),
            "ability_main_contrib": BinaryNode(type="binary", op="*", lhs="ability_final_main", rhs="c0005", label="主能力贡献"),
            "ability_sub_contrib": BinaryNode(type="binary", op="*", lhs="ability_final_sub", rhs="c0002", label="副能力贡献"),
            "ability_bonus": BinaryNode(type="binary", op="+", lhs="ability_main_contrib", rhs="ability_sub_contrib", label="能力值加成"),

            "base_atk": BinaryNode(type="binary", op="+", lhs="char_atk", rhs="weapon_atk", label="基础攻击合计"),
            "atk_mult": BinaryNode(type="binary", op="+", lhs="atk_bonus", rhs="const_one", label="攻击力+乘数"),
            "atk_bonus_atk": BinaryNode(type="binary", op="*", lhs="base_atk", rhs="atk_mult", label="攻击加成攻击力"),
            "mid_atk": ExprNode(
                type="expr", expr="atk_bonus_atk + add_atk + equip_atk",
                inputs={"atk_bonus_atk": "atk_bonus_atk", "add_atk": "add_atk", "equip_atk": "equip_atk"},
                label="中间攻击力",
            ),
            "ability_mult": BinaryNode(type="binary", op="+", lhs="const_one", rhs="ability_bonus", label="能力值乘数"),
            "final_attack_calc": BinaryNode(type="binary", op="*", lhs="mid_atk", rhs="ability_mult", label="最终攻击力"),
            "final_atk_var": VarNode(type="var", path="computed.最终攻击力", label="最终攻击力(外部)"),

            "skill_mult": VarNode(type="var", path="computed.技能倍率", label="技能倍率"),
            "zone_base": BinaryNode(type="binary", op="*", lhs="final_atk_var", rhs="skill_mult", label="基础伤害区"),
            "zone_crit": VarNode(type="var", path="computed.暴击区", label="暴击区"),
            "z1": BinaryNode(type="binary", op="*", lhs="zone_base", rhs="zone_crit", label="×暴击区"),
            "zone_dmg_bonus": VarNode(type="var", path="computed.伤害加成", label="伤害加成区"),
            "z2": BinaryNode(type="binary", op="*", lhs="z1", rhs="zone_dmg_bonus", label="×伤害加成区"),
            "zone_dmg_reduc": VarNode(type="var", path="computed.伤害减免", label="伤害减免区"),
            "z3": BinaryNode(type="binary", op="*", lhs="z2", rhs="zone_dmg_reduc", label="×伤害减免区"),
            "zone_amp": VarNode(type="var", path="computed.增幅", label="增幅区"),
            "z4": BinaryNode(type="binary", op="*", lhs="z3", rhs="zone_amp", label="×增幅区"),
            "zone_weak": VarNode(type="var", path="computed.虚弱", label="虚弱区"),
            "z5": BinaryNode(type="binary", op="*", lhs="z4", rhs="zone_weak", label="×虚弱区"),
            "zone_shelter": VarNode(type="var", path="computed.庇护", label="庇护区"),
            "z6": BinaryNode(type="binary", op="*", lhs="z5", rhs="zone_shelter", label="×庇护区"),
            "zone_fragile": VarNode(type="var", path="computed.脆弱", label="脆弱区"),
            "z7": BinaryNode(type="binary", op="*", lhs="z6", rhs="zone_fragile", label="×脆弱区"),
            "zone_vuln": VarNode(type="var", path="computed.易伤", label="易伤区"),
            "z8": BinaryNode(type="binary", op="*", lhs="z7", rhs="zone_vuln", label="×易伤区"),
            "zone_def": VarNode(type="var", path="computed.防御", label="防御区"),
            "z9": BinaryNode(type="binary", op="*", lhs="z8", rhs="zone_def", label="×防御区"),
            "zone_imbal": VarNode(type="var", path="computed.失衡易伤", label="失衡易伤区"),
            "z10": BinaryNode(type="binary", op="*", lhs="z9", rhs="zone_imbal", label="×失衡易伤区"),
            "zone_res": VarNode(type="var", path="computed.抗性", label="抗性区"),
            "z11": BinaryNode(type="binary", op="*", lhs="z10", rhs="zone_res", label="×抗性区"),
            "zone_ncr": VarNode(type="var", path="computed.非主控减伤", label="非主控减伤区"),
            "z12": BinaryNode(type="binary", op="*", lhs="z11", rhs="zone_ncr", label="×非主控减伤区"),
            "zone_combo": VarNode(type="var", path="computed.连击增伤", label="连击增伤区"),
            "z13": BinaryNode(type="binary", op="*", lhs="z12", rhs="zone_combo", label="×连击增伤区"),
            "zone_special": VarNode(type="var", path="computed.特殊乘区", label="特殊乘区"),
            "final_damage": BinaryNode(type="binary", op="*", lhs="z13", rhs="zone_special", label="×特殊乘区=最终伤害"),
        },
        outputs={
            "能力值加成": DAGOutput(node="ability_bonus", label="能力值加成"),
            "最终攻击力": DAGOutput(node="final_attack_calc", label="最终攻击力", is_primary=True),
            "最终伤害": DAGOutput(node="final_damage", label="最终伤害", is_primary=True),
        },
    )


def generate() -> DAGGraph:
    """生成完整终末地 DAG 公式图。"""
    return _make_master_graph()


def save_dag(graph: DAGGraph, path: Path | None = None) -> Path:
    """序列化 DAG 到 JSON 文件。"""
    target = path or OUTPUT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    d = dag_to_dict(graph)
    with target.open("w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    return target


def main() -> None:
    """CLI 入口：生成并保存 DAG JSON。"""
    g = generate()
    out = save_dag(g)
    print(f"已生成: {out}")
    print(f"  子图: {list(g.subgraphs.keys())}")
    print(f"  节点: {len(g.nodes)} 个")
    print(f"  输出: {list(g.outputs.keys())}")


if __name__ == "__main__":
    main()
