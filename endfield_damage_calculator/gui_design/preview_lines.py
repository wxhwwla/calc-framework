#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""单/多技能遍历快速预览文案（纯函数，无 CTk）。"""

from __future__ import annotations

from typing import Any, Dict, Optional

from calculation.damage_engine import DamageContext
from calculation.loadout_optimizer import (
    OptimizerConfig,
    WeaponCandidate,
    search_best_single_skill_loadouts,
)
from calculation.multi_skill_optimizer import (
    MultiSkillConfig,
    SkillScenario,
    optimize_multi_skill_loadouts,
)
from calculation.multi_skill_search_eval import build_skill_scenarios_from_levels
from calculation.multiplicative_zones.final_attack_zone import calculate_final_attack_with_details
from data.equipment_catalog import (
    catalog_preview_status_lines,
    get_equipment_catalog,
    sample_equipment_catalog,
)
from calculation.preview_cache import cached_preview, sync_preview_dependencies


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
    preview_weapon_candidates: Optional[list[WeaponCandidate]] = None,
    preview_scope_label: str = "",
    preview_equipment_catalog: Optional[Dict[str, list[dict]]] = None,
    preview_equipment_scope_label: str = "",
    enemy_defense: float = 100.0,
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
            preview_weapon_candidates=preview_weapon_candidates,
            preview_scope_label=preview_scope_label,
            preview_equipment_catalog=preview_equipment_catalog,
            preview_equipment_scope_label=preview_equipment_scope_label,
            enemy_defense=enemy_defense,
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
    preview_weapon_candidates: Optional[list[WeaponCandidate]] = None,
    preview_scope_label: str = "",
    preview_equipment_catalog: Optional[Dict[str, list[dict]]] = None,
    preview_equipment_scope_label: str = "",
    enemy_defense: float = 100.0,
) -> list[str]:
    if preview_equipment_catalog is None:
        catalog = get_equipment_catalog(scope_label=preview_equipment_scope_label or "全部装备")
    else:
        catalog = preview_equipment_catalog
    blocked = catalog_preview_status_lines(
        catalog, mode_label="单技能遍历(快速预览)"
    )
    if blocked:
        return blocked
    sampled_catalog = sample_equipment_catalog(catalog, per_slot=2)
    from gui_design.display_lines import resolve_selected_skill_for_damage

    skill_label, skill_multiplier, skill_warning = resolve_selected_skill_for_damage(
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
            skill_multiplier=skill_multiplier,
            skill_type=skill_label.split()[0],
            enemy_defense=enemy_defense,
        ),
        weapons=candidates,
        equipment_catalog=sampled_catalog,
        config=OptimizerConfig(
            top_n=3,
            warn_on_unfiltered=False,
            prune_non_beneficial=False,
        ),
    )
    lines = [
        "计算模式: 单技能遍历(快速预览)",
        f"技能: {skill_label}",
        f"候选范围: {preview_scope_label or '当前武器'}",
        f"装备范围: {preview_equipment_scope_label or '全部装备'}",
        f"预览组合数: {result.total_combinations}",
        "说明: 当前仅采样每个部位前2件装备；全量遍历请点武器区「全量遍历(弹窗结果)」。",
    ]
    if skill_warning:
        lines.append(f"提示: {skill_warning}")
    for idx, score in enumerate(result.top_results, start=1):
        loadout = score.loadout_names
        lines.append(
            f"Top{idx}: 武器:{score.weapon_name} 伤害 {score.final_damage:.1f} | "
            f"护甲:{loadout['chest']} 护手:{loadout['gloves']} "
            f"配件A:{loadout['accessory_a']} 配件B:{loadout['accessory_b']}"
        )
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
    manual_counts: Optional[Dict[str, int]] = None,
    use_manual_counts: bool = False,
    preview_equipment_catalog: Optional[Dict[str, list[dict]]] = None,
    preview_equipment_scope_label: str = "",
    enemy_defense: float = 100.0,
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
            manual_counts=manual_counts,
            use_manual_counts=use_manual_counts,
            preview_equipment_catalog=preview_equipment_catalog,
            preview_equipment_scope_label=preview_equipment_scope_label,
            enemy_defense=enemy_defense,
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
    manual_counts: Optional[Dict[str, int]] = None,
    use_manual_counts: bool = False,
    preview_equipment_catalog: Optional[Dict[str, list[dict]]] = None,
    preview_equipment_scope_label: str = "",
    enemy_defense: float = 100.0,
) -> list[str]:
    if preview_equipment_catalog is None:
        catalog = get_equipment_catalog(scope_label=preview_equipment_scope_label or "全部装备")
    else:
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
        selected_skill = scenarios[0].skill_name
        warning = ""
    final = calculate_final_attack_with_details(
        character=char_data,
        weapon=weapon_data,
        char_level=char_level,
        weapon_level=weapon_level,
        trust_level=trust_level,
    )
    config = MultiSkillConfig(
        selected_skill=selected_skill,
        top_n=3,
    )
    count_desc = f"默认次数: 当前选中技能 {selected_skill}×1，其它×0"
    if use_manual_counts:
        counts = {
            "战技": int((manual_counts or {}).get("战技", 0)),
            "连携技": int((manual_counts or {}).get("连携技", 0)),
            "终结技": int((manual_counts or {}).get("终结技", 0)),
        }
        if all(v == 0 for v in counts.values()):
            return [
                "计算模式: 多技能遍历(快速预览)",
                "手动次数不能全为0，请至少设置一项 > 0。",
            ]
        config = MultiSkillConfig(
            selected_skill=selected_skill,
            top_n=3,
            skill_counts=counts,
        )
        count_desc = (
            "手动次数: "
            f"战技×{counts['战技']}, 连携技×{counts['连携技']}, 终结技×{counts['终结技']}"
        )

    result = optimize_multi_skill_loadouts(
        base_context=DamageContext(
            final_attack=0.0,
            skill_multiplier=1.0,
            enemy_defense=enemy_defense,
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
        "说明: 当前仅采样每个部位前2件装备；全量遍历请点武器区「全量遍历(弹窗结果)」。",
    ]
    if warning:
        lines.append(f"提示: {warning}")
    for idx, score in enumerate(result.top_results, start=1):
        breakdown_text = " / ".join(
            [f"{name}:{value:.1f}" for name, value in score.skill_breakdown.items()]
        )
        lines.append(
            f"Top{idx}: 总伤 {score.weighted_total_damage:.1f} | {breakdown_text}"
        )
    if not result.top_results:
        lines.append("无可用结果，请检查装备数据。")
    return lines
