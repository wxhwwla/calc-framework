# SPDX-License-Identifier: AGPL-3.0
"""异常附带效果（导电法术易伤、碎甲物理易伤、腐蚀减抗，NGA PART 02）。"""

from __future__ import annotations

from games.endfield.calc.damage.originium_arts import enhance_attached_effect

# 异常等级 1–4 对应的基础附带数值
VULNERABILITY_BY_ABNORMAL_LEVEL: tuple[float, ...] = (0.12, 0.16, 0.20, 0.24)
CORROSION_INITIAL_RES_SHRED: tuple[float, ...] = (3.6, 4.8, 6.0, 7.2)


def _level_index(calc_level: int) -> int:
    return min(max(1, int(calc_level)), 4) - 1
    """level index。"""


def conductive_spell_vulnerability(
    calc_level: int,
    *,
    originium_arts_strength: float = 0.0,
    effect_multiplier: float = 1.0,
) -> float:
    """导电：敌人受到的法术伤害提高（易伤区，法术类伤害）。"""
    base = VULNERABILITY_BY_ABNORMAL_LEVEL[_level_index(calc_level)] * effect_multiplier
    return enhance_attached_effect(base, originium_arts_strength)


def armor_break_physical_vulnerability(
    calc_level: int,
    *,
    originium_arts_strength: float = 0.0,
    effect_multiplier: float = 1.0,
) -> float:
    """碎甲：敌人受到的物理伤害提高。"""
    base = VULNERABILITY_BY_ABNORMAL_LEVEL[_level_index(calc_level)] * effect_multiplier
    return enhance_attached_effect(base, originium_arts_strength)


def corrosion_initial_resistance_shred(
    calc_level: int,
    *,
    originium_arts_strength: float = 0.0,
    effect_multiplier: float = 1.0,
) -> float:
    """腐蚀：初始降低全属性抗性点数（抗性区以点数变化接入）。"""
    base = CORROSION_INITIAL_RES_SHRED[_level_index(calc_level)] * effect_multiplier
    return enhance_attached_effect(base, originium_arts_strength)


_SPELL_VULN_TYPES = ("法术-灼热", "法术-电磁", "法术-寒冷", "法术-自然")


def build_physical_attached_effects(
    abnormal: str,
    calc_level: int,
    *,
    originium_arts_strength: float = 0.0,
    effect_multiplier: float = 1.0,
) -> list:
    from games.endfield.calc.damage.engine import DamageEffect

    if abnormal != "碎甲":
        return []
    vuln = armor_break_physical_vulnerability(
        calc_level,
        originium_arts_strength=originium_arts_strength,
        effect_multiplier=effect_multiplier,
    )
    return [
        DamageEffect(
            effect_type="易伤",
            value=vuln,
            damage_types=("物理",),
            source="碎甲附带",
            raw_text=f"物理易伤+{vuln * 100:.1f}%",
        )
    ]
    """build physical attached effects。"""


def build_spell_attached_effects(
    abnormal_key: str,
    formula: str,
    calc_level: int,
    *,
    originium_arts_strength: float = 0.0,
    effect_multiplier: float = 1.0,
    corrosion_duration_seconds: float | None = None,
) -> list:
    from games.endfield.calc.damage.engine import DamageEffect

    if formula != "cross_anomaly":
        return []
    out: list = []
    if abnormal_key == "电磁异常":
        vuln = conductive_spell_vulnerability(
            calc_level,
            originium_arts_strength=originium_arts_strength,
            effect_multiplier=effect_multiplier,
        )
        out.append(
            DamageEffect(
                effect_type="易伤",
                value=vuln,
                damage_types=_SPELL_VULN_TYPES,
                source="导电附带",
                raw_text=f"法术易伤+{vuln * 100:.1f}%",
            )
        )
    elif abnormal_key == "自然异常":
        from games.endfield.calc.damage.corrosion import (
            CORROSION_DURATION_SEC,
            corrosion_total_resistance_shred,
        )

        duration = float(corrosion_duration_seconds) if corrosion_duration_seconds is not None else CORROSION_DURATION_SEC
        shred = corrosion_total_resistance_shred(
            calc_level,
            elapsed_seconds=duration,
            originium_arts_strength=originium_arts_strength,
            effect_multiplier=effect_multiplier,
        )
        out.append(
            DamageEffect(
                effect_type="抗性",
                value=-shred,
                source="腐蚀附带",
                raw_text=f"全属性抗性-{shred:.2f}",
            )
        )
    return out
    """build spell attached effects。"""
