# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""效果类型 → 整数 ID 映射（消除字符串匹配开销）。

与 Rust 侧 `effect_id.rs` 保持一致。
"""

from __future__ import annotations

# 效果类型 ID（与 Rust 侧一致）
EFFECT_DAMAGE_REDUCTION = 0
EFFECT_AMPLIFICATION = 1
EFFECT_WEAKNESS = 2
EFFECT_SHELTER = 3
EFFECT_FRAGILE = 4
EFFECT_VULNERABILITY = 5
EFFECT_COMBO_BONUS = 6
EFFECT_DAMAGE_BONUS = 7
EFFECT_IGNORE_RESISTANCE = 8
EFFECT_RESISTANCE = 9
EFFECT_DEFENSE = 10
EFFECT_IMBALANCE_COEFF = 11
EFFECT_NON_CONTROL_REDUCTION = 12
EFFECT_SPECIAL_ZONE = 13

# 效果类型字符串 → ID 映射
_EFFECT_TYPE_MAP: dict[str, int] = {
    "伤害减免": EFFECT_DAMAGE_REDUCTION,
    "增幅": EFFECT_AMPLIFICATION,
    "虚弱": EFFECT_WEAKNESS,
    "庇护": EFFECT_SHELTER,
    "脆弱": EFFECT_FRAGILE,
    "易伤": EFFECT_VULNERABILITY,
    "连击增伤": EFFECT_COMBO_BONUS,
    "伤害类型伤害加成": EFFECT_DAMAGE_BONUS,
    "技能类型伤害加成": EFFECT_DAMAGE_BONUS,
    "失衡伤害加成": EFFECT_DAMAGE_BONUS,
    "其他伤害加成": EFFECT_DAMAGE_BONUS,
    "无视抗性": EFFECT_IGNORE_RESISTANCE,
    "抗性": EFFECT_RESISTANCE,
    "防御": EFFECT_DEFENSE,
    "失衡易伤系数": EFFECT_IMBALANCE_COEFF,
    "非主控减伤": EFFECT_NON_CONTROL_REDUCTION,
    "特殊乘区": EFFECT_SPECIAL_ZONE,
}

# 技能类型 ID（与 Rust 侧一致）
SKILL_TYPE_NORMAL = 0
SKILL_TYPE_ULTIMATE = 1

# 技能类型字符串 → ID 映射
SKILL_TYPE_MAP: dict[str, int] = {
    "终结技": SKILL_TYPE_ULTIMATE,
}

# 暴击模式 ID（与 Rust 侧一致）
CRIT_MODE_NON_CRIT = 0
CRIT_MODE_ALWAYS_CRIT = 1
CRIT_MODE_EXPECTED = 2

# 暴击模式字符串 → ID 映射
_CRIT_MODE_MAP: dict[str, int] = {
    "always_crit": CRIT_MODE_ALWAYS_CRIT,
    "expected": CRIT_MODE_EXPECTED,
}


def effect_type_to_id(name: str) -> int:
    """效果类型字符串 → 整数 ID。未知类型返回 0。"""
    return _EFFECT_TYPE_MAP.get(name, 0)


def crit_mode_to_id(name: str) -> int:
    """暴击模式字符串 → 整数 ID。"""
    return _CRIT_MODE_MAP.get(name, CRIT_MODE_NON_CRIT)


__all__ = [
    "CRIT_MODE_ALWAYS_CRIT",
    "CRIT_MODE_EXPECTED",
    "CRIT_MODE_NON_CRIT",
    "EFFECT_COMBO_BONUS",
    "EFFECT_DAMAGE_BONUS",
    "EFFECT_DAMAGE_REDUCTION",
    "EFFECT_DEFENSE",
    "EFFECT_FRAGILE",
    "EFFECT_IGNORE_RESISTANCE",
    "EFFECT_IMBALANCE_COEFF",
    "EFFECT_NON_CONTROL_REDUCTION",
    "EFFECT_RESISTANCE",
    "EFFECT_SHELTER",
    "EFFECT_SPECIAL_ZONE",
    "EFFECT_VULNERABILITY",
    "EFFECT_WEAKNESS",
    "SKILL_TYPE_MAP",
    "SKILL_TYPE_NORMAL",
    "SKILL_TYPE_ULTIMATE",
    "crit_mode_to_id",
    "effect_type_to_id",
]
