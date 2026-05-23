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
from data.equipment_catalog import is_equipment_catalog_complete


@dataclass(frozen=True)
class SingleSkillSearchJob:
    """全量单技能搜索所需上下文。"""

    char_data: dict[str, Any]
    skill_label: str
    weapon_scope: str
    equipment_scope: str
    base_context: DamageContext
    weapon_candidates: tuple[WeaponCandidate, ...]
    equipment_catalog: dict[str, list[dict[str, Any]]]
    run_signature: str


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
) -> str:
    """生成续跑用 run_signature。"""
    seed = (
        f"{char_data.get('名称', '')}-lv{char_level}-wlv{weapon_level}-trust{trust_level}-"
        f"{skill_name}-w{weapon_count}-e{chest_count}-"
        f"{weapon_scope_label}-{equipment_scope_label}"
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
    all_weapons: list[dict[str, Any]],
    current_weapon: dict[str, Any],
    equipment_catalog: dict[str, list[dict[str, Any]]],
) -> tuple[Optional[SingleSkillSearchJob], Optional[str]]:
    """
    组装搜索作业。

    返回 (job, None) 或 (None, 用户可读错误文案)。
    """
    if not is_equipment_catalog_complete(equipment_catalog):
        return None, "装备数据不完整（缺护甲/护手/配件）。请先执行 sync_equipments.py --apply 同步 Wiki 装备。"

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
    )
    job = SingleSkillSearchJob(
        char_data=char_data,
        skill_label=skill_name,
        weapon_scope=weapon_scope_label,
        equipment_scope=equipment_scope_label,
        base_context=DamageContext(
            final_attack=0.0,
            skill_multiplier=float(skill_multiplier),
            skill_type=skill_type,
            enemy_defense=100.0,
        ),
        weapon_candidates=tuple(weapon_candidates),
        equipment_catalog=equipment_catalog,
        run_signature=run_signature,
    )
    return job, None


def job_to_legacy_dict(job: SingleSkillSearchJob) -> dict[str, Any]:
    """转换为 GUI / mvp 沿用的 dict 结构。"""
    return {
        "char_data": job.char_data,
        "skill_label": job.skill_label,
        "weapon_scope": job.weapon_scope,
        "equipment_scope": job.equipment_scope,
        "base_context": job.base_context,
        "weapon_candidates": list(job.weapon_candidates),
        "equipment_catalog": job.equipment_catalog,
        "run_signature": job.run_signature,
    }
