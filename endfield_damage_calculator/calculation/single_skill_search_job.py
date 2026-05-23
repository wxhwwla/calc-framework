#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""单技能全量搜索作业（无头组装，供 GUI / 测试复用）。"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Optional

from calculation.damage_engine import DamageContext
from calculation.multiplicative_zones.final_attack_zone import calculate_final_attack_with_details
from calculation.loadout_optimizer import WeaponCandidate
from calculation.loadout_slot_search import FixedLoadoutSelection
from calculation.multi_skill_search_eval import MultiSkillSearchEval
from data.equipment_catalog import catalog_full_search_error


@dataclass(frozen=True)
class SingleSkillSearchJob:
    """全量单技能搜索所需上下文。"""

    char_data: dict[str, Any]
    char_level: int
    weapon_level: int
    trust_level: int
    skill_label: str
    weapon_scope: str
    equipment_scope: str
    fixed_loadout: FixedLoadoutSelection
    base_context: DamageContext
    weapon_candidates: tuple[WeaponCandidate, ...]
    equipment_catalog: dict[str, list[dict[str, Any]]]
    weapon_data_by_name: dict[str, dict[str, Any]]
    run_signature: str
    multi_skill_eval: Optional[MultiSkillSearchEval] = None


def build_weapon_candidates(
    *,
    all_weapons: list[dict[str, Any]],
    char_data: dict[str, Any],
    current_weapon: dict[str, Any],
    weapon_scope_label: str,
    char_level: int,
    weapon_level: int,
    trust_level: int,
) -> list[WeaponCandidate]:
    """按武器候选范围生成 WeaponCandidate 列表。"""
    scope = (weapon_scope_label or "").strip()
    weapon_type = str(char_data.get("武器", ""))
    current_star = current_weapon.get("星级")
    current_name = current_weapon.get("名称")

    candidates: list[WeaponCandidate] = []
    for weapon in all_weapons:
        if weapon.get("类型") != weapon_type:
            continue
        if scope == "同类型同星级" and weapon.get("星级") != current_star:
            continue
        if scope == "当前武器" and weapon.get("名称") != current_name:
            continue
        details = calculate_final_attack_with_details(
            character=char_data,
            weapon=weapon,
            char_level=char_level,
            weapon_level=weapon_level,
            trust_level=trust_level,
        )
        candidates.append(
            WeaponCandidate(
                name=str(weapon.get("名称", "")),
                final_attack=float(details.get("final_attack", 0.0)),
            )
        )
    return candidates


def build_run_signature(
    *,
    char_data: dict[str, Any],
    char_level: int,
    weapon_level: int,
    trust_level: int,
    skill_name: str,
    weapon_count: int,
    chest_count: int,
    weapon_scope_label: str,
    equipment_scope_label: str,
    fixed_loadout: FixedLoadoutSelection,
    multi_skill_token: str = "",
) -> str:
    """
    生成续跑用 run_signature（写入 search_runs.db）。

    任一搜索参数（等级、技能、武器/装备范围、固定配装等）变化都会得到新签名，
    避免与旧库的 total_combinations / 已处理 key 混用。
    """
    seed = (
        f"{char_data.get('名称', '')}-lv{char_level}-wlv{weapon_level}-trust{trust_level}-"
        f"{skill_name}-w{weapon_count}-e{chest_count}-"
        f"{weapon_scope_label}-{equipment_scope_label}-"
        f"{fixed_loadout.signature_token()}-{multi_skill_token}"
    )
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:16]


def prepare_single_skill_search_job(
    *,
    char_data: dict[str, Any],
    char_level: int,
    weapon_level: int,
    trust_level: int,
    skill_name: str,
    skill_type: str,
    skill_multiplier: float,
    weapon_scope_label: str,
    equipment_scope_label: str,
    fixed_loadout: Optional[FixedLoadoutSelection] = None,
    all_weapons: list[dict[str, Any]],
    current_weapon: dict[str, Any],
    equipment_catalog: dict[str, list[dict[str, Any]]],
    multi_skill_eval: Optional[MultiSkillSearchEval] = None,
) -> tuple[Optional[SingleSkillSearchJob], Optional[str]]:
    """
    组装搜索作业。

    返回 (job, None) 或 (None, 用户可读错误文案)。
    """
    catalog_err = catalog_full_search_error(equipment_catalog)
    if catalog_err:
        return None, catalog_err

    weapon_candidates = build_weapon_candidates(
        all_weapons=all_weapons,
        char_data=char_data,
        current_weapon=current_weapon,
        weapon_scope_label=weapon_scope_label,
        char_level=char_level,
        weapon_level=weapon_level,
        trust_level=trust_level,
    )
    if not weapon_candidates:
        return None, "当前武器/装备候选范围下无可用武器。"

    multi_token = multi_skill_eval.signature_token() if multi_skill_eval else ""
    run_signature = build_run_signature(
        char_data=char_data,
        char_level=char_level,
        weapon_level=weapon_level,
        trust_level=trust_level,
        skill_name=skill_name,
        weapon_count=len(weapon_candidates),
        chest_count=len(equipment_catalog["chest"]),
        weapon_scope_label=weapon_scope_label,
        equipment_scope_label=equipment_scope_label,
        fixed_loadout=fixed_loadout or FixedLoadoutSelection(),
        multi_skill_token=multi_token,
    )
    weapon_data_by_name = {
        str(w.get("名称", "")): w for w in all_weapons if w.get("名称")
    }
    display_skill = multi_skill_eval.display_label if multi_skill_eval else skill_name
    job = SingleSkillSearchJob(
        char_data=char_data,
        char_level=char_level,
        weapon_level=weapon_level,
        trust_level=trust_level,
        skill_label=display_skill,
        weapon_scope=weapon_scope_label,
        equipment_scope=equipment_scope_label,
        fixed_loadout=fixed_loadout or FixedLoadoutSelection(),
        base_context=DamageContext(
            final_attack=0.0,
            skill_multiplier=float(skill_multiplier),
            skill_type=skill_type,
            enemy_defense=100.0,
        ),
        weapon_candidates=tuple(weapon_candidates),
        equipment_catalog=equipment_catalog,
        weapon_data_by_name=weapon_data_by_name,
        run_signature=run_signature,
        multi_skill_eval=multi_skill_eval,
    )
    return job, None


