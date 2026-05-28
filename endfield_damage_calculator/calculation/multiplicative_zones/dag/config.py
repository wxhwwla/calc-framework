#!/usr/bin/env python3
"""终末地完整伤害公式 DAG JSON 配置文件生成脚本。

输出文件位于 ``framework/src/calc_framework/configs/endfield_full.dag.json``。

子图：
- ``ability_bonus``：能力值加成 = main_flat×(1+main_pct/100)×0.005 + sub_flat×(1+sub_pct/100)×0.002
- ``final_attack``：最终攻击力 = (char_atk+weapon_atk)×(1+atk_bonus)+add_atk+equip_atk×(1+ability_bonus)
- ``single_hit_damage``：15 乘区连乘 → 最终伤害
- ``defense_reduction``：防御减伤 = 100 / (敌防 + 100)
- ``crit_zone``：暴击区 = 1 + 暴击率 × (暴击伤害 - 1)

主图：扁平化调用五个子图的计算逻辑，全部乘区值从 DAG 中间输出读取。
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
    CallNode,
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



from ._subgraph_builders import (
    _make_ability_bonus_subgraph,
    _make_crit_zone_subgraph,
    _make_defense_reduction_subgraph,
    _make_final_attack_subgraph,
    _make_single_hit_damage_subgraph,
)


def _make_master_graph() -> DAGGraph:
    return DAGGraph(
        schema_version="dag-v1",
        name="终末地伤害公式（完整版）",
        description=(
            "终末地 15 乘区完整伤害公式 DAG。"
            "子图含 ability_bonus / final_attack / single_hit_damage 用于独立校验；"
            "主图扁平求值。"
        ),
        variables={
            "character.基础攻击": DAGVariable(type="float", source="character", description="角色基础攻击力"),
            "weapon.基础攻击": DAGVariable(type="float", source="weapon", description="武器基础攻击力"),
            "weapon.攻击力+": DAGVariable(
                type="float", source="weapon", description="攻击力+ 小数加成（0.15 = 15%）",
            ),
            "weapon.附加攻击力+": DAGVariable(type="float", source="weapon", description="附加攻击力+ 平值"),
            "equipment.攻击力平值": DAGVariable(
                type="float", source="equipment", description="装备平铺攻击力", default=0.0,
            ),
            "computed.主能力平值加算": DAGVariable(
                type="float", source="computed", description="主能力平值全部来源",
            ),
            "computed.副能力平值加算": DAGVariable(type="float", source="computed", description="副能力平值全部来源"),
            "computed.主能力百分比": DAGVariable(type="float", source="computed", description="主能力百分比加成"),
            "computed.副能力百分比": DAGVariable(type="float", source="computed", description="副能力百分比加成"),
            "computed.最终攻击力": DAGVariable(
                type="float", source="computed",
                description="最终攻击力（可由本 DAG 计算或外部传入）",
            ),
            "computed.技能倍率": DAGVariable(type="float", source="computed", description="技能倍率"),
            "computed.暴击区": DAGVariable(type="float", source="computed", description="暴击区倍数"),
            "computed.伤害加成": DAGVariable(
                type="float", source="computed",
                description="伤害加成区 = 1+类型+技能+失衡+其他",
            ),
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
            "character.暴击率": DAGVariable(
                type="float", source="character",
                description="暴击率（小数，如 0.05 = 5%）", default=0.05,
            ),
            "character.暴击伤害": DAGVariable(
                type="float", source="character",
                description="暴击伤害（小数，如 0.5 = 50%）", default=0.5,
            ),
            "enemy.防御": DAGVariable(
                type="float", source="enemy",
                description="敌方防御值", default=100,
            ),
            "character.力量": DAGVariable(
                type="float", source="character",
                description="力量基础值", default=0.0,
            ),
            "character.敏捷": DAGVariable(
                type="float", source="character",
                description="敏捷基础值", default=0.0,
            ),
            "character.智识": DAGVariable(
                type="float", source="character",
                description="智识基础值", default=0.0,
            ),
            "character.意志": DAGVariable(
                type="float", source="character",
                description="意志基础值", default=0.0,
            ),
            "computed.力量加成值": DAGVariable(
                type="float", source="computed",
                description="力量加成值（武器技能）", default=0.0,
            ),
            "computed.敏捷加成值": DAGVariable(
                type="float", source="computed",
                description="敏捷加成值（武器技能）", default=0.0,
            ),
            "computed.智识加成值": DAGVariable(
                type="float", source="computed",
                description="智识加成值（武器技能）", default=0.0,
            ),
            "computed.意志加成值": DAGVariable(
                type="float", source="computed",
                description="意志加成值（武器技能）", default=0.0,
            ),
            "computed.基础攻击力合计": DAGVariable(
                type="float", source="computed",
                description="角色基础攻击+武器基础攻击", default=0.0,
            ),
            "computed.攻击加成攻击力": DAGVariable(
                type="float", source="computed",
                description="基础攻击力合计×(1+攻击力+%)", default=0.0,
            ),
            "computed.中间攻击力": DAGVariable(
                type="float", source="computed",
                description="攻击加成攻击力+附加攻击+装备平值", default=0.0,
            ),
        },
        subgraphs={
            "ability_bonus": _make_ability_bonus_subgraph(),
            "final_attack": _make_final_attack_subgraph(),
            "single_hit_damage": _make_single_hit_damage_subgraph(),
            "defense_reduction": _make_defense_reduction_subgraph(),
            "crit_zone": _make_crit_zone_subgraph(),
        },
        nodes={
            "char_atk": VarNode(type="var", path="character.基础攻击", label="角色攻击"),
            "weapon_atk": VarNode(type="var", path="weapon.基础攻击", label="武器攻击"),
            "atk_bonus": VarNode(type="var", path="weapon.攻击力+", label="攻击力+"),
            "add_atk": VarNode(type="var", path="weapon.附加攻击力+", label="附加攻击"),
            "equip_atk": VarNode(type="var", path="equipment.攻击力平值", label="装备攻击"),
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
            "ability_main_contrib": BinaryNode(
                type="binary", op="*", lhs="ability_final_main", rhs="c0005",
                label="主能力贡献",
            ),
            "ability_sub_contrib": BinaryNode(
                type="binary", op="*", lhs="ability_final_sub", rhs="c0002",
                label="副能力贡献",
            ),
            "ability_bonus": BinaryNode(
                type="binary", op="+", lhs="ability_main_contrib",
                rhs="ability_sub_contrib", label="能力值加成",
            ),

            "base_atk": BinaryNode(type="binary", op="+", lhs="char_atk", rhs="weapon_atk", label="基础攻击合计"),
            "atk_mult": BinaryNode(type="binary", op="+", lhs="atk_bonus", rhs="const_one", label="攻击力+乘数"),
            "atk_bonus_atk": BinaryNode(type="binary", op="*", lhs="base_atk", rhs="atk_mult", label="攻击加成攻击力"),
            "mid_atk": ExprNode(
                type="expr", expr="atk_bonus_atk + add_atk + equip_atk",
                inputs={"atk_bonus_atk": "atk_bonus_atk", "add_atk": "add_atk", "equip_atk": "equip_atk"},
                label="中间攻击力",
            ),
            "ability_mult": BinaryNode(type="binary", op="+", lhs="const_one", rhs="ability_bonus", label="能力值乘数"),
            "final_attack_calc": BinaryNode(
                type="binary", op="*", lhs="mid_atk", rhs="ability_mult",
                label="最终攻击力",
            ),
            "final_atk_var": VarNode(type="var", path="computed.最终攻击力", label="最终攻击力(外部)"),

            "char_attr_力量": VarNode(type="var", path="character.力量", label="力量基础"),
            "char_attr_敏捷": VarNode(type="var", path="character.敏捷", label="敏捷基础"),
            "char_attr_智识": VarNode(type="var", path="character.智识", label="智识基础"),
            "char_attr_意志": VarNode(type="var", path="character.意志", label="意志基础"),
            "comp_attr_力量_bonus": VarNode(type="var", path="computed.力量加成值", label="力量加成"),
            "comp_attr_敏捷_bonus": VarNode(type="var", path="computed.敏捷加成值", label="敏捷加成"),
            "comp_attr_智识_bonus": VarNode(type="var", path="computed.智识加成值", label="智识加成"),
            "comp_attr_意志_bonus": VarNode(type="var", path="computed.意志加成值", label="意志加成"),
            "attr_力量_total": BinaryNode(
                type="binary", op="+",
                lhs="char_attr_力量", rhs="comp_attr_力量_bonus",
                label="力量最终值",
            ),
            "attr_敏捷_total": BinaryNode(
                type="binary", op="+",
                lhs="char_attr_敏捷", rhs="comp_attr_敏捷_bonus",
                label="敏捷最终值",
            ),
            "attr_智识_total": BinaryNode(
                type="binary", op="+",
                lhs="char_attr_智识", rhs="comp_attr_智识_bonus",
                label="智识最终值",
            ),
            "attr_意志_total": BinaryNode(
                type="binary", op="+",
                lhs="char_attr_意志", rhs="comp_attr_意志_bonus",
                label="意志最终值",
            ),

            "skill_mult": VarNode(type="var", path="computed.技能倍率", label="技能倍率"),
            "zone_base": BinaryNode(type="binary", op="*", lhs="final_atk_var", rhs="skill_mult", label="基础伤害区"),
            "zone_crit": CallNode(
                type="call", subgraph="crit_zone",
                bindings={"crit_rate": "char_crit_rate", "crit_damage": "char_crit_dmg"},
                label="暴击区",
            ),
            "char_crit_rate": VarNode(type="var", path="character.暴击率", label="暴击率"),
            "char_crit_dmg": VarNode(type="var", path="character.暴击伤害", label="暴击伤害"),
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
            "zone_def": CallNode(
                type="call", subgraph="defense_reduction",
                bindings={"enemy_defense": "enemy_def"},
                label="防御区",
            ),
            "enemy_def": VarNode(type="var", path="enemy.防御", label="敌方防御"),
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
            "final_damage": BinaryNode(
                type="binary", op="*", lhs="z13", rhs="zone_special",
                label="×特殊乘区=最终伤害",
            ),
        },
        outputs={
            "能力值加成": DAGOutput(node="ability_bonus", label="能力值加成"),
            "最终攻击力": DAGOutput(node="final_attack_calc", label="最终攻击力", is_primary=True),
            "最终伤害": DAGOutput(node="final_damage", label="最终伤害", is_primary=True),
            "暴击区": DAGOutput(node="zone_crit", label="暴击区"),
            "伤害加成区": DAGOutput(node="zone_dmg_bonus", label="伤害加成区"),
            "伤害减免区": DAGOutput(node="zone_dmg_reduc", label="伤害减免区"),
            "增幅区": DAGOutput(node="zone_amp", label="增幅区"),
            "虚弱区": DAGOutput(node="zone_weak", label="虚弱区"),
            "庇护区": DAGOutput(node="zone_shelter", label="庇护区"),
            "脆弱区": DAGOutput(node="zone_fragile", label="脆弱区"),
            "易伤区": DAGOutput(node="zone_vuln", label="易伤区"),
            "防御区": DAGOutput(node="zone_def", label="防御区"),
            "失衡易伤区": DAGOutput(node="zone_imbal", label="失衡易伤区"),
            "抗性区": DAGOutput(node="zone_res", label="抗性区"),
            "非主控减伤区": DAGOutput(node="zone_ncr", label="非主控减伤区"),
            "连击增伤区": DAGOutput(node="zone_combo", label="连击增伤区"),
            "特殊乘区": DAGOutput(node="zone_special", label="特殊乘区"),
            "基础伤害区": DAGOutput(node="zone_base", label="基础伤害区"),
            "力量最终值": DAGOutput(node="attr_力量_total", label="力量最终值"),
            "敏捷最终值": DAGOutput(node="attr_敏捷_total", label="敏捷最终值"),
            "智识最终值": DAGOutput(node="attr_智识_total", label="智识最终值"),
            "意志最终值": DAGOutput(node="attr_意志_total", label="意志最终值"),
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
