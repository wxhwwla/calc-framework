#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""单/多技能遍历快速预览文案（纯函数，无 CTk）。"""

from __future__ import annotations

from typing import Any, Dict, Optional

from calculation.damage.engine import DamageContext
from calculation.loadout.optimizer import (
    OptimizerConfig,
    WeaponCandidate,
    search_best_single_skill_loadouts,
)
from calculation.multi_skill.optimizer import (
    MultiSkillConfig,
    SkillScenario,
    optimize_multi_skill_loadouts,
)
from calculation.search.evaluate.multi_skill import build_skill_scenarios_from_levels
from calculation.skills.segments import format_segment_breakdown_lines, normalize_manual_segment_counts
from calculation.multiplicative_zones.final_attack_zone import calculate_final_attack_with_details
from data.equipment_catalog import catalog_preview_status_lines, sample_equipment_catalog
from calculation.core.preview_cache import cached_preview, sync_preview_dependencies
from calculation.abnormal.physical import (
    compose_damage_total,
    evaluate_physical_abnormal_total,
    format_abnormal_breakdown_lines,
)
from calculation.abnormal.spell import (
    evaluate_spell_abnormal_total,
    format_spell_abnormal_breakdown_lines,
)


def build_single_skill_search_preview_lines(
    *,
    char_data: Optional[Dict[str, Any]],
    weapon_data: Optional[Dict[str, Any]],
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
    preview_weapon_candidates: Optional[list[WeaponCandidate]] = None,
    preview_scope_label: str = "",
    preview_equipment_catalog: Optional[Dict[str, list[dict]]] = None,
    preview_equipment_scope_label: str = "",
    enemy_defense: float = 100.0,
    physical_abnormal_counts: Optional[Dict[str, int]] = None,
    spell_abnormal_counts: Optional[Dict[str, int]] = None,
    damage_component_mode: str = "skill_and_abnormal",
    use_expected_crit: bool = False,
    extra_crit_rate: float = 0.0,
    extra_crit_damage: float = 0.0,
) -> list[str]:
    """构建单技能遍历模式的快速预览文案（带缓存）。"""
    if not char_data or not weapon_data:
        return ["请选择有效角色和武器"]

    sync_preview_dependencies(
        char_name=char_data.get("名称", ""),
        weapon_name=weapon_data.get("名称", ""),
        char_level=char_level,
        weapon_level=weapon_level,
        trust_level=trust_level,
        skill_1=skill_1_level,
        skill_2=skill_2_level,
        skill_3=skill_3_level,
        calculation_mode="single_skill_search_preview",
        weapon_scope=preview_scope_label,
        equipment_scope=preview_equipment_scope_label,
        enemy_defense=enemy_defense,
        preview_weapon_names=tuple(
            c.name for c in (preview_weapon_candidates or [])
        ),
        custom_equipment_catalog=preview_equipment_catalog is not None,
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
        return _build_single_skill_search_preview_lines_impl(
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
            preview_weapon_candidates=preview_weapon_candidates,
            preview_scope_label=preview_scope_label,
            preview_equipment_catalog=preview_equipment_catalog,
            preview_equipment_scope_label=preview_equipment_scope_label,
            enemy_defense=enemy_defense,
            physical_abnormal_counts=physical_abnormal_counts,
            spell_abnormal_counts=spell_abnormal_counts,
            damage_component_mode=damage_component_mode,
            use_expected_crit=use_expected_crit,
            extra_crit_rate=extra_crit_rate,
            extra_crit_damage=extra_crit_damage,
        )

    lines, _ = cached_preview("single_skill_search_preview", _compute)
    return lines


def _build_single_skill_search_preview_lines_impl(
    *,
    char_data: Dict[str, Any],
    weapon_data: Dict[str, Any],
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
    preview_weapon_candidates: Optional[list[WeaponCandidate]] = None,
    preview_scope_label: str = "",
    preview_equipment_catalog: Optional[Dict[str, list[dict]]] = None,
    preview_equipment_scope_label: str = "",
    enemy_defense: float = 100.0,
    physical_abnormal_counts: Optional[Dict[str, int]] = None,
    spell_abnormal_counts: Optional[Dict[str, int]] = None,
    damage_component_mode: str = "skill_and_abnormal",
    use_expected_crit: bool = False,
    extra_crit_rate: float = 0.0,
    extra_crit_damage: float = 0.0,
) -> list[str]:
    if not preview_equipment_catalog:
        return [
            "计算模式: 单技能遍历(快速预览)",
            "错误: 未提供装备 catalog，请通过 GameDataFacade 传入后再预览。",
        ]
    catalog = preview_equipment_catalog
    blocked = catalog_preview_status_lines(
        catalog, mode_label="单技能遍历(快速预览)"
    )
    if blocked:
        return blocked
    sampled_catalog = sample_equipment_catalog(catalog, per_slot=2)
    from gui_design.presentation.display_lines import resolve_selected_skill_for_damage

    skill = resolve_selected_skill_for_damage(
        char_data,
        skill_1_level=skill_1_level,
        skill_2_level=skill_2_level,
        skill_3_level=skill_3_level,
    )
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
    candidates = preview_weapon_candidates or [
        WeaponCandidate(
            name=str(weapon_data.get("名称", "当前武器")),
            final_attack=float(final["final_attack"]),
        )
    ]
    result = search_best_single_skill_loadouts(
        base_context=DamageContext(
            final_attack=0.0,
            skill_multiplier=skill.multiplier,
            damage_type=skill.damage_type,
            skill_type=skill.skill_type,
            enemy_defense=enemy_defense,
            crit_rate=0.05 + float(extra_crit_rate),
            crit_damage=0.5 + float(extra_crit_damage),
        ),
        weapons=candidates,
        equipment_catalog=sampled_catalog,
        config=OptimizerConfig(
            top_n=3,
            crit_mode="expected" if use_expected_crit else "non_crit",  # type: ignore[arg-type]
            warn_on_unfiltered=False,
            prune_non_beneficial=False,
        ),
    )
    lines = [
        "计算模式: 单技能遍历(快速预览)",
        f"技能: {skill.label}",
        f"伤害类型: {skill.damage_type_display}",
        f"候选范围: {preview_scope_label or '当前武器'}",
        f"装备范围: {preview_equipment_scope_label or '全部装备'}",
        f"预览组合数: {result.total_combinations}",
        "说明: 当前仅采样每个部位前2件装备；全量遍历请点武器区「全量遍历(弹窗结果)」。",
    ]
    mode_text = {
        "skill_only": "仅技能",
        "abnormal_only": "仅异常",
        "skill_and_abnormal": "技能+异常",
    }.get(damage_component_mode, "技能+异常")
    lines.append(f"口径: {mode_text} | 期望伤害: {'开' if use_expected_crit else '关'}")
    physical_total, physical_breakdown = evaluate_physical_abnormal_total(
        context=DamageContext(
            final_attack=float(final["final_attack"]),
            skill_multiplier=1.0,
            damage_type="物理",
            skill_type="异常",
            enemy_defense=enemy_defense,
            crit_rate=0.05 + float(extra_crit_rate),
            crit_damage=0.5 + float(extra_crit_damage),
        ),
        crit_mode="expected" if use_expected_crit else "non_crit",  # type: ignore[arg-type]
        effects=[],
        counts=physical_abnormal_counts or {},
        char_level=char_level,
    )
    spell_total, spell_breakdown = evaluate_spell_abnormal_total(
        context=DamageContext(
            final_attack=float(final["final_attack"]),
            skill_multiplier=1.0,
            damage_type="法术-灼热",
            skill_type="异常",
            enemy_defense=enemy_defense,
            crit_rate=0.05 + float(extra_crit_rate),
            crit_damage=0.5 + float(extra_crit_damage),
        ),
        crit_mode="expected" if use_expected_crit else "non_crit",  # type: ignore[arg-type]
        effects=[],
        counts=spell_abnormal_counts or {},
        char_level=char_level,
    )
    abnormal_total = physical_total + spell_total
    if abnormal_total > 0:
        lines.append(f"当前武器异常估算总伤: {abnormal_total:.1f}")
        lines.extend(format_abnormal_breakdown_lines(physical_breakdown, physical_abnormal_counts, indent="  "))
        lines.extend(format_spell_abnormal_breakdown_lines(spell_breakdown, spell_abnormal_counts, indent="  "))
    if skill.warning:
        lines.append(f"提示: {skill.warning}")
    for idx, score in enumerate(result.top_results, start=1):
        loadout = score.loadout_names
        lines.append(
            f"Top{idx}: 武器:{score.weapon_name} 伤害 {score.final_damage:.1f} | "
            f"护甲:{loadout['chest']} 护手:{loadout['gloves']} "
            f"配件A:{loadout['accessory_a']} 配件B:{loadout['accessory_b']}"
        )
        if abnormal_total > 0:
            merged = compose_damage_total(
                skill_damage=score.final_damage,
                abnormal_damage=abnormal_total,
                mode=damage_component_mode,
            )
            lines.append(f"      技能 {score.final_damage:.1f} | 异常 {abnormal_total:.1f} | 合计 {merged:.1f}")
    if not result.top_results:
        lines.append("无可用结果，请检查装备数据。")
    return lines


def build_multi_skill_search_preview_lines(
    *,
    char_data: Optional[Dict[str, Any]],
    weapon_data: Optional[Dict[str, Any]],
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
    manual_counts: Optional[Dict[str, int]] = None,
    use_manual_counts: bool = False,
    preview_equipment_catalog: Optional[Dict[str, list[dict]]] = None,
    preview_equipment_scope_label: str = "",
    enemy_defense: float = 100.0,
    physical_abnormal_counts: Optional[Dict[str, int]] = None,
    spell_abnormal_counts: Optional[Dict[str, int]] = None,
    damage_component_mode: str = "skill_and_abnormal",
    use_expected_crit: bool = False,
    extra_crit_rate: float = 0.0,
    extra_crit_damage: float = 0.0,
) -> list[str]:
    """构建多技能遍历模式的快速预览文案（带缓存）。"""
    if not char_data or not weapon_data:
        return ["请选择有效角色和武器"]

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
        )

    lines, _ = cached_preview("multi_skill_search_preview", _compute)
    return lines


