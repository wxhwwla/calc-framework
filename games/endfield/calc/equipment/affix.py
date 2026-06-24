#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""装备属性词条解析（面板词条 → 伤害效果 / 平铺属性）。"""

from __future__ import annotations

import re
from typing import Any

from games.endfield.calc.damage.engine import DamageEffect
from games.endfield.calc.equipment.system import FourSlotLoadout, _infer_damage_types, _parse_percent_value

_STAT_FLAT_RE = re.compile(r"^(力量|敏捷|智识|意志|攻击力|防御力|生命值)(\d+(?:\.\d+)?)(%?)$")
_SKILL_BONUS_RE = re.compile(r"^(战技|连携技|终结技|普通攻击)伤害(?:加成)?(\d+(?:\.\d+)?)%?$")
_ALL_SKILL_BONUS_RE = re.compile(r"^全技能伤害(?:加成)?(\d+(?:\.\d+)?)%?$")
_DAMAGE_BONUS_RE = re.compile(r"^(物理|灼热|电磁|寒冷|自然|法术|超域)?伤害(?:加成)?(\d+(?:\.\d+)?)%?$")
_ORIGINIUM_ARTS_RE = re.compile(r"^源石技艺强度(\d+(?:\.\d+)?)$")


def parse_equipment_affix_line(
    text: str,
    *,
    source: str,
) -> tuple[list[DamageEffect], dict[str, float]]:
    """
    解析单条属性词条或效果短句。

    返回 (伤害相关效果列表, 平铺属性加成字典)。
    """
    raw = (text or "").strip()
    if not raw:
        return [], {}

    effects: list[DamageEffect] = []
    flat_stats: dict[str, float] = {}

    compact = raw.replace(" ", "")
    skill_match = _SKILL_BONUS_RE.search(compact)
    if skill_match:
        skill_name = skill_match.group(1)
        value = float(skill_match.group(2)) / 100.0
        effects.append(
            DamageEffect(
                effect_type="技能类型伤害加成",
                value=value,
                source=source,
                raw_text=raw,
                skill_types=(skill_name,),
            )
        )
        return effects, flat_stats

    all_skill_match = _ALL_SKILL_BONUS_RE.search(compact)
    if all_skill_match:
        value = float(all_skill_match.group(1)) / 100.0
        effects.append(
            DamageEffect(
                effect_type="技能类型伤害加成",
                value=value,
                source=source,
                raw_text=raw,
                skill_types=("战技", "连携技", "终结技"),
            )
        )
        return effects, flat_stats

    originium_match = _ORIGINIUM_ARTS_RE.search(compact)
    if originium_match:
        from games.endfield.calc.damage.originium_arts import ORIGINIUM_FLAT_STAT_KEY
        from games.endfield.calc.equipment.display_corrections import correct_originium_display

        shown = float(originium_match.group(1))
        actual = correct_originium_display(int(shown)) if shown == int(shown) else shown
        flat_stats[ORIGINIUM_FLAT_STAT_KEY] = flat_stats.get(ORIGINIUM_FLAT_STAT_KEY, 0.0) + actual
        return effects, flat_stats

    dmg_match = _DAMAGE_BONUS_RE.search(compact)
    if dmg_match and dmg_match.group(1):
        tag = dmg_match.group(1)
        value = float(dmg_match.group(2)) / 100.0
        damage_types = _infer_damage_types(tag)
        effects.append(
            DamageEffect(
                effect_type="伤害类型伤害加成",
                value=value,
                source=source,
                raw_text=raw,
                damage_types=damage_types,
            )
        )
        return effects, flat_stats

    stat_match = _STAT_FLAT_RE.match(raw.replace(" ", ""))
    if stat_match:
        name = stat_match.group(1)
        value = float(stat_match.group(2))
        is_percent = bool(stat_match.group(3))
        if name == "攻击力" and is_percent:
            from games.endfield.calc.equipment.display_corrections import correct_percent_display

            pct = correct_percent_display(value)
            effects.append(
                DamageEffect(
                    effect_type="装备攻击力加成",
                    value=pct / 100.0,
                    source=source,
                    raw_text=raw,
                )
            )
        elif not is_percent and name in ("力量", "敏捷", "智识", "意志", "攻击力", "防御力"):
            from games.endfield.calc.equipment.display_corrections import correct_flat_stat_value

            flat_stats[name] = flat_stats.get(name, 0.0) + correct_flat_stat_value(name, value)
        return effects, flat_stats

    # 套装/效果长句中的「物理伤害+20%」等
    if "伤害" in raw and "%" in raw:
        value = _parse_percent_value(raw)
        if value > 0:
            damage_types = _infer_damage_types(raw)
            if damage_types:
                effects.append(
                    DamageEffect(
                        effect_type="伤害类型伤害加成",
                        value=value,
                        source=source,
                        raw_text=raw,
                        damage_types=damage_types,
                    )
                )
            elif "伤害+" in raw or "伤害加成" in raw:
                effects.append(
                    DamageEffect(
                        effect_type="其他伤害加成",
                        value=value,
                        source=source,
                        raw_text=raw,
                    )
                )

    originium_in_sentence = re.search(r"源石技艺强度\+?(\d+(?:\.\d+)?)", raw)
    if originium_in_sentence:
        from games.endfield.calc.damage.originium_arts import ORIGINIUM_FLAT_STAT_KEY

        flat_stats[ORIGINIUM_FLAT_STAT_KEY] = flat_stats.get(ORIGINIUM_FLAT_STAT_KEY, 0.0) + float(
            originium_in_sentence.group(1)
        )

    stat_in_sentence = re.search(
        r"(力量|敏捷|智识|意志)\+(\d+(?:\.\d+)?)(?!%)",
        raw,
    )
    if stat_in_sentence:
        flat_stats[stat_in_sentence.group(1)] = flat_stats.get(stat_in_sentence.group(1), 0.0) + float(
            stat_in_sentence.group(2)
        )

    return effects, flat_stats


