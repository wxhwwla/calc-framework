# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""Rust 全批量评估集成。

使用 Rust 全批量函数替代 Python 逐任务评估。
将整个武器×装备组合的遍历循环移入 Rust，消除 Python 逐任务开销。
"""

from __future__ import annotations

import importlib.util
from itertools import product
from typing import Any

from utils.frozen_runtime import use_rust_full_batch
from utils.search_diagnostics import get_search_logger

from games.endfield.calc.loadout.optimizer import LoadoutScore, OptimizerConfig, WeaponCandidate
from games.endfield.calc.loadout.slot_search import (
    FixedLoadoutSelection,
    equipment_catalog_for_selection,
)
from games.endfield.calc.search.evaluate.context import SearchEvalContext
from games.endfield.calc.search.evaluate.rust_batch_data import resolve_equipment_slot_lists
from games.endfield.calc.search.plan.job import SingleSkillSearchJob


def _rust_full_batch_importable() -> bool:
    """需同时存在模块与 ``evaluate_full_batch_py``（旧版 wheel 仅有 SoA）。"""
    if importlib.util.find_spec("rust_search") is None:
        return False
    try:
        import rust_search as _rs
    except ImportError:
        return False
    return hasattr(_rs, "evaluate_full_batch_py")


def _has_active_abnormal_counts(search_eval: SearchEvalContext | None) -> bool:
    if search_eval is None:
        return False
    for counts in (search_eval.physical_abnormal_counts, search_eval.spell_abnormal_counts):
        if counts and any(int(v) > 0 for v in counts.values()):
            return True
    return False


def can_run_full_batch_search(
    *,
    search_eval: SearchEvalContext | None,
    search_job: SingleSkillSearchJob | None,
    task_evaluator: Any | None,
) -> bool:
    """是否满足启用 Rust Tier-4 全批量的前置条件（不含目录是否为空）。"""
    if not use_rust_full_batch():
        return False
    if not _rust_full_batch_importable():
        return False
    if search_eval is None:
        return False
    if task_evaluator is not None and search_job is None:
        # 自定义 evaluator 且无 search_job：无法保证语义一致
        return False
    if search_job is not None and search_job.multi_skill_eval is not None:
        return False
    # 异常次数加权仍走 SoA / 逐任务路径
    return not _has_active_abnormal_counts(search_eval)


def _precompute_final_attacks_for_batch(
    *,
    weapons: list[Any],
    equipment_flat_stats: list[dict[str, float]],
    equipment_atk_percents: list[float],
    search_eval: SearchEvalContext,
) -> list[float] | None:
    """按武器×装备顺序预计算最终攻击力；缺武器数据时返回 None（回退 SoA）。"""
    from games.endfield.calc.loadout.attack_eval import final_attack_details_for_loadout

    attacks: list[float] = []
    for weapon in weapons:
        weapon_data = search_eval.weapon_data_by_name.get(weapon.name)
        if weapon_data is None:
            return None
        for flat_stats, atk_percent in zip(equipment_flat_stats, equipment_atk_percents):
            details = final_attack_details_for_loadout(
                character=search_eval.char_data,
                weapon=weapon_data,
                char_level=search_eval.char_level,
                weapon_level=search_eval.weapon_level,
                trust_level=search_eval.trust_level,
                weapon_normal_levels=list(search_eval.weapon_normal_levels),
                weapon_special_states=list(search_eval.weapon_special_states),
                equipment_stat_bonus=flat_stats,
                equipment_attack_percent=atk_percent,
            )
            attacks.append(float(details["final_attack"]))
    return attacks


def evaluate_full_batch_rust(
    weapons: list[Any],
    equipment_catalog: dict[str, list[dict[str, Any]]],
    char_data: dict[str, Any],
    char_level: int,
    base_context: Any,
    top_n: int = 10,
    *,
    crit_mode: str = "non_crit",
    damage_pipeline: str = "normal",
    allow_duplicate_accessory: bool = True,
    search_eval: SearchEvalContext | None = None,
) -> list[LoadoutScore]:
    """使用 Rust 全批量函数评估所有配装组合。

    将武器×装备的笛卡尔积遍历完全移入 Rust，Python 侧只做数据预处理。
    提供 ``search_eval`` 时，最终攻击力走 ``final_attack_details_for_loadout`` 预计算，
    与 SoA ``evaluate_task`` 对齐。
    """
    from extensions.rust_search.python.rust_bridge import evaluate_full_batch

    from games.endfield.calc.equipment.affix import aggregate_loadout_modifiers
    from games.endfield.calc.equipment.system import build_four_slot_loadout

    weapon_names: list[str] = []
    weapon_final_attacks: list[float] = []
    weapon_effects: list[list[tuple[str, float]]] = []
    for weapon in weapons:
        weapon_names.append(weapon.name)
        weapon_final_attacks.append(weapon.final_attack)
        effects = [(eff.effect_type, float(eff.value)) for eff in weapon.effects]
        weapon_effects.append(effects)

    chest_list, gloves_list, acc_a_list, acc_b_list = resolve_equipment_slot_lists(equipment_catalog)

    slog = get_search_logger()
    slog.info(
        "装备目录: chest=%d, gloves=%d, acc_a=%d, acc_b=%d",
        len(chest_list),
        len(gloves_list),
        len(acc_a_list),
        len(acc_b_list),
    )

    if not chest_list or not gloves_list or not acc_a_list or not acc_b_list:
        slog.warning("装备目录为空，跳过 Rust 全批量评估")
        return []

    equipment_chest_names: list[str] = []
    equipment_gloves_names: list[str] = []
    equipment_acc_a_names: list[str] = []
    equipment_acc_b_names: list[str] = []
    equipment_effects: list[list[tuple[str, float]]] = []
    equipment_flat_stats: list[dict[str, float]] = []
    equipment_atk_percents: list[float] = []

    for chest, glove, acc_a, acc_b in product(chest_list, gloves_list, acc_a_list, acc_b_list):
        try:
            loadout = build_four_slot_loadout(
                chest=chest,
                gloves=glove,
                accessory_a=acc_a,
                accessory_b=acc_b,
                allow_duplicate_accessory=allow_duplicate_accessory,
            )
            equip_effects, flat_stats, atk_percent = aggregate_loadout_modifiers(loadout)

            equipment_chest_names.append(chest.get("名称", ""))
            equipment_gloves_names.append(glove.get("名称", ""))
            equipment_acc_a_names.append(acc_a.get("名称", ""))
            equipment_acc_b_names.append(acc_b.get("名称", ""))

            effects = [(eff.effect_type, float(eff.value)) for eff in equip_effects]
            equipment_effects.append(effects)
            equipment_flat_stats.append(dict(flat_stats))
            equipment_atk_percents.append(float(atk_percent))
        except (ValueError, KeyError, TypeError):
            continue

    if not equipment_chest_names:
        slog.warning("装备组合为空，跳过 Rust 全批量评估")
        return []

    precomputed: list[float] | None = None
    if search_eval is not None:
        precomputed = _precompute_final_attacks_for_batch(
            weapons=weapons,
            equipment_flat_stats=equipment_flat_stats,
            equipment_atk_percents=equipment_atk_percents,
            search_eval=search_eval,
        )
        if precomputed is None:
            slog.warning("search_eval 缺少武器数据，跳过 Rust 全批量评估")
            return []

    # 旧路径兼容：无预计算时仍传 char 基础攻给 Rust 简化公式
    base_attack_raw = char_data.get("基础攻击力", char_data.get("基础攻击", [0]))
    if isinstance(base_attack_raw, list):
        base_attack = float(base_attack_raw[0]) if base_attack_raw else 0.0
    else:
        base_attack = float(base_attack_raw)
    if precomputed is not None:
        base_attack = 0.0

    total_combos = len(weapon_names) * len(equipment_chest_names)
    slog.info(
        "Rust 全批量评估: %d 武器 × %d 装备组合 = %d 总组合, precomputed=%s, crit_mode=%s",
        len(weapon_names),
        len(equipment_chest_names),
        total_combos,
        precomputed is not None,
        crit_mode,
    )

    slog.info("调用 Rust evaluate_full_batch...")
    results = evaluate_full_batch(
        weapon_names=weapon_names,
        weapon_final_attacks=weapon_final_attacks,
        weapon_effects=weapon_effects,
        equipment_chest_names=equipment_chest_names,
        equipment_gloves_names=equipment_gloves_names,
        equipment_acc_a_names=equipment_acc_a_names,
        equipment_acc_b_names=equipment_acc_b_names,
        equipment_effects=equipment_effects,
        equipment_flat_stats=equipment_flat_stats,
        equipment_atk_percents=equipment_atk_percents,
        char_name=char_data.get("名称", ""),
        char_level=char_level,
        char_base_attack=base_attack,
        skill_multiplier=base_context.skill_multiplier,
        damage_type=base_context.damage_type,
        skill_type=base_context.skill_type,
        is_unbalanced=base_context.is_unbalanced,
        is_true_damage=base_context.is_true_damage,
        enemy_defense=base_context.enemy_defense,
        enemy_resistance=base_context.enemy_resistance,
        ignore_resistance=base_context.ignore_resistance,
        imbalance_vulnerability_coeff=base_context.imbalance_vulnerability_coeff,
        crit_rate=base_context.crit_rate,
        crit_damage=base_context.crit_damage,
        damage_type_bonus=base_context.damage_type_bonus,
        skill_type_bonus=base_context.skill_type_bonus,
        imbalance_damage_bonus=base_context.imbalance_damage_bonus,
        other_damage_bonus=base_context.other_damage_bonus,
        combo_stacks=base_context.combo_stacks,
        break_defense_stacks=base_context.break_defense_stacks,
        base_damage_bonus=base_context.base_damage_bonus,
        top_n=top_n,
        crit_mode=crit_mode,
        damage_pipeline=damage_pipeline,
        precomputed_final_attacks=precomputed,
    )

    slog.info("Rust evaluate_full_batch 返回 %d 个结果", len(results))
    if results:
        slog.info("第一个结果: 武器=%s, 伤害=%.2f", results[0][0], results[0][1])

    return [
        LoadoutScore(
            weapon_name=weapon_name,
            final_damage=final_damage,
            loadout_names=loadout_names,
        )
        for weapon_name, final_damage, loadout_names in results
    ]


def try_run_full_batch_from_plan(
    *,
    weapons: list[WeaponCandidate],
    equipment_catalog: dict[str, list[dict[str, Any]]],
    config: OptimizerConfig,
    fixed_loadout: FixedLoadoutSelection,
    base_context: Any,
    search_eval: SearchEvalContext,
    top_n: int,
    progress_callback: Any | None = None,
    cancel_token: Any | None = None,
) -> list[LoadoutScore] | None:
    """若开关开启则跑全批量；失败/空结果返回 None 以便回退 SoA。"""
    if cancel_token is not None and bool(getattr(cancel_token, "is_cancelled", False)):
        return []

    four_slot = equipment_catalog_for_selection(equipment_catalog, selection=fixed_loadout)
    if progress_callback is not None:
        progress_callback({"processed": 0, "total": 0, "phase": "full_batch"})

    try:
        scores = evaluate_full_batch_rust(
            weapons=weapons,
            equipment_catalog=four_slot,
            char_data=search_eval.char_data,
            char_level=search_eval.char_level,
            base_context=base_context,
            top_n=top_n,
            crit_mode=str(config.crit_mode),
            damage_pipeline="normal",
            allow_duplicate_accessory=config.allow_duplicate_accessory,
            search_eval=search_eval,
        )
    except Exception as exc:
        get_search_logger().warning("Rust 全批量失败，回退 SoA: %s", exc)
        return None

    if not scores:
        get_search_logger().warning("Rust 全批量返回空结果，回退 SoA")
        return None

    if progress_callback is not None:
        n_chest = max(1, len(four_slot.get("chest", [])))
        progress_callback(
            {
                "processed": len(weapons) * n_chest,
                "total": len(weapons) * n_chest,
                "phase": "full_batch_done",
            }
        )
    return scores


__all__ = [
    "can_run_full_batch_search",
    "evaluate_full_batch_rust",
    "try_run_full_batch_from_plan",
]
