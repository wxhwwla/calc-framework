# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""Rust 搜索加速桥接层 — 无缝替代 Python evaluate_search_damage。

用法::

    from extensions.rust_search.python.rust_bridge import evaluate_search_damage

函数签名与 ``games.endfield.calc.dag_adapter.search_evaluate.evaluate_search_damage``
完全一致，可直接替换。

设计原则：
1. Python 预处理（效果过滤、manual_buffs）→ Rust 热路径（累加 + 乘区）→ 返回
2. Rust 扩展不可用时自动降级到纯 Python 版
3. 支持 ``RUST_SEARCH_FALLBACK=1`` 环境变量强制降级
"""

from __future__ import annotations

import os
import threading
from typing import Any

from games.endfield.calc.damage.break_defense import damage_effects_from_break_defense
from games.endfield.calc.damage.engine.helpers import _collect_effects
from games.endfield.calc.damage.engine.types import CritMode, DamageContext, DamageEffect

# ── Rust 扩展导入（带降级） ────────────────────────────────────────
_HAS_RUST = False
if not os.environ.get("RUST_SEARCH_FALLBACK"):
    try:
        import rust_search as _rs

        _HAS_RUST = True
    except ImportError:
        pass

_rust_call_lock = threading.Lock()

# ── 效果类型 → 整数 ID 映射（与 effect_id.rs 一致） ─────────────
_EFFECT_ID_MAP: dict[str, int] = {
    "伤害减免": 0,
    "增幅": 1,
    "虚弱": 2,
    "庇护": 3,
    "脆弱": 4,
    "易伤": 5,
    "连击增伤": 6,
    "伤害类型伤害加成": 7,
    "技能类型伤害加成": 7,
    "失衡伤害加成": 7,
    "其他伤害加成": 7,
    "无视抗性": 8,
    "抗性": 9,
    "防御": 10,
    "失衡易伤系数": 11,
    "非主控减伤": 12,
    "特殊乘区": 13,
}

# ── 技能类型 → 整数 ID ─────────────────────────────────────────
_SKILL_TYPE_ID_MAP: dict[str, int] = {
    "终结技": 1,
}

# ── 暴击模式 → 整数 ID ─────────────────────────────────────────
_CRIT_MODE_ID_MAP: dict[str, int] = {
    "always_crit": 1,
    "expected": 2,
}

# ── 手动 buff 字段映射（与 search_evaluate.py 一致） ──────────────
_CONTEXT_BUFF_MAP: dict[str, str] = {
    "暴击率": "crit_rate",
    "暴击伤害": "crit_damage",
    "伤害类型加成": "damage_type_bonus",
    "技能类型加成": "skill_type_bonus",
    "失衡伤害加成": "imbalance_damage_bonus",
    "其他伤害加成": "other_damage_bonus",
}


def _apply_manual_buffs(
    *,
    manual_buffs: list[dict[str, str | float]] | None = None,
    crit_rate: float = 0.05,
    crit_damage: float = 0.5,
    damage_type_bonus: float = 0.0,
    skill_type_bonus: float = 0.0,
    imbalance_damage_bonus: float = 0.0,
    other_damage_bonus: float = 0.0,
) -> tuple[dict[str, float], list[DamageEffect]]:
    """处理 manual_buffs → (字段覆盖, 额外效果列表)。"""
    overrides: dict[str, float] = {}
    extra_effects: list[DamageEffect] = []
    for entry in manual_buffs or []:
        et = str(entry.get("effect_type", "")).strip()
        v = float(entry.get("value", 0.0))
        if not et:
            continue
        ctx_field = _CONTEXT_BUFF_MAP.get(et)
        if ctx_field:
            overrides[ctx_field] = overrides.get(ctx_field, 0.0) + v
        else:
            extra_effects.append(
                DamageEffect(
                    effect_type=et,
                    value=v,
                    source="手动buff",
                    raw_text=f"{et}+{v * 100:.0f}%",
                )
            )
    result = {
        "crit_rate": crit_rate + overrides.get("crit_rate", 0.0),
        "crit_damage": crit_damage + overrides.get("crit_damage", 0.0),
        "damage_type_bonus": damage_type_bonus + overrides.get("damage_type_bonus", 0.0),
        "skill_type_bonus": skill_type_bonus + overrides.get("skill_type_bonus", 0.0),
        "imbalance_damage_bonus": imbalance_damage_bonus + overrides.get("imbalance_damage_bonus", 0.0),
        "other_damage_bonus": other_damage_bonus + overrides.get("other_damage_bonus", 0.0),
    }
    return result, extra_effects


def evaluate_search_damage(
    *,
    final_attack: float,
    skill_multiplier: float,
    damage_type: str,
    skill_type: str,
    is_unbalanced: bool = False,
    is_true_damage: bool = False,
    enemy_defense: float = 100.0,
    enemy_resistance: float = 0.0,
    ignore_resistance: float = 0.0,
    imbalance_vulnerability_coeff: float = 1.3,
    crit_rate: float = 0.05,
    crit_damage: float = 0.5,
    damage_type_bonus: float = 0.0,
    skill_type_bonus: float = 0.0,
    imbalance_damage_bonus: float = 0.0,
    other_damage_bonus: float = 0.0,
    combo_stacks: int = 0,
    break_defense_stacks: int = 0,
    base_damage_bonus: float = 0.0,
    effects: list[DamageEffect] | None = None,
    crit_mode: CritMode = "non_crit",
    manual_buffs: list[dict[str, str | float]] | None = None,
    damage_pipeline: str = "normal",
) -> Any:
    """Rust 加速版的 evaluate_search_damage。

    参数与 Python 版 ``search_evaluate.evaluate_search_damage`` 完全一致。
    Rust 扩展不可用时自动使用 Python 版。
    """
    if not _HAS_RUST:
        from games.endfield.calc.dag_adapter.search_evaluate import (
            evaluate_search_damage as _py_eval,
        )

        return _py_eval(
            final_attack=final_attack,
            skill_multiplier=skill_multiplier,
            damage_type=damage_type,
            skill_type=skill_type,
            is_unbalanced=is_unbalanced,
            is_true_damage=is_true_damage,
            enemy_defense=enemy_defense,
            enemy_resistance=enemy_resistance,
            ignore_resistance=ignore_resistance,
            imbalance_vulnerability_coeff=imbalance_vulnerability_coeff,
            crit_rate=crit_rate,
            crit_damage=crit_damage,
            damage_type_bonus=damage_type_bonus,
            skill_type_bonus=skill_type_bonus,
            imbalance_damage_bonus=imbalance_damage_bonus,
            other_damage_bonus=other_damage_bonus,
            combo_stacks=combo_stacks,
            break_defense_stacks=break_defense_stacks,
            base_damage_bonus=base_damage_bonus,
            effects=effects,
            crit_mode=crit_mode,
            manual_buffs=manual_buffs,
            damage_pipeline=damage_pipeline,
        )

    # ── Rust 路径：预处理 → 调用 → 返回 ──
    # 1. 处理 manual_buffs
    if manual_buffs:
        overrides, extra_effects = _apply_manual_buffs(
            manual_buffs=manual_buffs,
            crit_rate=crit_rate,
            crit_damage=crit_damage,
            damage_type_bonus=damage_type_bonus,
            skill_type_bonus=skill_type_bonus,
            imbalance_damage_bonus=imbalance_damage_bonus,
            other_damage_bonus=other_damage_bonus,
        )
        crit_rate = overrides["crit_rate"]
        crit_damage = overrides["crit_damage"]
        damage_type_bonus = overrides["damage_type_bonus"]
        skill_type_bonus = overrides["skill_type_bonus"]
        imbalance_damage_bonus = overrides["imbalance_damage_bonus"]
        other_damage_bonus = overrides["other_damage_bonus"]
    else:
        extra_effects = []

    # 2. 合并效果列表
    all_effects = list(effects or []) + extra_effects + list(damage_effects_from_break_defense(break_defense_stacks))

    # 3. 轻量过滤（只需 damage_type / skill_type / is_unbalanced）
    _ctx = DamageContext(
        final_attack=final_attack,
        skill_multiplier=skill_multiplier,
        damage_type=damage_type,
        skill_type=skill_type,
        is_unbalanced=is_unbalanced,
        is_true_damage=is_true_damage,
        enemy_defense=enemy_defense,
        enemy_resistance=enemy_resistance,
        ignore_resistance=ignore_resistance,
        imbalance_vulnerability_coeff=imbalance_vulnerability_coeff,
        crit_rate=crit_rate,
        crit_damage=crit_damage,
        damage_type_bonus=damage_type_bonus,
        skill_type_bonus=skill_type_bonus,
        imbalance_damage_bonus=imbalance_damage_bonus,
        other_damage_bonus=other_damage_bonus,
        combo_stacks=combo_stacks,
        break_defense_stacks=break_defense_stacks,
        base_damage_bonus=base_damage_bonus,
    )
    known_effects, unknown_effects, warnings = _collect_effects(_ctx, all_effects)

    # 4. 转简单元组 → Rust
    rust_effects = [(e.effect_type, float(e.value)) for e in known_effects]

    # 5. 调用 Rust
    with _rust_call_lock:
        rs_result = _rs.evaluate_search_damage(
            final_attack=final_attack,
            skill_multiplier=skill_multiplier,
            skill_type=skill_type,
            is_true_damage=is_true_damage,
            is_unbalanced=is_unbalanced,
            enemy_defense=enemy_defense,
            enemy_resistance=enemy_resistance,
            ignore_resistance=ignore_resistance,
            imbalance_vulnerability_coeff=imbalance_vulnerability_coeff,
            crit_rate=crit_rate,
            crit_damage=crit_damage,
            damage_type_bonus=damage_type_bonus,
            skill_type_bonus=skill_type_bonus,
            imbalance_damage_bonus=imbalance_damage_bonus,
            other_damage_bonus=other_damage_bonus,
            combo_stacks=combo_stacks,
            break_defense_stacks=break_defense_stacks,
            base_damage_bonus=base_damage_bonus,
            effects=rust_effects,
            crit_mode=crit_mode,
            damage_pipeline=damage_pipeline,
        )

    # 6. 转换为 Python DamageEvalResult 风格
    from games.endfield.calc.dag_adapter.search_evaluate import DamageEvalResult

    return DamageEvalResult(
        final_damage=rs_result.final_damage,
        zone_values=dict(rs_result.zone_values),
        warnings=tuple(str(w) for w in warnings),
        unknown_effects=tuple(u for u in unknown_effects),
    )


def _preprocess_for_rust(**kwargs: Any) -> dict:
    """预处理单组参数 → Rust 批量调用的 flat 字段。"""
    final_attack = kwargs["final_attack"]
    skill_multiplier = kwargs["skill_multiplier"]
    damage_type = kwargs["damage_type"]
    skill_type = kwargs["skill_type"]
    is_unbalanced = kwargs.get("is_unbalanced", False)
    is_true_damage = kwargs.get("is_true_damage", False)
    enemy_defense = kwargs.get("enemy_defense", 100.0)
    enemy_resistance = kwargs.get("enemy_resistance", 0.0)
    ignore_resistance = kwargs.get("ignore_resistance", 0.0)
    imbalance_vulnerability_coeff = kwargs.get("imbalance_vulnerability_coeff", 1.3)
    crit_rate = kwargs.get("crit_rate", 0.05)
    crit_damage = kwargs.get("crit_damage", 0.5)
    damage_type_bonus = kwargs.get("damage_type_bonus", 0.0)
    skill_type_bonus = kwargs.get("skill_type_bonus", 0.0)
    imbalance_damage_bonus = kwargs.get("imbalance_damage_bonus", 0.0)
    other_damage_bonus = kwargs.get("other_damage_bonus", 0.0)
    combo_stacks = kwargs.get("combo_stacks", 0)
    break_defense_stacks = kwargs.get("break_defense_stacks", 0)
    base_damage_bonus = kwargs.get("base_damage_bonus", 0.0)
    effects = kwargs.get("effects") or []
    crit_mode = kwargs.get("crit_mode", "non_crit")
    manual_buffs = kwargs.get("manual_buffs")
    damage_pipeline = kwargs.get("damage_pipeline", "normal")

    if not _HAS_RUST:
        return {"fallback": True, **kwargs}

    if manual_buffs:
        overrides, extra_effects = _apply_manual_buffs(
            manual_buffs=manual_buffs,
            crit_rate=crit_rate,
            crit_damage=crit_damage,
            damage_type_bonus=damage_type_bonus,
            skill_type_bonus=skill_type_bonus,
            imbalance_damage_bonus=imbalance_damage_bonus,
            other_damage_bonus=other_damage_bonus,
        )
        crit_rate = overrides["crit_rate"]
        crit_damage = overrides["crit_damage"]
        damage_type_bonus = overrides["damage_type_bonus"]
        skill_type_bonus = overrides["skill_type_bonus"]
        imbalance_damage_bonus = overrides["imbalance_damage_bonus"]
        other_damage_bonus = overrides["other_damage_bonus"]
    else:
        extra_effects = []

    all_effects = list(effects) + extra_effects + list(damage_effects_from_break_defense(break_defense_stacks))
    _ctx = DamageContext(
        final_attack=final_attack,
        skill_multiplier=skill_multiplier,
        damage_type=damage_type,
        skill_type=skill_type,
        is_unbalanced=is_unbalanced,
        is_true_damage=is_true_damage,
        enemy_defense=enemy_defense,
        enemy_resistance=enemy_resistance,
        ignore_resistance=ignore_resistance,
        imbalance_vulnerability_coeff=imbalance_vulnerability_coeff,
        crit_rate=crit_rate,
        crit_damage=crit_damage,
        damage_type_bonus=damage_type_bonus,
        skill_type_bonus=skill_type_bonus,
        imbalance_damage_bonus=imbalance_damage_bonus,
        other_damage_bonus=other_damage_bonus,
        combo_stacks=combo_stacks,
        break_defense_stacks=break_defense_stacks,
        base_damage_bonus=base_damage_bonus,
    )
    known_effects, _unknown, _warnings = _collect_effects(_ctx, all_effects)
    rust_effects = [(e.effect_type, float(e.value)) for e in known_effects]

    return dict(
        final_attack=final_attack,
        skill_multiplier=skill_multiplier,
        skill_type=skill_type,
        is_true_damage=is_true_damage,
        is_unbalanced=is_unbalanced,
        enemy_defense=enemy_defense,
        enemy_resistance=enemy_resistance,
        ignore_resistance=ignore_resistance,
        imbalance_vulnerability_coeff=imbalance_vulnerability_coeff,
        crit_rate=crit_rate,
        crit_damage=crit_damage,
        damage_type_bonus=damage_type_bonus,
        skill_type_bonus=skill_type_bonus,
        imbalance_damage_bonus=imbalance_damage_bonus,
        other_damage_bonus=other_damage_bonus,
        combo_stacks=combo_stacks,
        break_defense_stacks=break_defense_stacks,
        base_damage_bonus=base_damage_bonus,
        effects=rust_effects,
        crit_mode=crit_mode,
        damage_pipeline=damage_pipeline,
    )


def evaluate_search_damage_batch(param_list: list[dict]) -> list[Any]:
    """批量评估 N 组参数，摊销 Rust FFI 开销。

    Args:
        param_list: ``evaluate_search_damage`` 参数字典列表（与单函数一致）

    Returns:
        ``DamageEvalResult`` 列表
    """
    if not _HAS_RUST or not param_list:
        from games.endfield.calc.dag_adapter.search_evaluate import (
            evaluate_search_damage as _py_eval,
        )

        return [_py_eval(**p) for p in param_list]

    preprocessed = [_preprocess_for_rust(**p) for p in param_list]
    if any(pp.get("fallback") for pp in preprocessed):
        from games.endfield.calc.dag_adapter.search_evaluate import (
            evaluate_search_damage as _py_eval,
        )

        return [_py_eval(**p) for p in param_list]

    N = len(preprocessed)

    def pluck(key: str):
        return [pp[key] for pp in preprocessed]

    def _invoke_batch() -> list:
        return _rs.evaluate_search_damage_batch(
            final_attacks=pluck("final_attack"),
            skill_multipliers=pluck("skill_multiplier"),
            skill_types=pluck("skill_type"),
            is_true_damages=pluck("is_true_damage"),
            is_unbalanceds=pluck("is_unbalanced"),
            enemy_defenses=pluck("enemy_defense"),
            enemy_resistances=pluck("enemy_resistance"),
            ignore_resistances=pluck("ignore_resistance"),
            imbalance_vulnerability_coeffs=pluck("imbalance_vulnerability_coeff"),
            crit_rates=pluck("crit_rate"),
            crit_damages=pluck("crit_damage"),
            damage_type_bonuses=pluck("damage_type_bonus"),
            skill_type_bonuses=pluck("skill_type_bonus"),
            imbalance_damage_bonuses=pluck("imbalance_damage_bonus"),
            other_damage_bonuses=pluck("other_damage_bonus"),
            combo_stacks_list=pluck("combo_stacks"),
            break_defense_stacks_list=pluck("break_defense_stacks"),
            base_damage_bonuses=pluck("base_damage_bonus"),
            effects_batch=pluck("effects"),
            crit_modes=pluck("crit_mode"),
            damage_pipelines=pluck("damage_pipeline"),
        )

    from utils.frozen_runtime import rust_parallel_batch_enabled

    if rust_parallel_batch_enabled():
        rs_results = _invoke_batch()
    else:
        with _rust_call_lock:
            rs_results = _invoke_batch()

    from games.endfield.calc.dag_adapter.search_evaluate import DamageEvalResult

    return [DamageEvalResult(final_damage=fd, zone_values={}, warnings=(), unknown_effects=()) for fd in rs_results]


def _preprocess_for_rust_soa(
    param_list: list[dict],
) -> dict[str, list] | None:
    """批量预处理 → SoA 格式的 flat lists。返回 None 表示降级。

    与 _preprocess_for_rust 逻辑一致，但：
    - 效果类型映射为整数 ID（消除 Rust 侧字符串匹配）
    - 技能类型/暴击模式映射为整数 ID
    - damage_pipeline 映射为 bool（"abnormal" → True）
    """
    if not _HAS_RUST:
        return None

    n = len(param_list)
    final_attacks: list[float] = [0.0] * n
    skill_multipliers: list[float] = [0.0] * n
    skill_type_ids: list[int] = [0] * n
    is_true_damages: list[bool] = [False] * n
    is_unbalanceds: list[bool] = [False] * n
    enemy_defenses: list[float] = [100.0] * n
    enemy_resistances: list[float] = [0.0] * n
    ignore_resistances: list[float] = [0.0] * n
    imbalance_vulnerability_coeffs: list[float] = [1.3] * n
    crit_rates: list[float] = [0.05] * n
    crit_damages: list[float] = [0.5] * n
    damage_type_bonuses: list[float] = [0.0] * n
    skill_type_bonuses: list[float] = [0.0] * n
    imbalance_damage_bonuses: list[float] = [0.0] * n
    other_damage_bonuses: list[float] = [0.0] * n
    combo_stacks_list: list[int] = [0] * n
    break_defense_stacks_list: list[int] = [0] * n
    base_damage_bonuses: list[float] = [0.0] * n
    effect_ids_batch: list[list[int]] = [[] for _ in range(n)]
    effect_values_batch: list[list[float]] = [[] for _ in range(n)]
    crit_mode_ids: list[int] = [0] * n
    is_abnormals: list[bool] = [False] * n

    for i, p in enumerate(param_list):
        # 提取参数
        crit_rate = p.get("crit_rate", 0.05)
        crit_damage = p.get("crit_damage", 0.5)
        damage_type_bonus = p.get("damage_type_bonus", 0.0)
        skill_type_bonus = p.get("skill_type_bonus", 0.0)
        imbalance_damage_bonus = p.get("imbalance_damage_bonus", 0.0)
        other_damage_bonus = p.get("other_damage_bonus", 0.0)
        combo_stacks = p.get("combo_stacks", 0)
        break_defense_stacks = p.get("break_defense_stacks", 0)

        # 处理 manual_buffs
        manual_buffs = p.get("manual_buffs")
        if manual_buffs:
            overrides, extra_effects = _apply_manual_buffs(
                manual_buffs=manual_buffs,
                crit_rate=crit_rate,
                crit_damage=crit_damage,
                damage_type_bonus=damage_type_bonus,
                skill_type_bonus=skill_type_bonus,
                imbalance_damage_bonus=imbalance_damage_bonus,
                other_damage_bonus=other_damage_bonus,
            )
            crit_rate = overrides["crit_rate"]
            crit_damage = overrides["crit_damage"]
            damage_type_bonus = overrides["damage_type_bonus"]
            skill_type_bonus = overrides["skill_type_bonus"]
            imbalance_damage_bonus = overrides["imbalance_damage_bonus"]
            other_damage_bonus = overrides["other_damage_bonus"]
        else:
            extra_effects = []

        # 合并效果列表
        effects = list(p.get("effects") or [])
        all_effects = effects + extra_effects + list(damage_effects_from_break_defense(break_defense_stacks))

        # 预处理效果 → _collect_effects
        _ctx = DamageContext(
            final_attack=p["final_attack"],
            skill_multiplier=p["skill_multiplier"],
            damage_type=p.get("damage_type", ""),
            skill_type=p.get("skill_type", "战技"),
            is_unbalanced=p.get("is_unbalanced", False),
            is_true_damage=p.get("is_true_damage", False),
            enemy_defense=p.get("enemy_defense", 100.0),
            enemy_resistance=p.get("enemy_resistance", 0.0),
            ignore_resistance=p.get("ignore_resistance", 0.0),
            imbalance_vulnerability_coeff=p.get("imbalance_vulnerability_coeff", 1.3),
            crit_rate=crit_rate,
            crit_damage=crit_damage,
            damage_type_bonus=damage_type_bonus,
            skill_type_bonus=skill_type_bonus,
            imbalance_damage_bonus=imbalance_damage_bonus,
            other_damage_bonus=other_damage_bonus,
            combo_stacks=combo_stacks,
            break_defense_stacks=break_defense_stacks,
            base_damage_bonus=p.get("base_damage_bonus", 0.0),
        )
        known_effects, _unknown, _warnings = _collect_effects(_ctx, all_effects)

        # 填充 SoA 数组
        final_attacks[i] = p["final_attack"]
        skill_multipliers[i] = p["skill_multiplier"]
        skill_type_ids[i] = _SKILL_TYPE_ID_MAP.get(p.get("skill_type", "战技"), 0)
        is_true_damages[i] = p.get("is_true_damage", False)
        is_unbalanceds[i] = p.get("is_unbalanced", False)
        enemy_defenses[i] = p.get("enemy_defense", 100.0)
        enemy_resistances[i] = p.get("enemy_resistance", 0.0)
        ignore_resistances[i] = p.get("ignore_resistance", 0.0)
        imbalance_vulnerability_coeffs[i] = p.get("imbalance_vulnerability_coeff", 1.3)
        crit_rates[i] = crit_rate
        crit_damages[i] = crit_damage
        damage_type_bonuses[i] = damage_type_bonus
        skill_type_bonuses[i] = skill_type_bonus
        imbalance_damage_bonuses[i] = imbalance_damage_bonus
        other_damage_bonuses[i] = other_damage_bonus
        combo_stacks_list[i] = combo_stacks
        break_defense_stacks_list[i] = break_defense_stacks
        base_damage_bonuses[i] = p.get("base_damage_bonus", 0.0)
        crit_mode_ids[i] = _CRIT_MODE_ID_MAP.get(p.get("crit_mode", "non_crit"), 0)
        is_abnormals[i] = p.get("damage_pipeline", "normal") == "abnormal"

        # 效果 → 整数 ID
        ids: list[int] = []
        vals: list[float] = []
        for e in known_effects:
            eid = _EFFECT_ID_MAP.get(e.effect_type)
            if eid is not None:
                ids.append(eid)
                vals.append(float(e.value))
        effect_ids_batch[i] = ids
        effect_values_batch[i] = vals

    return {
        "final_attacks": final_attacks,
        "skill_multipliers": skill_multipliers,
        "skill_type_ids": skill_type_ids,
        "is_true_damages": is_true_damages,
        "is_unbalanceds": is_unbalanceds,
        "enemy_defenses": enemy_defenses,
        "enemy_resistances": enemy_resistances,
        "ignore_resistances": ignore_resistances,
        "imbalance_vulnerability_coeffs": imbalance_vulnerability_coeffs,
        "crit_rates": crit_rates,
        "crit_damages": crit_damages,
        "damage_type_bonuses": damage_type_bonuses,
        "skill_type_bonuses": skill_type_bonuses,
        "imbalance_damage_bonuses": imbalance_damage_bonuses,
        "other_damage_bonuses": other_damage_bonuses,
        "combo_stacks_list": combo_stacks_list,
        "break_defense_stacks_list": break_defense_stacks_list,
        "base_damage_bonuses": base_damage_bonuses,
        "effect_ids_batch": effect_ids_batch,
        "effect_values_batch": effect_values_batch,
        "crit_mode_ids": crit_mode_ids,
        "is_abnormals": is_abnormals,
    }


def evaluate_search_batch_soa(param_list: list[dict]) -> list[Any]:
    """SoA 批量评估：一次 FFI 调用处理 N 个任务（零 Python 循环）。

    与 ``evaluate_search_damage_batch`` 功能一致，但使用 SoA 格式
    消除 per-task FFI 开销和字符串匹配。

    Args:
        param_list: ``evaluate_search_damage`` 参数字典列表

    Returns:
        ``DamageEvalResult`` 列表
    """
    if not _HAS_RUST or not param_list:
        from games.endfield.calc.dag_adapter.search_evaluate import (
            evaluate_search_damage as _py_eval,
        )

        return [_py_eval(**p) for p in param_list]

    soa = _preprocess_for_rust_soa(param_list)
    if soa is None:
        from games.endfield.calc.dag_adapter.search_evaluate import (
            evaluate_search_damage as _py_eval,
        )

        return [_py_eval(**p) for p in param_list]

    from utils.frozen_runtime import rust_parallel_batch_enabled

    if rust_parallel_batch_enabled():
        rs_results = _rs.evaluate_search_batch_soa(**soa)
    else:
        with _rust_call_lock:
            rs_results = _rs.evaluate_search_batch_soa(**soa)

    from games.endfield.calc.dag_adapter.search_evaluate import DamageEvalResult

    return [DamageEvalResult(final_damage=fd, zone_values={}, warnings=(), unknown_effects=()) for fd in rs_results]


def evaluate_search_batch_raw(
    final_attacks: list[float],
    skill_multipliers: list[float],
    skill_type_ids: list[int],
    is_true_damages: list[bool],
    is_unbalanceds: list[bool],
    enemy_defenses: list[float],
    enemy_resistances: list[float],
    ignore_resistances: list[float],
    imbalance_vulnerability_coeffs: list[float],
    crit_rates: list[float],
    crit_damages: list[float],
    damage_type_bonuses: list[float],
    skill_type_bonuses: list[float],
    imbalance_damage_bonuses: list[float],
    other_damage_bonuses: list[float],
    combo_stacks_list: list[int],
    break_defense_stacks_list: list[int],
    base_damage_bonuses: list[float],
    effect_ids_batch: list[list[int]],
    effect_values_batch: list[list[float]],
    crit_mode_ids: list[int],
    is_abnormals: list[bool],
) -> list[float]:
    """原始数组批量评估：零 Python dict 开销，一次 FFI 调用处理 N 个任务。

    与 ``evaluate_search_batch_soa`` 相同的 Rust 内核，但接受原始数组参数，
    避免 Python 侧构建和解析 dict 的开销。

    Args:
        各参数为长度 N 的列表，与 Rust 侧 BatchInput 字段一一对应。

    Returns:
        每个任务的最终伤害值列表
    """
    if not _HAS_RUST or not final_attacks:
        return [0.0] * len(final_attacks)

    from utils.frozen_runtime import rust_parallel_batch_enabled

    if rust_parallel_batch_enabled():
        rs_results = _rs.evaluate_search_batch_raw(
            final_attacks,
            skill_multipliers,
            skill_type_ids,
            is_true_damages,
            is_unbalanceds,
            enemy_defenses,
            enemy_resistances,
            ignore_resistances,
            imbalance_vulnerability_coeffs,
            crit_rates,
            crit_damages,
            damage_type_bonuses,
            skill_type_bonuses,
            imbalance_damage_bonuses,
            other_damage_bonuses,
            combo_stacks_list,
            break_defense_stacks_list,
            base_damage_bonuses,
            effect_ids_batch,
            effect_values_batch,
            crit_mode_ids,
            is_abnormals,
        )
    else:
        with _rust_call_lock:
            rs_results = _rs.evaluate_search_batch_raw(
                final_attacks,
                skill_multipliers,
                skill_type_ids,
                is_true_damages,
                is_unbalanceds,
                enemy_defenses,
                enemy_resistances,
                ignore_resistances,
                imbalance_vulnerability_coeffs,
                crit_rates,
                crit_damages,
                damage_type_bonuses,
                skill_type_bonuses,
                imbalance_damage_bonuses,
                other_damage_bonuses,
                combo_stacks_list,
                break_defense_stacks_list,
                base_damage_bonuses,
                effect_ids_batch,
                effect_values_batch,
                crit_mode_ids,
                is_abnormals,
            )

    return list(rs_results)


def evaluate_full_batch(
    weapon_names: list[str],
    weapon_final_attacks: list[float],
    weapon_effects: list[list[tuple[str, float]]],
    equipment_chest_names: list[str],
    equipment_gloves_names: list[str],
    equipment_acc_a_names: list[str],
    equipment_acc_b_names: list[str],
    equipment_effects: list[list[tuple[str, float]]],
    equipment_flat_stats: list[dict[str, float]],
    equipment_atk_percents: list[float],
    char_name: str,
    char_level: int,
    char_base_attack: float,
    skill_multiplier: float,
    damage_type: str,
    skill_type: str,
    is_unbalanced: bool,
    is_true_damage: bool,
    enemy_defense: float,
    enemy_resistance: float,
    ignore_resistance: float,
    imbalance_vulnerability_coeff: float,
    crit_rate: float,
    crit_damage: float,
    damage_type_bonus: float,
    skill_type_bonus: float,
    imbalance_damage_bonus: float,
    other_damage_bonus: float,
    combo_stacks: int,
    break_defense_stacks: int,
    base_damage_bonus: float,
    top_n: int = 10,
) -> list[tuple[str, float, dict[str, str]]]:
    """全批量评估：Python 预处理 → Rust 完整评估 → 返回结果。

    消除 Python 逐任务开销，实现 ~5 秒完成 97 万组合遍历。

    Args:
        各参数为预处理后的数据，详见 rust_batch_data.py。

    Returns:
        [(武器名, 最终伤害, {部位: 装备名})] 列表，按伤害降序排列。
    """
    if not _HAS_RUST or not weapon_names:
        return []

    from utils.frozen_runtime import rust_parallel_batch_enabled

    if rust_parallel_batch_enabled():
        rs_results = _rs.evaluate_full_batch_py(
            weapon_names,
            weapon_final_attacks,
            weapon_effects,
            equipment_chest_names,
            equipment_gloves_names,
            equipment_acc_a_names,
            equipment_acc_b_names,
            equipment_effects,
            equipment_flat_stats,
            equipment_atk_percents,
            char_name,
            char_level,
            char_base_attack,
            skill_multiplier,
            damage_type,
            skill_type,
            is_unbalanced,
            is_true_damage,
            enemy_defense,
            enemy_resistance,
            ignore_resistance,
            imbalance_vulnerability_coeff,
            crit_rate,
            crit_damage,
            damage_type_bonus,
            skill_type_bonus,
            imbalance_damage_bonus,
            other_damage_bonus,
            combo_stacks,
            break_defense_stacks,
            base_damage_bonus,
            top_n,
        )
    else:
        with _rust_call_lock:
            rs_results = _rs.evaluate_full_batch_py(
                weapon_names,
                weapon_final_attacks,
                weapon_effects,
                equipment_chest_names,
                equipment_gloves_names,
                equipment_acc_a_names,
                equipment_acc_b_names,
                equipment_effects,
                equipment_flat_stats,
                equipment_atk_percents,
                char_name,
                char_level,
                char_base_attack,
                skill_multiplier,
                damage_type,
                skill_type,
                is_unbalanced,
                is_true_damage,
                enemy_defense,
                enemy_resistance,
                ignore_resistance,
                imbalance_vulnerability_coeff,
                crit_rate,
                crit_damage,
                damage_type_bonus,
                skill_type_bonus,
                imbalance_damage_bonus,
                other_damage_bonus,
                combo_stacks,
                break_defense_stacks,
                base_damage_bonus,
                top_n,
            )

    return [(r[0], r[1], dict(r[2])) for r in rs_results]
