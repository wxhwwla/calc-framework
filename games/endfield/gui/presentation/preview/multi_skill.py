#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""单/多技能遍历快速预览文案（纯函数，无 CTk）。"""

from __future__ import annotations

from typing import Any

from calc_framework.ui.i18n import tr

from games.endfield.calc.core.preview_cache import cached_preview, sync_preview_dependencies
from games.endfield.calc.damage.engine import DamageContext
from games.endfield.calc.damage.physical_abnormal_state import format_break_defense_rotation_note
from games.endfield.calc.loadout.optimizer import (
    WeaponCandidate,
)
from games.endfield.calc.manual_buff.physical import (
    compose_damage_total,
    evaluate_physical_abnormal_total,
    format_abnormal_breakdown_lines,
)
from games.endfield.calc.manual_buff.spell import (
    evaluate_spell_abnormal_total,
    format_spell_abnormal_breakdown_lines,
)
from games.endfield.calc.multi_skill.optimizer import (
    MultiSkillConfig,
    SkillScenario,
    optimize_multi_skill_loadouts,
)
from games.endfield.calc.multiplicative_zones.final_attack_zone import calculate_final_attack_with_details
from games.endfield.calc.search.evaluate.multi_skill import build_skill_scenarios_from_levels
from games.endfield.calc.skills.segments import format_segment_breakdown_lines, normalize_manual_segment_counts
from games.endfield.data_loading.enemy_eval_params import EnemyEvalParams
from games.endfield.data_loading.equipment_catalog import catalog_preview_status_lines, sample_equipment_catalog


def _resolve_enemy_eval(
    enemy_defense: float,
    enemy_eval: EnemyEvalParams | None,
) -> EnemyEvalParams:
    if enemy_eval is not None:
        return enemy_eval
    return EnemyEvalParams.from_defense_only(enemy_defense)


