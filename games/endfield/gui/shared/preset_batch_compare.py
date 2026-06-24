#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""多条配装预设并行评估（供 GUI「多方案对比」）。"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from games.endfield.calc.core.parallel_evaluate import evaluate_parallel
from games.endfield.calc.damage.engine import DamageContext
from games.endfield.calc.loadout.attack_eval import final_attack_details_for_loadout
from games.endfield.calc.loadout.optimizer import LoadoutScore, OptimizerTask, WeaponCandidate, evaluate_task
from games.endfield.calc.multi_skill.optimizer import evaluate_multi_skill_task
from games.endfield.calc.search.evaluate.context import SearchEvalContext
from games.endfield.calc.search.evaluate.multi_skill import build_skill_scenarios_from_levels
from games.endfield.gui.app.loadout_preset import LoadoutPreset


@dataclass(frozen=True)
class PresetCompareRow:
    """单条预设的评估结果。"""

    label: str

    final_damage: float

    loadout_summary: str

    error: str = ""


def _find_by_name(rows: Sequence[dict[str, Any]], name: str) -> dict[str, Any] | None:
    target = (name or "").strip()

    if not target:
        return None

    for row in rows:
        if str(row.get("名称", "")) == target:
            return row

    """find by name。"""
    return None


def _empty_equipment(*, slot_kind: str) -> dict[str, Any]:
    return {
        "名称": "（空）",
        "装备种类": slot_kind,
        "部位": slot_kind,
        "套装": "",
        "效果": [],
        "三件套效果": [],
        "属性词条": [],
    }
    """empty equipment。"""


def _resolve_equipment(
    name: str | None,
    equipments: Sequence[dict[str, Any]],
    *,
    slot_kind: str,
) -> dict[str, Any]:
    if not (name or "").strip():
        return _empty_equipment(slot_kind=slot_kind)

    row = _find_by_name(equipments, str(name))

    if row is None:
        raise ValueError(f"未找到装备: {name}")

    """resolve equipment。"""
    return row


def _preset_label(preset: LoadoutPreset) -> str:
    base = f"{preset.char_name} / {preset.weapon_name}"

    if preset.note.strip():
        return f"{base}（{preset.note.strip()}）"

    """preset label。"""
    return base


def _build_eval_item(
    preset: LoadoutPreset,
    *,
    characters: Sequence[dict[str, Any]],
    weapons: Sequence[dict[str, Any]],
    equipments: Sequence[dict[str, Any]],
    enemy_defense: float,
) -> tuple[str, OptimizerTask, SearchEvalContext, DamageContext, bool, tuple, dict[str, int]]:
    char = _find_by_name(characters, preset.char_name)

    if char is None:
        raise ValueError(f"未找到角色: {preset.char_name}")

    weapon = _find_by_name(weapons, preset.weapon_name)

    if weapon is None:
        raise ValueError(f"未找到武器: {preset.weapon_name}")

    fixed = preset.fixed_equipment_names

    chest = _resolve_equipment(fixed.get("chest"), equipments, slot_kind="护甲")

    gloves = _resolve_equipment(fixed.get("gloves"), equipments, slot_kind="护手")

    acc_a = _resolve_equipment(fixed.get("accessory_a"), equipments, slot_kind="配件")

    acc_b = _resolve_equipment(fixed.get("accessory_b"), equipments, slot_kind="配件")

    final = final_attack_details_for_loadout(
        character=char,
        weapon=weapon,
        char_level=preset.char_level,
        weapon_level=preset.weapon_level,
        trust_level=preset.trust_level,
        weapon_normal_levels=preset.weapon_normal_levels,
        weapon_special_states=preset.weapon_special_states,
    )

    weapon_candidate = WeaponCandidate(
        name=str(weapon.get("名称", preset.weapon_name)),
        final_attack=float(final["final_attack"]),
    )

    task: OptimizerTask = (weapon_candidate, (chest, gloves, acc_a, acc_b))

    search_eval = SearchEvalContext(
        char_data=char,
        char_level=preset.char_level,
        weapon_level=preset.weapon_level,
        trust_level=preset.trust_level,
        weapon_data_by_name={str(weapon.get("名称", "")): weapon},
        weapon_normal_levels=tuple(int(v) for v in preset.weapon_normal_levels),
        weapon_special_states=tuple(dict(s) for s in preset.weapon_special_states),
    )

    scenarios = tuple(
        build_skill_scenarios_from_levels(
            char,
            skill_1_level=preset.skill_levels[0],
            skill_2_level=preset.skill_levels[1],
            skill_3_level=preset.skill_levels[2],
        )
    )

    if not scenarios:
        raise ValueError("技能等级均为 0 或无有效倍率")

    from games.endfield.calc.skills.segments import normalize_manual_segment_counts

    counts = normalize_manual_segment_counts(
        {
            "战技": max(0, int(preset.multi_skill_counts.get("战技", 0))),
            "连携技": max(0, int(preset.multi_skill_counts.get("连携技", 0))),
            "终结技": max(0, int(preset.multi_skill_counts.get("终结技", 0))),
            **{k: int(v) for k, v in preset.multi_skill_counts.items() if ":" in k},
        },
        list(scenarios),
    )

    use_multi = bool(preset.use_manual_multi_skill_counts) and any(counts.values())

    primary = scenarios[0]

    if use_multi:
        base_context = DamageContext(
            final_attack=0.0,
            skill_multiplier=1.0,
            skill_type=primary.resolved_skill_type,
            enemy_defense=float(enemy_defense),
        )

        active_counts = {k: v for k, v in counts.items() if v > 0}

    else:
        base_context = DamageContext(
            final_attack=0.0,
            skill_multiplier=primary.skill_multiplier,
            skill_type=primary.resolved_skill_type,
            enemy_defense=float(enemy_defense),
        )

        active_counts = {primary.scenario_key: 1}

    """build eval item。"""
    return _preset_label(preset), task, search_eval, base_context, use_multi, scenarios, active_counts


