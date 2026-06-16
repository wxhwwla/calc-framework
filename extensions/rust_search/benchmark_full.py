#!/usr/bin/env python3
"""完整基准：Python vs Rust 单次 vs Rust 批量 + 缓存验证。"""

import importlib
import os
import sys
import time

sys.path.insert(0, "games/endfield")
sys.path.insert(0, "framework/src")
sys.path.insert(0, ".")

# 改 RUST_SEARCH_FALLBACK 用 Python 级操作，避免 PowerShell 展开
_ENV_KEY = "RUST_SEARCH_FALLBACK"


def main():
    N = 50000
    BATCH = 1000

    # 生成测试参数 — 模拟 10 把武器 × 同一配装
    params_list = []
    N_WEAPONS = 10
    for wi in range(N_WEAPONS):
        w_fa = 1200.0 + wi * 50.0
        for _ in range(N // N_WEAPONS):
            params_list.append(
                {
                    "final_attack": w_fa,
                    "skill_multiplier": 2.0,
                    "damage_type": "物理",
                    "skill_type": "战技",
                    "is_unbalanced": False,
                    "is_true_damage": False,
                    "enemy_defense": 200.0,
                    "enemy_resistance": 0.0,
                    "ignore_resistance": 0.0,
                    "imbalance_vulnerability_coeff": 1.3,
                    "crit_rate": 0.05,
                    "crit_damage": 0.5,
                    "damage_type_bonus": 0.1,
                    "skill_type_bonus": 0.0,
                    "imbalance_damage_bonus": 0.0,
                    "other_damage_bonus": 0.0,
                    "combo_stacks": 0,
                    "break_defense_stacks": 0,
                    "base_damage_bonus": 0.0,
                    "effects": [],
                    "crit_mode": "non_crit",
                    "manual_buffs": None,
                    "damage_pipeline": "normal",
                }
            )

    print("=" * 60)
    print("D+B 联合基准测试")
    print("=" * 60)
    print(f"组合数: {N} (10 武器 × {N // 10} 配装 = cache 命中 90%)")
    print()

    # ── Python 路径 ──
    os.environ[_ENV_KEY] = "1"
    import games.endfield.calc.loadout.optimizer.evaluate as ev_mod

    importlib.reload(ev_mod)
    from games.endfield.calc.dag_adapter.search_evaluate import evaluate_search_damage as py_fn

    for _ in range(500):
        py_fn(**params_list[0])
    t0 = time.perf_counter()
    for p in params_list:
        py_fn(**p)
    t_py = time.perf_counter() - t0
    print(f"Python 单次 evaluate: {t_py:.3f}s  ({N / t_py:.0f} 次/s)")

    # ── Rust 单次 ──
    del os.environ[_ENV_KEY]
    importlib.reload(ev_mod)
    import rust_search

    p0 = params_list[0]
    for _ in range(500):
        rust_search.evaluate_search_damage(
            final_attack=p0["final_attack"],
            skill_multiplier=p0["skill_multiplier"],
            skill_type=p0["skill_type"],
            is_true_damage=False,
            is_unbalanced=p0["is_unbalanced"],
            enemy_defense=p0["enemy_defense"],
            enemy_resistance=0.0,
            ignore_resistance=0.0,
            imbalance_vulnerability_coeff=1.3,
            crit_rate=p0["crit_rate"],
            crit_damage=p0["crit_damage"],
            damage_type_bonus=p0["damage_type_bonus"],
            skill_type_bonus=0.0,
            imbalance_damage_bonus=0.0,
            other_damage_bonus=0.0,
            combo_stacks=0,
            break_defense_stacks=0,
            base_damage_bonus=0.0,
            effects=[],
            crit_mode=p0["crit_mode"],
            damage_pipeline="normal",
        )
    t0 = time.perf_counter()
    for p in params_list:
        rust_search.evaluate_search_damage(
            final_attack=p["final_attack"],
            skill_multiplier=p["skill_multiplier"],
            skill_type=p["skill_type"],
            is_true_damage=False,
            is_unbalanced=p["is_unbalanced"],
            enemy_defense=p["enemy_defense"],
            enemy_resistance=0.0,
            ignore_resistance=0.0,
            imbalance_vulnerability_coeff=1.3,
            crit_rate=p["crit_rate"],
            crit_damage=p["crit_damage"],
            damage_type_bonus=p["damage_type_bonus"],
            skill_type_bonus=0.0,
            imbalance_damage_bonus=0.0,
            other_damage_bonus=0.0,
            combo_stacks=0,
            break_defense_stacks=0,
            base_damage_bonus=0.0,
            effects=[],
            crit_mode=p["crit_mode"],
            damage_pipeline="normal",
        )
    t_rs1 = time.perf_counter() - t0
    print(f"Rust 单次 evaluate:     {t_rs1:.3f}s  ({N / t_rs1:.0f} 次/s)")

    # ── Rust 批量 ──
    v_attacks = [p["final_attack"] for p in params_list]
    v_skill_mul = [p["skill_multiplier"] for p in params_list]
    v_skill_type = [p["skill_type"] for p in params_list]
    v_unbalanced = [p["is_unbalanced"] for p in params_list]
    v_defense = [p["enemy_defense"] for p in params_list]
    v_crit_rate = [p["crit_rate"] for p in params_list]
    v_crit_dmg = [p["crit_damage"] for p in params_list]
    v_dmg_bonus = [p["damage_type_bonus"] for p in params_list]
    v_mode = [p["crit_mode"] for p in params_list]

    batches = list(range(0, N, BATCH))
    t0 = time.perf_counter()
    for start in batches:
        end = min(start + BATCH, N)
        rust_search.evaluate_search_damage_batch(
            final_attacks=v_attacks[start:end],
            skill_multipliers=v_skill_mul[start:end],
            skill_types=v_skill_type[start:end],
            is_true_damages=[False] * (end - start),
            is_unbalanceds=v_unbalanced[start:end],
            enemy_defenses=v_defense[start:end],
            enemy_resistances=[0.0] * (end - start),
            ignore_resistances=[0.0] * (end - start),
            imbalance_vulnerability_coeffs=[1.3] * (end - start),
            crit_rates=v_crit_rate[start:end],
            crit_damages=v_crit_dmg[start:end],
            damage_type_bonuses=v_dmg_bonus[start:end],
            skill_type_bonuses=[0.0] * (end - start),
            imbalance_damage_bonuses=[0.0] * (end - start),
            other_damage_bonuses=[0.0] * (end - start),
            combo_stacks_list=[0] * (end - start),
            break_defense_stacks_list=[0] * (end - start),
            base_damage_bonuses=[0.0] * (end - start),
            effects_batch=[[] for _ in range(end - start)],
            crit_modes=v_mode[start:end],
            damage_pipelines=["normal"] * (end - start),
        )
    t_rsB = time.perf_counter() - t0
    print(f"Rust 批量 evaluate:     {t_rsB:.3f}s  ({N / t_rsB:.0f} 次/s)")

    print()
    print(f"Python → Rust 单次:  {t_py / t_rs1:.1f}x")
    print(f"Python → Rust 批量:  {t_py / t_rsB:.1f}x")
    print(f"Rust 单次 → 批量:    {t_rs1 / t_rsB:.1f}x")


if __name__ == "__main__":
    main()
