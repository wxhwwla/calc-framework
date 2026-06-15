#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""终末地完整伤害公式 DAG JSON 配置文件生成脚本。

迁移自 ``multiplicative_zones.dag.config``。

输出文件位于 ``framework/src/calc_framework/configs/endfield_full.dag.json``。

6 块架构（ADR-0011 §3.2）：
- ``ability_bonus``（属性块）：能力值加成 = main_flat×(1+main_pct/100)×0.005 + ...
- ``final_attack``（攻击力块）：最终攻击力 = (char+weapon)×(1+atk_bonus)+add+equip×(1+ability_bonus)
- ``crit_zone``（暴击块）：暴击区 = 1 + 暴击率×(暴击伤害-1)
- ``base_damage_block``（基础伤害块）：final_attack×skill_mult×crit_zone
- ``buff_debuff_block``（增益/减益块）：7 个乘区连乘
- ``environment_block``（环境乘区块）：防御减伤 + 5 个环境乘区连乘

主图：6 个 CallNode 块通过链式绑定串联，展开后等价于原 70 节点扁平 DAG。
"""

# pyright: reportCallIssue=false

from __future__ import annotations

import json
import sys
from pathlib import Path

from calc_framework.logging import get_logger

_logger = get_logger(__name__)

_FRAMEWORK_DIR = Path(__file__).resolve().parents[4] / "framework"
_SRC_DIR = _FRAMEWORK_DIR / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from calc_framework.dag.schema import (
    BinaryNode,
    CallNode,
    DAGGraph,
    DAGOutput,
    DAGVariable,
    VarNode,
)
from calc_framework.dag.serializer import dag_to_dict

OUTPUT_PATH = _SRC_DIR / "calc_framework" / "configs" / "endfield_full.dag.json"


from ._subgraph_builders import (
    _make_ability_bonus_subgraph,
    _make_base_damage_block_subgraph,
    _make_buff_debuff_block_subgraph,
    _make_crit_zone_subgraph,
    _make_environment_block_subgraph,
    _make_final_attack_subgraph,
    _make_single_hit_damage_subgraph,
)


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
        variables={
            "character.基础攻击": DAGVariable(type="float", source="character", description="角色基础攻击力"),
            "weapon.基础攻击": DAGVariable(type="float", source="weapon", description="武器基础攻击力"),
            "weapon.攻击力+": DAGVariable(
                type="float",
                source="weapon",
                description="攻击力+ 小数加成（0.15 = 15%）",
            ),
            "weapon.附加攻击力+": DAGVariable(type="float", source="weapon", description="附加攻击力+ 平值"),
            "equipment.攻击力平值": DAGVariable(
                type="float",
                source="equipment",
                description="装备平铺攻击力",
                default=0.0,
            ),
            "computed.主能力平值加算": DAGVariable(
                type="float",
                source="computed",
                description="主能力平值全部来源",
            ),
            "computed.副能力平值加算": DAGVariable(type="float", source="computed", description="副能力平值全部来源"),
            "computed.主能力百分比": DAGVariable(type="float", source="computed", description="主能力百分比加成"),
            "computed.副能力百分比": DAGVariable(type="float", source="computed", description="副能力百分比加成"),
            "computed.技能倍率": DAGVariable(type="float", source="computed", description="技能倍率"),
            "computed.伤害加成": DAGVariable(
                type="float",
                source="computed",
                description="伤害加成区 = 1+类型+技能+失衡+其他",
            ),
            "computed.伤害减免": DAGVariable(type="float", source="computed", description="伤害减免区 = ∏(1-减免值)"),
            "computed.增幅": DAGVariable(type="float", source="computed", description="增幅区 = 1+Σ增幅值"),
            "computed.虚弱": DAGVariable(type="float", source="computed", description="虚弱区 = ∏(1-虚弱值)"),
            "computed.庇护": DAGVariable(type="float", source="computed", description="庇护区 = 1-max(庇护值)"),
            "computed.脆弱": DAGVariable(type="float", source="computed", description="脆弱区 = 1+Σ脆弱值"),
            "computed.易伤": DAGVariable(type="float", source="computed", description="易伤区 = 1+Σ易伤值"),
            "computed.失衡易伤": DAGVariable(type="float", source="computed", description="失衡易伤区"),
            "computed.抗性": DAGVariable(type="float", source="computed", description="抗性区"),
            "computed.非主控减伤": DAGVariable(type="float", source="computed", description="非主控减伤区"),
            "computed.连击增伤": DAGVariable(type="float", source="computed", description="连击增伤区"),
            "computed.特殊乘区": DAGVariable(type="float", source="computed", description="特殊乘区"),
            "character.暴击率": DAGVariable(
                type="float",
                source="character",
                description="暴击率（小数，如 0.05 = 5%）",
                default=0.05,
            ),
            "character.暴击伤害": DAGVariable(
                type="float",
                source="character",
                description="暴击伤害（小数，如 0.5 = 50%）",
                default=0.5,
            ),
            "enemy.防御": DAGVariable(
                type="float",
                source="enemy",
                description="敌方防御值",
                default=100,
            ),
            "character.力量": DAGVariable(
                type="float",
                source="character",
                description="力量基础值",
                default=0.0,
            ),
            "character.敏捷": DAGVariable(
                type="float",
                source="character",
                description="敏捷基础值",
                default=0.0,
            ),
            "character.智识": DAGVariable(
                type="float",
                source="character",
                description="智识基础值",
                default=0.0,
            ),
            "character.意志": DAGVariable(
                type="float",
                source="character",
                description="意志基础值",
                default=0.0,
            ),
            "computed.力量加成值": DAGVariable(
                type="float",
                source="computed",
                description="力量加成值（武器技能）",
                default=0.0,
            ),
            "computed.敏捷加成值": DAGVariable(
                type="float",
                source="computed",
                description="敏捷加成值（武器技能）",
                default=0.0,
            ),
            "computed.智识加成值": DAGVariable(
                type="float",
                source="computed",
                description="智识加成值（武器技能）",
                default=0.0,
            ),
            "computed.意志加成值": DAGVariable(
                type="float",
                source="computed",
                description="意志加成值（武器技能）",
                default=0.0,
            ),
            "character.基础生命值": DAGVariable(
                type="float",
                source="character",
                description="角色基础生命值",
                default=0.0,
            ),
            "character.基础防御力": DAGVariable(
                type="float",
                source="character",
                description="角色基础防御力",
                default=0.0,
            ),
            "weapon.精炼等级": DAGVariable(
                type="int",
                source="weapon",
                description="武器精炼等级（1-9）",
                default=1,
            ),
            "computed.武器精炼主能力值加成": DAGVariable(
                type="float",
                source="computed",
                description="武器精炼主能力值+加成",
                default=0.0,
            ),
            "computed.武器精炼附加攻击力加成": DAGVariable(
                type="float",
                source="computed",
                description="武器精炼附加攻击力+加成",
                default=0.0,
            ),
            "weapon.法术伤害+": DAGVariable(
                type="float",
                source="weapon",
                description="武器法术伤害+加成（小数）",
                default=0.0,
            ),
            "weapon.攻击力+平值": DAGVariable(
                type="float",
                source="weapon",
                description="武器攻击力+平值加成",
                default=0.0,
            ),
            "weapon.最大生命值+": DAGVariable(
                type="float",
                source="weapon",
                description="武器最大生命值+加成",
                default=0.0,
            ),
        },
        subgraphs={
            "ability_bonus": _make_ability_bonus_subgraph(),
            "final_attack": _make_final_attack_subgraph(),
            "single_hit_damage": _make_single_hit_damage_subgraph(),
            "crit_zone": _make_crit_zone_subgraph(),
            "base_damage_block": _make_base_damage_block_subgraph(),
            "buff_debuff_block": _make_buff_debuff_block_subgraph(),
            "environment_block": _make_environment_block_subgraph(),
        },
        nodes={
            # ── 输入 VarNodes ──
            "char_atk": VarNode(type="var", path="character.基础攻击", label="角色攻击"),
            "weapon_atk": VarNode(type="var", path="weapon.基础攻击", label="武器攻击"),
            "atk_bonus": VarNode(type="var", path="weapon.攻击力+", label="攻击力+"),
            "add_atk": VarNode(type="var", path="weapon.附加攻击力+", label="附加攻击"),
            "equip_atk": VarNode(type="var", path="equipment.攻击力平值", label="装备攻击"),
            "main_flat": VarNode(type="var", path="computed.主能力平值加算", label="主能力平值"),
            "sub_flat": VarNode(type="var", path="computed.副能力平值加算", label="副能力平值"),
            "main_pct": VarNode(type="var", path="computed.主能力百分比", label="主能力%"),
            "sub_pct": VarNode(type="var", path="computed.副能力百分比", label="副能力%"),
            "char_crit_rate": VarNode(type="var", path="character.暴击率", label="暴击率"),
            "char_crit_dmg": VarNode(type="var", path="character.暴击伤害", label="暴击伤害"),
            "enemy_def": VarNode(type="var", path="enemy.防御", label="敌方防御"),
            "skill_mult": VarNode(type="var", path="computed.技能倍率", label="技能倍率"),
            # computed zone VarNodes（由 Loader 填充）
            "zone_dmg_bonus": VarNode(type="var", path="computed.伤害加成", label="伤害加成区"),
            "zone_dmg_reduc": VarNode(type="var", path="computed.伤害减免", label="伤害减免区"),
            "zone_amp": VarNode(type="var", path="computed.增幅", label="增幅区"),
            "zone_weak": VarNode(type="var", path="computed.虚弱", label="虚弱区"),
            "zone_shelter": VarNode(type="var", path="computed.庇护", label="庇护区"),
            "zone_fragile": VarNode(type="var", path="computed.脆弱", label="脆弱区"),
            "zone_vuln": VarNode(type="var", path="computed.易伤", label="易伤区"),
            "zone_imbal": VarNode(type="var", path="computed.失衡易伤", label="失衡易伤区"),
            "zone_res": VarNode(type="var", path="computed.抗性", label="抗性区"),
            "zone_ncr": VarNode(type="var", path="computed.非主控减伤", label="非主控减伤区"),
            "zone_combo": VarNode(type="var", path="computed.连击增伤", label="连击增伤区"),
            "zone_special": VarNode(type="var", path="computed.特殊乘区", label="特殊乘区"),
            # 角色基础生命/防御
            "char_base_hp": VarNode(type="var", path="character.基础生命值", label="基础生命值"),
            "char_base_def": VarNode(type="var", path="character.基础防御力", label="基础防御力"),
            # 武器精炼
            "weapon_refine_lv": VarNode(type="var", path="weapon.精炼等级", label="精炼等级"),
            "weapon_refine_main_attr": VarNode(type="var", path="computed.武器精炼主能力值加成", label="精炼主能力值+"),
            "weapon_refine_add_atk": VarNode(type="var", path="computed.武器精炼附加攻击力加成", label="精炼附加攻击+"),
            # 武器被动效果
            "weapon_spell_dmg": VarNode(type="var", path="weapon.法术伤害+", label="法术伤害+"),
            "weapon_atk_flat": VarNode(type="var", path="weapon.攻击力+平值", label="攻击力+平值"),
            "weapon_max_hp": VarNode(type="var", path="weapon.最大生命值+", label="最大生命值+"),
            # 属性四维
            "char_attr_力量": VarNode(type="var", path="character.力量", label="力量基础"),
            "char_attr_敏捷": VarNode(type="var", path="character.敏捷", label="敏捷基础"),
            "char_attr_智识": VarNode(type="var", path="character.智识", label="智识基础"),
            "char_attr_意志": VarNode(type="var", path="character.意志", label="意志基础"),
            "comp_attr_力量_bonus": VarNode(type="var", path="computed.力量加成值", label="力量加成"),
            "comp_attr_敏捷_bonus": VarNode(type="var", path="computed.敏捷加成值", label="敏捷加成"),
            "comp_attr_智识_bonus": VarNode(type="var", path="computed.智识加成值", label="智识加成"),
            "comp_attr_意志_bonus": VarNode(type="var", path="computed.意志加成值", label="意志加成"),
            "attr_力量_total": BinaryNode(
                type="binary",
                op="+",
                lhs="char_attr_力量",
                rhs="comp_attr_力量_bonus",
                label="力量最终值",
            ),
            "attr_敏捷_total": BinaryNode(
                type="binary",
                op="+",
                lhs="char_attr_敏捷",
                rhs="comp_attr_敏捷_bonus",
                label="敏捷最终值",
            ),
            "attr_智识_total": BinaryNode(
                type="binary",
                op="+",
                lhs="char_attr_智识",
                rhs="comp_attr_智识_bonus",
                label="智识最终值",
            ),
            "attr_意志_total": BinaryNode(
                type="binary",
                op="+",
                lhs="char_attr_意志",
                rhs="comp_attr_意志_bonus",
                label="意志最终值",
            ),
            # ── 块 1：属性块 ──
            "block1_ability": CallNode(
                type="call",
                subgraph="ability_bonus",
                bindings={
                    "main_flat": "main_flat",
                    "sub_flat": "sub_flat",
                    "main_pct": "main_pct",
                    "sub_pct": "sub_pct",
                },
                label="属性块-能力值加成",
            ),
            # ── 块 2：攻击力块 ──
            "block2_attack": CallNode(
                type="call",
                subgraph="final_attack",
                bindings={
                    "char_base_atk": "char_atk",
                    "weapon_base_atk": "weapon_atk",
                    "atk_bonus": "atk_bonus",
                    "additional_atk": "add_atk",
                    "equip_flat_atk": "equip_atk",
                    "ability_bonus": "block1_ability",
                },
                label="攻击力块",
            ),
            # ── 块 3：暴击块 ──
            "block3_crit": CallNode(
                type="call",
                subgraph="crit_zone",
                bindings={
                    "crit_rate": "char_crit_rate",
                    "crit_damage": "char_crit_dmg",
                },
                label="暴击块",
            ),
            # ── 块 4：基础伤害块 ──
            "block4_base": CallNode(
                type="call",
                subgraph="base_damage_block",
                bindings={
                    "final_attack": "block2_attack",
                    "skill_mult": "skill_mult",
                    "crit_zone": "block3_crit",
                },
                label="基础伤害块",
            ),
            # ── 块 5：增益/减益块 ──
            "block5_buff": CallNode(
                type="call",
                subgraph="buff_debuff_block",
                bindings={
                    "damage_after_crit": "block4_base",
                    "zone_dmg_bonus": "zone_dmg_bonus",
                    "zone_dmg_reduc": "zone_dmg_reduc",
                    "zone_amp": "zone_amp",
                    "zone_weak": "zone_weak",
                    "zone_shelter": "zone_shelter",
                    "zone_fragile": "zone_fragile",
                    "zone_vuln": "zone_vuln",
                },
                label="增益减益块",
            ),
            # ── 块 6：环境乘区块 ──
            "block6_env": CallNode(
                type="call",
                subgraph="environment_block",
                bindings={
                    "damage_after_buff": "block5_buff",
                    "enemy_defense": "enemy_def",
                    "zone_imbal": "zone_imbal",
                    "zone_res": "zone_res",
                    "zone_ncr": "zone_ncr",
                    "zone_combo": "zone_combo",
                    "zone_special": "zone_special",
                },
                label="环境乘区块",
            ),
        },
        outputs={
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
    _logger.info("已生成: %s", out)
    _logger.info("  子图: %s", list(g.subgraphs.keys()))
    _logger.info("  节点: %d 个", len(g.nodes))
    _logger.info("  输出: %s", list(g.outputs.keys()))


if __name__ == "__main__":
    main()