def build_multi_skill_search_preview_lines(
    *,
    char_data: dict[str, Any] | None,
    weapon_data: dict[str, Any] | None,
    char_level: int,
    weapon_level: int,
    trust_level: int = 0,
    skill_1_level: int = 0,
    skill_2_level: int = 0,
    skill_3_level: int = 0,
    normal_skill_1_name: str = "",
    normal_skill_1_level: int = 1,
    normal_skill_2_name: str = "",
    normal_skill_2_level: int = 1,
    normal_skill_3_name: str = "",
    normal_skill_3_level: int = 0,
    special_skill_1_name: str = "",
    special_skill_1_level: int = 1,
    special_skill_1_stack: int = 1,
    special_skill_2_name: str = "",
    special_skill_2_level: int = 1,
    special_skill_2_stack: int = 1,
    manual_counts: dict[str, int] | None = None,
    use_manual_counts: bool = False,
    preview_equipment_catalog: dict[str, list[dict]] | None = None,
    preview_equipment_scope_label: str = "",
    enemy_defense: float = 100.0,
    physical_abnormal_counts: dict[str, int] | None = None,
    spell_abnormal_counts: dict[str, int] | None = None,
    damage_component_mode: str = "skill_and_abnormal",
    use_expected_crit: bool = False,
    extra_crit_rate: float = 0.0,
    extra_crit_damage: float = 0.0,
    enemy_eval: EnemyEvalParams | None = None,
) -> list[str]:
    """构建多技能遍历模式的快速预览文案（带缓存）。"""
    if not char_data or not weapon_data:
        return [tr("desktop.endfield.needValidCharWeaponShort")]

    resolved_enemy = _resolve_enemy_eval(enemy_defense, enemy_eval)

    sync_preview_dependencies(
        char_name=char_data.get("名称", ""),
        weapon_name=weapon_data.get("名称", ""),
        char_level=char_level,
        weapon_level=weapon_level,
        trust_level=trust_level,
        skill_1=skill_1_level,
        skill_2=skill_2_level,
        skill_3=skill_3_level,
        calculation_mode="multi_skill_search_preview",
        equipment_scope=preview_equipment_scope_label,
        enemy_defense=enemy_defense,
        enemy_eval_token=resolved_enemy.preview_cache_token(),
        multi_skill_counts=tuple(sorted((manual_counts or {}).items())),
        use_manual_multi_skill_counts=use_manual_counts,
        physical_abnormal_counts=tuple(sorted((physical_abnormal_counts or {}).items())),
        spell_abnormal_counts=tuple(sorted((spell_abnormal_counts or {}).items())),
        damage_component_mode=damage_component_mode,
        use_expected_crit=bool(use_expected_crit),
        extra_crit_rate=float(extra_crit_rate),
        extra_crit_damage=float(extra_crit_damage),
        normal_skill_1_name=normal_skill_1_name,
        normal_skill_1_level=int(normal_skill_1_level),
        normal_skill_2_name=normal_skill_2_name,
        normal_skill_2_level=int(normal_skill_2_level),
        normal_skill_3_name=normal_skill_3_name,
        normal_skill_3_level=int(normal_skill_3_level),
        special_skill_1_name=special_skill_1_name,
        special_skill_1_level=int(special_skill_1_level),
        special_skill_1_stack=int(special_skill_1_stack),
        special_skill_2_name=special_skill_2_name,
        special_skill_2_level=int(special_skill_2_level),
        special_skill_2_stack=int(special_skill_2_stack),
    )

    def _compute() -> list[str]:
        return _build_multi_skill_search_preview_lines_impl(
            char_data=char_data,
            weapon_data=weapon_data,
            char_level=char_level,
            weapon_level=weapon_level,
            trust_level=trust_level,
            skill_1_level=skill_1_level,
            skill_2_level=skill_2_level,
            skill_3_level=skill_3_level,
            normal_skill_1_name=normal_skill_1_name,
            normal_skill_1_level=normal_skill_1_level,
            normal_skill_2_name=normal_skill_2_name,
            normal_skill_2_level=normal_skill_2_level,
            normal_skill_3_name=normal_skill_3_name,
            normal_skill_3_level=normal_skill_3_level,
            special_skill_1_name=special_skill_1_name,
            special_skill_1_level=special_skill_1_level,
            special_skill_1_stack=special_skill_1_stack,
            special_skill_2_name=special_skill_2_name,
            special_skill_2_level=special_skill_2_level,
            special_skill_2_stack=special_skill_2_stack,
            manual_counts=manual_counts,
            use_manual_counts=use_manual_counts,
            preview_equipment_catalog=preview_equipment_catalog,
            preview_equipment_scope_label=preview_equipment_scope_label,
            enemy_defense=enemy_defense,
            physical_abnormal_counts=physical_abnormal_counts,
            spell_abnormal_counts=spell_abnormal_counts,
            damage_component_mode=damage_component_mode,
            use_expected_crit=use_expected_crit,
            extra_crit_rate=extra_crit_rate,
            extra_crit_damage=extra_crit_damage,
            enemy_eval=resolved_enemy,
        )

    lines, _ = cached_preview("multi_skill_search_preview", _compute)
    return lines