def parse_equipment_effect_block(text: str, *, source: str) -> tuple[list[DamageEffect], dict[str, float]]:
    """解析可能含多句的套装效果文案。"""
    all_effects: list[DamageEffect] = []
    all_flats: dict[str, float] = {}
    for part in re.split(r"[。；;\n]", text):
        effs, flats = parse_equipment_affix_line(part, source=source)
        all_effects.extend(effs)
        for key, val in flats.items():
            all_flats[key] = all_flats.get(key, 0.0) + val
    return all_effects, all_flats


def aggregate_loadout_modifiers(
    loadout: FourSlotLoadout,
) -> tuple[list[DamageEffect], dict[str, float], float]:
    """汇总四格装备的属性词条平铺、套装效果与百分比攻击力加成。"""
    items = [loadout.chest, loadout.gloves, loadout.accessory_a, loadout.accessory_b]
    effects: list[DamageEffect] = []
    flat_stats: dict[str, float] = {}
    attack_percent = 0.0

    def _absorb_item(item: dict[str, Any]) -> None:
        nonlocal attack_percent
        for eff in item.get("效果") or []:
            if getattr(eff, "effect_type", "") == "装备攻击力加成":
                attack_percent += float(eff.value)
            else:
                effects.append(eff)
        for key, val in (item.get("flat_stats") or {}).items():
            flat_stats[key] = flat_stats.get(key, 0.0) + float(val)
        """absorb item。"""

    for item in items:
        _absorb_item(item)

    # 同套装满 3 件时，合并该套装第一件上的「三件套效果」
    set_counts: dict[str, int] = {}
    for item in items:
        set_id = str(item.get("套装") or "").strip()
        if set_id:
            set_counts[set_id] = set_counts.get(set_id, 0) + 1
    for set_id, count in set_counts.items():
        if count < 3:
            continue
        for item in items:
            if str(item.get("套装") or "").strip() != set_id:
                continue
            for eff in item.get("三件套效果") or []:
                if getattr(eff, "effect_type", "") == "装备攻击力加成":
                    attack_percent += float(eff.value)
                else:
                    effects.append(eff)
            break

    return effects, flat_stats, attack_percent
