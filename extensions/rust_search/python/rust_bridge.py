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
        unknown_effects=tuple({"effect_type": str(u[0]), "source": str(u[1])} for u in unknown_effects),
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

    rs_results = _rs.evaluate_search_damage_batch(
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

    from games.endfield.calc.dag_adapter.search_evaluate import DamageEvalResult

    return [DamageEvalResult(final_damage=fd, zone_values={}, warnings=(), unknown_effects=()) for fd in rs_results]
