#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""终末地 DAG 主图节点表（P2-07 从 ``config.py`` 拆出）。"""

from __future__ import annotations

from calc_framework.dag.schema import BinaryNode, CallNode, NodeType, VarNode


def _make_nodes() -> dict[str, NodeType]:
    """构建主图节点表：输入 VarNode、属性合计节点与 6 个 CallNode 块。"""
    return {
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
    }
