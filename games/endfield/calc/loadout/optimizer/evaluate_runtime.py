# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""配装评估的运行时快照与缓存。

从 ``evaluate.py`` 拆出（P2-07），负责装备/最终攻击力缓存、单线程模式开关
以及 ``build_runtime_eval_snapshot``。``evaluate`` 继续再导出这些符号，
``task_batch`` 与 ``store`` 的既有导入路径不变。
"""

from __future__ import annotations

import logging
import threading
from collections import OrderedDict
from typing import Any

from games.endfield.calc.damage.originium_arts import sum_originium_arts_strength
from games.endfield.calc.equipment.affix import aggregate_loadout_modifiers
from games.endfield.calc.equipment.system import build_four_slot_loadout
from games.endfield.calc.loadout.attack_eval import final_attack_details_for_loadout
from games.endfield.calc.search.evaluate.context import SearchEvalContext

from .types import RuntimeEvalSnapshot, WeaponCandidate

__all__ = [
    "build_runtime_eval_snapshot",
    "set_single_thread_mode",
    "warmup_final_attack_cache",
]

logger = logging.getLogger(__name__)

# ── 装备侧效果缓存（键=四件装备名元组，同一配装不同武器时复用） ──
_loadout_cache: OrderedDict[tuple[str, str, str, str], tuple[list, dict[str, float], float]] = OrderedDict()
_loadout_cache_lock = threading.Lock()
_MAX_LOADOUT_CACHE = 500000  # 增大到 50 万，覆盖所有装备组合

# ── 最终攻击力缓存（键=(武器名, 四件装备名)，避免重复计算 final_attack） ──
_final_attack_cache: OrderedDict[tuple[str, str, str, str, str], float] = OrderedDict()
_MAX_ATTACK_CACHE = 2000000  # 增大到 200 万，覆盖所有组合
_attack_cache_hits = 0
_attack_cache_misses = 0

# ── 单线程模式标志（跳过锁开销） ──
_single_thread_mode = False


def set_single_thread_mode(enabled: bool) -> None:
    """设置单线程模式（跳过锁开销）。"""
    global _single_thread_mode
    _single_thread_mode = enabled
    logger.info("单线程模式: %s", enabled)


def warmup_final_attack_cache(
    *,
    weapons: list[WeaponCandidate],
    equipment_catalog: dict[str, list[dict[str, Any]]],
    search_eval: SearchEvalContext | None = None,
) -> int:
    """预热 final_attack 缓存，消除搜索时的缓存预热开销。

    遍历所有武器+装备组合，预先计算 final_attack 并存入缓存。

    Args:
        weapons: 武器候选列表
        equipment_catalog: 装备目录（按部位分组）
        search_eval: 搜索评估上下文

    Returns:
        预热的缓存条目数
    """
    if search_eval is None:
        return 0

    # 获取装备列表
    chest_list = equipment_catalog.get("chest", [])
    gloves_list = equipment_catalog.get("gloves", [])
    acc_a_list = equipment_catalog.get("accessory_a", [])
    acc_b_list = equipment_catalog.get("accessory_b", [])

    if not chest_list or not gloves_list:
        return 0

    # 限制预热数量（避免内存爆炸）
    max_chest = min(len(chest_list), 50)
    max_gloves = min(len(gloves_list), 50)
    max_acc_a = min(len(acc_a_list), 10)
    max_acc_b = min(len(acc_b_list), 10)

    warmed = 0
    for weapon in weapons:
        weapon_data = search_eval.weapon_data_by_name.get(weapon.name)
        if weapon_data is None:
            continue

        for chest in chest_list[:max_chest]:
            for glove in gloves_list[:max_gloves]:
                for acc_a in acc_a_list[:max_acc_a]:
                    for acc_b in acc_b_list[:max_acc_b]:
                        try:
                            # 构建装备组合
                            loadout = build_four_slot_loadout(
                                chest=chest,
                                gloves=glove,
                                accessory_a=acc_a,
                                accessory_b=acc_b,
                                allow_duplicate_accessory=True,
                            )
                            _, flat_stats, atk_percent = aggregate_loadout_modifiers(loadout)

                            # 计算 final_attack
                            _ckey = (
                                chest.get("名称", ""),
                                glove.get("名称", ""),
                                acc_a.get("名称", ""),
                                acc_b.get("名称", ""),
                            )
                            _akey = (weapon.name, _ckey[0], _ckey[1], _ckey[2], _ckey[3])

                            if _akey not in _final_attack_cache:
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
                                _final_attack_cache[_akey] = float(details["final_attack"])
                                warmed += 1
                        except (ValueError, KeyError, TypeError):
                            # 跳过无效的装备组合
                            continue

    return warmed


def build_runtime_eval_snapshot(
    *,
    task: tuple[WeaponCandidate, tuple[dict, dict, dict, dict]],
    search_eval: SearchEvalContext | None = None,
) -> RuntimeEvalSnapshot:
    """将一条任务解析为可复用的运行时快照。

    解析流程：
    1. 从任务中提取武器和四格配装
    2. 构建四格配装运行时结构
    3. 聚合装备词条和套装效果 → DamageEffect + 平铺四维 + 攻击力%
    4. 若提供了 search_eval，按当前等级曲线重算最终攻击力
    5. 返回运行时快照

    Args:
        task: 搜索任务（武器候选 + 四格配装）
        search_eval: 搜索评估上下文（用于全量搜索）

    Returns:
        RuntimeEvalSnapshot 对象
    """
    weapon, (chest, glove, acc_a, acc_b) = task
    # 装备侧聚合结果缓存（同一配装不同武器复用，避免重复笛卡尔积级 build+aggregate）
    _ckey = (chest.get("名称", ""), glove.get("名称", ""), acc_a.get("名称", ""), acc_b.get("名称", ""))
    # 单线程模式跳过锁开销
    if _single_thread_mode:
        cached = _loadout_cache.get(_ckey)
        if cached is not None:
            equip_effects, flat_stats, atk_percent = cached
        else:
            loadout = build_four_slot_loadout(
                chest=chest,
                gloves=glove,
                accessory_a=acc_a,
                accessory_b=acc_b,
                allow_duplicate_accessory=True,
            )
            equip_effects, flat_stats, atk_percent = aggregate_loadout_modifiers(loadout)
            if len(_loadout_cache) >= _MAX_LOADOUT_CACHE:
                _loadout_cache.popitem(last=False)
            _loadout_cache[_ckey] = (equip_effects, flat_stats, atk_percent)
    else:
        with _loadout_cache_lock:
            cached = _loadout_cache.get(_ckey)
            if cached is not None:
                equip_effects, flat_stats, atk_percent = cached
            else:
                loadout = build_four_slot_loadout(
                    chest=chest,
                    gloves=glove,
                    accessory_a=acc_a,
                    accessory_b=acc_b,
                    allow_duplicate_accessory=True,
                )
                equip_effects, flat_stats, atk_percent = aggregate_loadout_modifiers(loadout)
                if len(_loadout_cache) >= _MAX_LOADOUT_CACHE:
                    _loadout_cache.popitem(last=False)
                _loadout_cache[_ckey] = (equip_effects, flat_stats, atk_percent)
    effects = list(weapon.effects) + equip_effects
    final_attack = weapon.final_attack
    # 全量搜索时按当前等级曲线重算 final_attack（含装备平铺与攻击%）
    if search_eval is not None:
        global _attack_cache_hits, _attack_cache_misses
        # 检查 final_attack 缓存（键=武器名+四件装备名）
        _akey = (weapon.name, _ckey[0], _ckey[1], _ckey[2], _ckey[3])
        cached_attack = _final_attack_cache.get(_akey)
        if cached_attack is not None:
            final_attack = cached_attack
            _attack_cache_hits += 1
        else:
            _attack_cache_misses += 1
            weapon_data = search_eval.weapon_data_by_name.get(weapon.name)
            if weapon_data is not None:
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
                final_attack = float(details["final_attack"])
                # 缓存结果
                if len(_final_attack_cache) >= _MAX_ATTACK_CACHE:
                    _final_attack_cache.popitem(last=False)
                _final_attack_cache[_akey] = final_attack
        # 每 10000 次输出缓存命中率
        total = _attack_cache_hits + _attack_cache_misses
        if total > 0 and total % 10000 == 0:
            hit_rate = _attack_cache_hits / total * 100
            logger.info("final_attack 缓存命中率: %.1f%% (%d/%d)", hit_rate, _attack_cache_hits, total)
    return RuntimeEvalSnapshot(
        weapon_name=weapon.name,
        final_attack=final_attack,
        effects=tuple(effects),
        loadout_names={
            "chest": chest.get("名称", ""),
            "gloves": glove.get("名称", ""),
            "accessory_a": acc_a.get("名称", ""),
            "accessory_b": acc_b.get("名称", ""),
        },
        originium_arts_strength=sum_originium_arts_strength(flat_stats),
    )