def _evaluate_item(
    item: tuple[str, OptimizerTask, SearchEvalContext, DamageContext, bool, tuple, dict[str, int]],
) -> PresetCompareRow:
    label, task, search_eval, base_ctx, use_multi, scenarios, counts = item

    try:
        if use_multi:
            score: LoadoutScore = evaluate_multi_skill_task(
                shared_context=base_ctx,
                crit_mode="non_crit",
                task=task,
                scenarios=scenarios,
                skill_counts=counts,
                search_eval=search_eval,
            )

        else:
            score = evaluate_task(
                base_context=base_ctx,
                crit_mode="non_crit",
                task=task,
                search_eval=search_eval,
            )

        names = score.loadout_names

        summary = (
            f"武器:{score.weapon_name} | 护甲:{names.get('chest', '')} "
            f"护手:{names.get('gloves', '')} 配件A:{names.get('accessory_a', '')} "
            f"配件B:{names.get('accessory_b', '')}"
        )

        return PresetCompareRow(label=label, final_damage=float(score.final_damage), loadout_summary=summary)

    except Exception as exc:
        """evaluate item。"""
        return PresetCompareRow(label=label, final_damage=0.0, loadout_summary="", error=str(exc))


def compare_presets_parallel(
    presets: Sequence[LoadoutPreset],
    *,
    characters: Sequence[dict[str, Any]],
    weapons: Sequence[dict[str, Any]],
    equipments: Sequence[dict[str, Any]],
    enemy_defense: float = 100.0,
    max_workers: int = 1,
) -> list[PresetCompareRow]:
    """并行评估多条预设；成功项按伤害降序，失败项在后。"""

    if not presets:
        return []

    prepared: list[tuple[str, OptimizerTask, SearchEvalContext, DamageContext, bool, tuple, dict[str, int]]] = []

    errors: list[PresetCompareRow] = []

    for preset in presets:
        try:
            prepared.append(
                _build_eval_item(
                    preset,
                    characters=characters,
                    weapons=weapons,
                    equipments=equipments,
                    enemy_defense=enemy_defense,
                )
            )

        except Exception as exc:
            errors.append(
                PresetCompareRow(
                    label=_preset_label(preset),
                    final_damage=0.0,
                    loadout_summary="",
                    error=str(exc),
                )
            )

    if not prepared:
        return errors

    evaluated = evaluate_parallel(prepared, _evaluate_item, max_workers=max_workers)

    ok_rows = sorted([r for r in evaluated if not r.error], key=lambda r: r.final_damage, reverse=True)

    err_rows = [r for r in evaluated if r.error]

    return ok_rows + err_rows + errors
