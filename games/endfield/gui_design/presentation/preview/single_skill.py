#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""单/多技能遍历快速预览文案（纯函数，无 CTk）。"""

from __future__ import annotations

from typing import Any

from games.endfield.calc.core.preview_cache import cached_preview, sync_preview_dependencies
from games.endfield.calc.damage.engine import DamageContext
from games.endfield.calc.loadout.optimizer import (
    OptimizerConfig,
    WeaponCandidate,
    search_best_single_skill_loadouts,
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
from games.endfield.calc.multiplicative_zones.final_attack_zone import calculate_final_attack_with_details
from games.endfield.data_loading.equipment_catalog import catalog_preview_status_lines, sample_equipment_catalog
from games.endfield.data_loading.enemy_eval_params import EnemyEvalParams


def _resolve_enemy_eval(
    enemy_defense: float,
    enemy_eval: EnemyEvalParams | None,
) -> EnemyEvalParams:
    if enemy_eval is not None:
        return enemy_eval
    return EnemyEvalParams.from_defense_only(enemy_defense)


def build_single_skill_search_preview_lines(
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
    preview_weapon_candidates: list[WeaponCandidate] | None = None,
    preview_scope_label: str = "",
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
    """构建单技能遍历模式的快速预览文案（带缓存）。"""
    if not char_data or not weapon_data:
        return ["请选择有效角色和武器"]

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
        calculation_mode="single_skill_search_preview",
        weapon_scope=preview_scope_label,
        equipment_scope=preview_equipment_scope_label,
        enemy_defense=enemy_defense,
        enemy_eval_token=resolved_enemy.preview_cache_token(),
        preview_weapon_names=tuple(c.name for c in (preview_weapon_candidates or [])),
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
            enemy_eval=resolved_enemy,
        )

    lines, _ = cached_preview("single_skill_search_preview", _compute)
    return lines


def _build_single_skill_search_preview_lines_impl(
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
    preview_weapon_candidates: list[WeaponCandidate] | None = None,
    preview_scope_label: str = "",
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
            "计算模式: 单技能遍历(快速预览)",
            "错误: 未提供装备 catalog，请通过 GameDataFacade 传入后再预览。",
        ]
    catalog = preview_equipment_catalog
    blocked = catalog_preview_status_lines(catalog, mode_label="单技能遍历(快速预览)")
    if blocked:
        return blocked
    sampled_catalog = sample_equipment_catalog(catalog, per_slot=2)
    resolved_enemy = _resolve_enemy_eval(enemy_defense, enemy_eval)
    crit_rate = 0.05 + float(extra_crit_rate)
    crit_damage = 0.5 + float(extra_crit_damage)
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
            **resolved_enemy.damage_context_fields(
                skill_multiplier=skill.multiplier,
                damage_type=skill.damage_type,
                skill_type=skill.skill_type,
                crit_rate=crit_rate,
                crit_damage=crit_damage,
            )
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
        **resolved_enemy.abnormal_eval_kwargs(),
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
        **resolved_enemy.abnormal_eval_kwargs(),
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
            f"第{idx}名: 武器:{score.weapon_name} 伤害 {score.final_damage:.1f} | "
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