def _build_multi_skill_search_preview_lines_impl(
    *,
    char_data: dict[str, Any],
    weapon_data: dict[str, Any],
    char_level: int,
    weapon_level: int,
    trust_level: int = 0,
    skill_1_level: int = 0,
    skill_2_level: int = 0,
    skill_3_level: int = 0,
    normal_skill_1_name: str = "",
    normal_skill_1_level: int = 1,
    normal_skill_2_name: str = "",
    normal_skill_2_level: int = 1,
    normal_skill_3_name: str = "",
    normal_skill_3_level: int = 0,
    special_skill_1_name: str = "",
    special_skill_1_level: int = 1,
    special_skill_1_stack: int = 1,
    special_skill_2_name: str = "",
    special_skill_2_level: int = 1,
    special_skill_2_stack: int = 1,
    manual_counts: dict[str, int] | None = None,
    use_manual_counts: bool = False,
    preview_equipment_catalog: dict[str, list[dict]] | None = None,
    preview_equipment_scope_label: str = "",
    enemy_defense: float = 100.0,
    physical_abnormal_counts: dict[str, int] | None = None,
    spell_abnormal_counts: dict[str, int] | None = None,
    damage_component_mode: str = "skill_and_abnormal",
    use_expected_crit: bool = False,
    extra_crit_rate: float = 0.0,
    extra_crit_damage: float = 0.0,
    enemy_eval: EnemyEvalParams | None = None,
) -> list[str]:
    if not preview_equipment_catalog:
        return [
            tr("desktop.endfield.modeMultiSkillPreview"),
            tr("desktop.endfield.previewCatalogMissing"),
        ]
    catalog = preview_equipment_catalog
    blocked = catalog_preview_status_lines(
        catalog,
        mode_label=tr("desktop.endfield.modeMultiSkillPreviewLabel"),
    )
    if blocked:
        return blocked
    sampled_catalog = sample_equipment_catalog(catalog, per_slot=2)
    resolved_enemy = _resolve_enemy_eval(enemy_defense, enemy_eval)
    crit_rate = 0.05 + float(extra_crit_rate)
    crit_damage = 0.5 + float(extra_crit_damage)
    scenarios = build_skill_scenarios_from_levels(
        char_data,
        skill_1_level=skill_1_level,
        skill_2_level=skill_2_level,
        skill_3_level=skill_3_level,
    )
    if not scenarios:
        scenarios = [SkillScenario(skill_name="战技", skill_multiplier=1.0, skill_type="战技")]
        selected_skill = "战技"
        warning = tr("desktop.endfield.previewNoSkillFallback")
    else:
        selected_skill = scenarios[0].resolved_skill_type
        warning = ""
    final = calculate_final_attack_with_details(
        character=char_data,
        weapon=weapon_data,
        char_level=char_level,
        weapon_level=weapon_level,
        trust_level=trust_level,
        normal_skill_1_name=normal_skill_1_name,
        normal_skill_1_level=normal_skill_1_level,
        normal_skill_2_name=normal_skill_2_name,
        normal_skill_2_level=normal_skill_2_level,
        normal_skill_3_name=normal_skill_3_name,
        normal_skill_3_level=normal_skill_3_level,
        special_skill_1_name=special_skill_1_name,
        special_skill_1_level=special_skill_1_level,
        special_skill_1_stack=special_skill_1_stack,
        special_skill_2_name=special_skill_2_name,
        special_skill_2_level=special_skill_2_level,
        special_skill_2_stack=special_skill_2_stack,
    )
    config = MultiSkillConfig(
        selected_skill=selected_skill,
        top_n=3,
        crit_mode="expected" if use_expected_crit else "non_crit",
    )
    count_desc = tr("desktop.endfield.previewDefaultCounts", skill=selected_skill)
    if use_manual_counts:
        counts = normalize_manual_segment_counts(manual_counts or {}, scenarios)
        if all(v == 0 for v in counts.values()):
            return [
                tr("desktop.endfield.modeMultiSkillPreview"),
                tr("desktop.endfield.previewManualCountsZero"),
            ]
        active_counts = {k: v for k, v in counts.items() if v > 0}
        config = MultiSkillConfig(
            selected_skill=selected_skill,
            top_n=3,
            skill_counts=active_counts,
            crit_mode="expected" if use_expected_crit else "non_crit",
        )
        from games.endfield.calc.skills.segments import format_segment_count_label

        count_desc = tr(
            "desktop.endfield.previewManualCounts",
            label=format_segment_count_label(active_counts),
        )

    from games.endfield.calc.damage.types import format_damage_type_display

    segment_type_lines = []
    for scenario in scenarios:
        type_display = format_damage_type_display(
            scenario.damage_type or "物理",
            is_default=not scenario.damage_type_explicit,
        )
        segment_type_lines.append(f"  {scenario.scenario_key}: {type_display}")

    result = optimize_multi_skill_loadouts(
        base_context=DamageContext(
            **resolved_enemy.damage_context_fields(
                crit_rate=crit_rate,
                crit_damage=crit_damage,
            )
        ),
        weapons=[
            WeaponCandidate(
                name=str(weapon_data.get("名称", tr("desktop.endfield.previewCurrentWeapon"))),
                final_attack=float(final["final_attack"]),
            )
        ],
        equipment_catalog=sampled_catalog,
        scenarios=scenarios,
        config=config,
        character=char_data,
    )
    lines = [
        tr("desktop.endfield.modeMultiSkillPreview"),
        tr(
            "desktop.endfield.previewEquipmentScope",
            scope=preview_equipment_scope_label or tr("desktop.endfield.previewAllEquipment"),
        ),
        tr("desktop.endfield.previewComboCount", n=result.total_combinations),
        count_desc,
        tr("desktop.endfield.previewSegmentDamageTypes"),
        *segment_type_lines,
        tr("desktop.endfield.previewSampleNote"),
    ]
    mode_text = {
        "skill_only": tr("desktop.endfield.previewModeSkillOnly"),
        "abnormal_only": tr("desktop.endfield.previewModeAbnormalOnly"),
        "skill_and_abnormal": tr("desktop.endfield.previewModeSkillAndAbnormal"),
    }.get(damage_component_mode, tr("desktop.endfield.previewModeSkillAndAbnormal"))
    crit_text = tr("desktop.endfield.previewCritOn") if use_expected_crit else tr("desktop.endfield.previewCritOff")
    lines.append(tr("desktop.endfield.previewCaliber", mode=mode_text, crit=crit_text))
    if use_manual_counts and resolved_enemy.break_defense_stacks > 0:
        note = format_break_defense_rotation_note(
            resolved_enemy.break_defense_stacks,
            normalize_manual_segment_counts(manual_counts or {}, scenarios),
        )
        if note:
            lines.append(note)
    physical_total, physical_breakdown = evaluate_physical_abnormal_total(
        context=DamageContext(
            **resolved_enemy.damage_context_fields(
                final_attack=float(final["final_attack"]),
                skill_multiplier=1.0,
                damage_type="物理",
                skill_type="异常",
                crit_rate=crit_rate,
                crit_damage=crit_damage,
            )
        ),
        crit_mode="expected" if use_expected_crit else "non_crit",  # type: ignore[arg-type]
        effects=[],
        counts=physical_abnormal_counts or {},
        char_level=char_level,
        **resolved_enemy.abnormal_eval_kwargs(),  # type: ignore[arg-type]
    )
    spell_total, spell_breakdown = evaluate_spell_abnormal_total(
        context=DamageContext(
            **resolved_enemy.damage_context_fields(
                final_attack=float(final["final_attack"]),
                skill_multiplier=1.0,
                damage_type="法术-灼热",
                skill_type="异常",
                crit_rate=crit_rate,
                crit_damage=crit_damage,
            )
        ),
        crit_mode="expected" if use_expected_crit else "non_crit",  # type: ignore[arg-type]
        effects=[],
        counts=spell_abnormal_counts or {},
        char_level=char_level,
        **resolved_enemy.abnormal_eval_kwargs(),  # type: ignore[arg-type]
    )
    abnormal_total = physical_total + spell_total
    if abnormal_total > 0:
        lines.append(tr("desktop.endfield.previewAbnormalEstimateTotal", damage=f"{abnormal_total:.1f}"))
        lines.extend(format_abnormal_breakdown_lines(physical_breakdown, physical_abnormal_counts, indent="  "))
        lines.extend(format_spell_abnormal_breakdown_lines(spell_breakdown, spell_abnormal_counts, indent="  "))
    if warning:
        lines.append(tr("desktop.endfield.previewHint", warning=warning))
    for idx, score in enumerate(result.top_results, start=1):
        breakdown_lines = format_segment_breakdown_lines(
            score.skill_breakdown,
            result.skill_count_map,
            indent="  ",
        )
        lines.append(
            tr(
                "desktop.endfield.previewRankMultiSkill",
                idx=idx,
                damage=f"{score.weighted_total_damage:.1f}",
            )
        )
        if abnormal_total > 0:
            merged = compose_damage_total(
                skill_damage=score.weighted_total_damage,
                abnormal_damage=abnormal_total,
                mode=damage_component_mode,
            )
            lines.append(
                tr(
                    "desktop.endfield.previewRankSkillAbnormalMergeMulti",
                    skill=f"{score.weighted_total_damage:.1f}",
                    abnormal=f"{abnormal_total:.1f}",
                    merged=f"{merged:.1f}",
                )
            )
        lines.extend(breakdown_lines)
    if not result.top_results:
        lines.append(tr("desktop.endfield.previewNoResults"))
    """build multi skill search preview lines impl。"""
    return lines
