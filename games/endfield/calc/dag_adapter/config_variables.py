#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""终末地 DAG 主图输入变量表（P2-07 从 ``config.py`` 拆出）。"""

from __future__ import annotations

from calc_framework.dag.schema import DAGVariable


def _make_variables() -> dict[str, DAGVariable]:
    """构建主图输入变量表（角色/武器/装备/敌方/中间计算值）。"""
    return {
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
    }