def _build_multi_skill_search_preview_lines_impl(
    *,
    char_data: Dict[str, Any],
    weapon_data: Dict[str, Any],
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
    manual_counts: Optional[Dict[str, int]] = None,
    use_manual_counts: bool = False,
    preview_equipment_catalog: Optional[Dict[str, list[dict]]] = None,
    preview_equipment_scope_label: str = "",
    enemy_defense: float = 100.0,
    physical_abnormal_counts: Optional[Dict[str, int]] = None,
    spell_abnormal_counts: Optional[Dict[str, int]] = None,
    damage_component_mode: str = "skill_and_abnormal",
    use_expected_crit: bool = False,
    extra_crit_rate: float = 0.0,
    extra_crit_damage: float = 0.0,
) -> list[str]:
    if not preview_equipment_catalog:
        return [
            "计算模式: 多技能遍历(快速预览)",
            "错误: 未提供装备 catalog，请通过 GameDataFacade 传入后再预览。",
        ]
    catalog = preview_equipment_catalog
    blocked = catalog_preview_status_lines(
        catalog, mode_label="多技能遍历(快速预览)"
    )
    if blocked:
        return blocked
    sampled_catalog = sample_equipment_catalog(catalog, per_slot=2)
    scenarios = build_skill_scenarios_from_levels(
        char_data,
        skill_1_level=skill_1_level,
        skill_2_level=skill_2_level,
        skill_3_level=skill_3_level,
    )
    if not scenarios:
        scenarios = [SkillScenario(skill_name="战技", skill_multiplier=1.0, skill_type="战技")]
        selected_skill = "战技"
        warning = "未选择技能等级或无可用倍率，按战技 100% 预览。"
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
    count_desc = f"默认次数: 当前选中技能 {selected_skill}×1，其它×0"
    if use_manual_counts:
        counts = normalize_manual_segment_counts(manual_counts or {}, scenarios)
        if all(v == 0 for v in counts.values()):
            return [
                "计算模式: 多技能遍历(快速预览)",
                "手动次数不能全为0，请至少设置一项 > 0。",
            ]
        active_counts = {k: v for k, v in counts.items() if v > 0}
        config = MultiSkillConfig(
            selected_skill=selected_skill,
            top_n=3,
            skill_counts=active_counts,
            crit_mode="expected" if use_expected_crit else "non_crit",
        )
        from calculation.skills.segments import format_segment_count_label

        count_desc = f"手动次数: {format_segment_count_label(active_counts)}"

    from calculation.damage.types import format_damage_type_display

    segment_type_lines = []
    for scenario in scenarios:
        type_display = format_damage_type_display(
            scenario.damage_type or "物理",
            is_default=not scenario.damage_type_explicit,
        )
        segment_type_lines.append(f"  {scenario.scenario_key}: {type_display}")

    result = optimize_multi_skill_loadouts(
        base_context=DamageContext(
            final_attack=0.0,
            skill_multiplier=1.0,
            enemy_defense=enemy_defense,
            crit_rate=0.05 + float(extra_crit_rate),
            crit_damage=0.5 + float(extra_crit_damage),
        ),
        weapons=[
            WeaponCandidate(
                name=str(weapon_data.get("名称", "当前武器")),
                final_attack=float(final["final_attack"]),
            )
        ],
        equipment_catalog=sampled_catalog,
        scenarios=scenarios,
        config=config,
        character=char_data,
    )
    lines = [
        "计算模式: 多技能遍历(快速预览)",
        f"装备范围: {preview_equipment_scope_label or '全部装备'}",
        f"预览组合数: {result.total_combinations}",
        count_desc,
        "段伤害类型:",
        *segment_type_lines,
        "说明: 当前仅采样每个部位前2件装备；全量遍历请点武器区「全量遍历(弹窗结果)」。",
    ]
    mode_text = {
        "skill_only": "仅技能",
        "abnormal_only": "仅异常",
        "skill_and_abnormal": "技能+异常",
    }.get(damage_component_mode, "技能+异常")
    lines.append(f"口径: {mode_text} | 期望伤害: {'开' if use_expected_crit else '关'}")
    physical_total, physical_breakdown = evaluate_physical_abnormal_total(
        context=DamageContext(
            final_attack=float(final["final_attack"]),
            skill_multiplier=1.0,
            damage_type="物理",
            skill_type="异常",
            enemy_defense=enemy_defense,
            crit_rate=0.05 + float(extra_crit_rate),
            crit_damage=0.5 + float(extra_crit_damage),
        ),
        crit_mode="expected" if use_expected_crit else "non_crit",  # type: ignore[arg-type]
        effects=[],
        counts=physical_abnormal_counts or {},
        char_level=char_level,
    )
    spell_total, spell_breakdown = evaluate_spell_abnormal_total(
        context=DamageContext(
            final_attack=float(final["final_attack"]),
            skill_multiplier=1.0,
            damage_type="法术-灼热",
            skill_type="异常",
            enemy_defense=enemy_defense,
            crit_rate=0.05 + float(extra_crit_rate),
            crit_damage=0.5 + float(extra_crit_damage),
        ),
        crit_mode="expected" if use_expected_crit else "non_crit",  # type: ignore[arg-type]
        effects=[],
        counts=spell_abnormal_counts or {},
        char_level=char_level,
    )
    abnormal_total = physical_total + spell_total
    if abnormal_total > 0:
        lines.append(f"当前武器异常估算总伤: {abnormal_total:.1f}")
        lines.extend(format_abnormal_breakdown_lines(physical_breakdown, physical_abnormal_counts, indent="  "))
        lines.extend(format_spell_abnormal_breakdown_lines(spell_breakdown, spell_abnormal_counts, indent="  "))
    if warning:
        lines.append(f"提示: {warning}")
    for idx, score in enumerate(result.top_results, start=1):
        breakdown_lines = format_segment_breakdown_lines(
            score.skill_breakdown,
            result.skill_count_map,
            indent="  ",
        )
        lines.append(f"Top{idx}: 总伤 {score.weighted_total_damage:.1f}")
        if abnormal_total > 0:
            merged = compose_damage_total(
                skill_damage=score.weighted_total_damage,
                abnormal_damage=abnormal_total,
                mode=damage_component_mode,
            )
            lines.append(f"  技能 {score.weighted_total_damage:.1f} | 异常 {abnormal_total:.1f} | 合计 {merged:.1f}")
        lines.extend(breakdown_lines)
    if not result.top_results:
        lines.append("无可用结果，请检查装备数据。")
    return lines
