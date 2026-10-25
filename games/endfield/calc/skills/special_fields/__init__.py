#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""武器有条件特殊能力字段。"""

from .codec import (
    LEGACY_SPECIAL_KEY,
    SPECIAL_FIELD_KEYS,
    build_special_field,
    infer_max_stack_from_special,
    is_accidental_rank_multiple_curve,
    parse_special_field,
)
from .name_utils import bonus_attribute_keys, bonus_curve_for_key, weapon_special_field_keys
from .runtime_bonus import (
    add_special_picks_attack_percent,
    add_special_picks_to_ability_pct,
    add_special_picks_to_main_sub_bonus,
    apply_conditional_special_to_stats,
    get_special_value_at_level,
    migrate_legacy_weapon_special_level,
    special_pick_bonus,
)
from .skills_schema import (
    migrate_weapon_record_to_skill_schema,
    migrate_weapon_records_to_skill_schema,
    read_weapon_skills_schema,
    write_weapon_skills_schema,
)
from .slots_io import read_weapon_special_slots, write_weapon_special_slots

__all__ = [
    "LEGACY_SPECIAL_KEY",
    "SPECIAL_FIELD_KEYS",
    "add_special_picks_attack_percent",
    "add_special_picks_to_ability_pct",
    "add_special_picks_to_main_sub_bonus",
    "apply_conditional_special_to_stats",
    "bonus_attribute_keys",
    "bonus_curve_for_key",
    "build_special_field",
    "get_special_value_at_level",
    "infer_max_stack_from_special",
    "is_accidental_rank_multiple_curve",
    "migrate_legacy_weapon_special_level",
    "migrate_weapon_record_to_skill_schema",
    "migrate_weapon_records_to_skill_schema",
    "parse_special_field",
    "read_weapon_skills_schema",
    "read_weapon_special_slots",
    "special_pick_bonus",
    "weapon_special_field_keys",
    "write_weapon_skills_schema",
    "write_weapon_special_slots",
]
