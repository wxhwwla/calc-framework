# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""Rust 全批量评估集成。

使用 Rust 全批量函数替代 Python 逐任务评估。
"""

from __future__ import annotations

from typing import Any

from games.endfield.calc.loadout.optimizer import LoadoutScore


def evaluate_full_batch_rust(
    weapons: list[Any],
    equipment_catalog: dict[str, list[dict[str, Any]]],
    char_data: dict[str, Any],
    char_level: int,
    base_context: Any,
    top_n: int = 10,
) -> list[LoadoutScore]:
    """使用 Rust 全批量函数评估所有配装组合。

    Args:
        weapons: 武器候选列表
        equipment_catalog: 装备目录（按部位分组）
        char_data: 角色数据字典
        char_level: 角色等级
        base_context: 基础伤害上下文
        top_n: 返回前 N 个结果

    Returns:
        LoadoutScore 列表，按伤害降序排列
    """
    from extensions.rust_search.python.rust_bridge import evaluate_full_batch

    # 预处理武器数据
    weapon_names = []
    weapon_final_attacks = []
    weapon_effects = []
    for weapon in weapons:
        weapon_names.append(weapon.name)
        weapon_final_attacks.append(weapon.final_attack)
        effects = [(eff.effect_type, float(eff.value)) for eff in weapon.effects]
        weapon_effects.append(effects)

    # 预处理装备组合
    from games.endfield.calc.equipment.affix import aggregate_loadout_modifiers
    from games.endfield.calc.equipment.system import build_four_slot_loadout

    chest_list = equipment_catalog.get("chest", [])
    gloves_list = equipment_catalog.get("gloves", [])
    acc_list = equipment_catalog.get("accessories", [])

    from utils.search_diagnostics import get_search_logger

    slog = get_search_logger()
    slog.info("装备目录: chest=%d, gloves=%d, acc=%d", len(chest_list), len(gloves_list), len(acc_list))

    if not chest_list or not gloves_list:
        slog.warning("装备目录为空，跳过 Rust 全批量评估")
        return []

    equipment_chest_names = []
    equipment_gloves_names = []
    equipment_acc_a_names = []
    equipment_acc_b_names = []
    equipment_effects = []
    equipment_flat_stats = []
    equipment_atk_percents = []

    for chest in chest_list:
        for glove in gloves_list:
            for acc_a in acc_list:
                for acc_b in acc_list:
                    try:
                        loadout = build_four_slot_loadout(
                            chest=chest,
                            gloves=glove,
                            accessory_a=acc_a,
                            accessory_b=acc_b,
                            allow_duplicate_accessory=True,
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
                        # 跳过无效的装备组合
                        continue

    if not equipment_chest_names:
        slog.warning("装备组合为空，跳过 Rust 全批量评估")
        return []

    # 计算基础攻击力
    base_attack_raw = char_data.get("基础攻击", [0])
    if isinstance(base_attack_raw, list):
        base_attack = float(base_attack_raw[0]) if base_attack_raw else 0.0
    else:
        base_attack = float(base_attack_raw)

    # 添加调试日志
    slog.info(
        "Rust 全批量评估: %d 武器, %d 装备组合, 基础攻击=%.1f",
        len(weapon_names),
        len(equipment_chest_names),
        base_attack,
    )

    # 调用 Rust 全批量函数
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
    )

    slog.info("Rust evaluate_full_batch 返回 %d 个结果", len(results))
    if results:
        slog.info("第一个结果: 武器=%s, 伤害=%.2f", results[0][0], results[0][1])

    # 转换为 LoadoutScore
    scores = []
    for weapon_name, final_damage, loadout_names in results:
        scores.append(
            LoadoutScore(
                weapon_name=weapon_name,
                final_damage=final_damage,
                loadout_names=loadout_names,
            )
        )

    return scores


__all__ = ["evaluate_full_batch_rust"]
