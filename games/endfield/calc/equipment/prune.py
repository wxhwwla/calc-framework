#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""装备剪枝：按角色主/副能力与目标技能类型排序候选。"""



from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

from games.endfield.calc.equipment.affix import parse_equipment_affix_line

_STAT_FLAT_IN_AFFIX = re.compile(r"^(力量|敏捷|智识|意志|攻击力)(\d+(?:\.\d+)?)(%?)$")





def character_ability_attrs(character: dict[str, Any]) -> tuple[str, str]:

    """读取角色主能力、副能力对应的四维名称。"""

    return (

        str(character.get("主能力") or "").strip(),

        str(character.get("副能力") or "").strip(),

    )





def _iter_equipment_text_lines(item: dict[str, Any]) -> Iterable[str]:

    for text in item.get("属性词条") or []:

        if text:

            yield str(text)

    for block in item.get("效果") or []:

        raw = getattr(block, "raw_text", None) or str(block)

        if raw:

            yield str(raw)

    for block in item.get("三件套效果") or []:

        raw = getattr(block, "raw_text", None) or str(block)

        if raw:

            yield str(raw)
    """iter equipment text lines。"""





def _collect_flat_stats_from_item(item: dict[str, Any]) -> dict[str, float]:

    flats: dict[str, float] = {}

    for line in _iter_equipment_text_lines(item):

        _, part = parse_equipment_affix_line(line, source="")

        for key, val in part.items():

            flats[key] = flats.get(key, 0.0) + float(val)

        compact = line.replace(" ", "")

        m = _STAT_FLAT_IN_AFFIX.match(compact)

        if m and not m.group(3):

            name = m.group(1)

            if name in ("力量", "敏捷", "智识", "意志"):

                flats[name] = flats.get(name, 0.0) + float(m.group(2))

    return flats
    """collect flat stats from item。"""





def _has_ability_percent_tag(item: dict[str, Any], *, tag: str) -> bool:

    needle = tag.replace(" ", "")

    for line in _iter_equipment_text_lines(item):

        compact = line.replace(" ", "")

        if needle in compact and "%" in compact:

            return True

    return False
    """has ability percent tag。"""





def equipment_stat_affinity_tier(

    item: dict[str, Any],

    main_attr: str,

    sub_attr: str,

) -> int:

    """

    主/副属性契合度（数值越小越优先）。



    0 同时含主、副；1 仅主；2 仅副；3 皆无。

    """

    flats = _collect_flat_stats_from_item(item)

    has_main = bool((main_attr and flats.get(main_attr, 0.0) > 0) or _has_ability_percent_tag(item, tag="主能力"))

    has_sub = bool((sub_attr and flats.get(sub_attr, 0.0) > 0) or _has_ability_percent_tag(item, tag="副能力"))

    if has_main and has_sub:

        return 0

    if has_main:

        return 1

    if has_sub:

        return 2

    return 3





def equipment_has_skill_damage_bonus(item: dict[str, Any], skill_type: str) -> bool:

    """装备词条或效果是否含指定技能类型的伤害加成。"""

    if not skill_type:

        return False

    needle = f"{skill_type}伤害"

    return any(needle in line.replace(" ", "") for line in _iter_equipment_text_lines(item))





def equipment_skill_affinity_tier(

    item: dict[str, Any],

    skill_types: tuple[str, ...],

) -> int:

    """0=对任一目标技能有加成；1=无加成。"""

    if not skill_types:

        return 1

    for skill in skill_types:

        if equipment_has_skill_damage_bonus(item, skill):

            return 0

    return 1





def equipment_prune_sort_key(

    item: dict[str, Any],

    main_attr: str,

    sub_attr: str,

    skill_types: tuple[str, ...],

) -> tuple[int, int, str]:

    """排序键：主副属性契合 → 技能加成 → 名称。"""

    return (

        equipment_stat_affinity_tier(item, main_attr, sub_attr),

        equipment_skill_affinity_tier(item, skill_types),

        str(item.get("名称", "")),

    )





def sort_equipment_catalog_by_priority(

    catalog: dict[str, list[dict[str, Any]]],

    *,

    main_attr: str,

    sub_attr: str,

    skill_types: tuple[str, ...],

) -> dict[str, list[dict[str, Any]]]:

    """各部位内按剪枝优先级排序（不改变件数）。"""

    result: dict[str, list[dict[str, Any]]] = {}

    for slot in ("chest", "gloves", "accessories"):

        items = list(catalog.get(slot) or [])

        items.sort(key=lambda it: equipment_prune_sort_key(it, main_attr, sub_attr, skill_types))

        result[slot] = items

    return result

