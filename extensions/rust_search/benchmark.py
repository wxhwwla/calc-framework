#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rust 搜索加速 — 性能基准测试。

用法: python extensions/rust_search/benchmark.py [--ci]
"""

from __future__ import annotations

import importlib
import os
import sys
import time

sys.path.insert(0, "games/endfield")
sys.path.insert(0, "framework/src")
sys.path.insert(0, ".")

from games.endfield.calc.damage.engine import DamageContext
from games.endfield.calc.loadout.optimizer.types import WeaponCandidate


def make_task():
    """用模拟数据构造搜索任务 — 不必加载真实 JSON。"""
    weapon = WeaponCandidate(name="测试武器", final_attack=1200.0)
    # 四件模拟装备（部位用 _SLOT_ALIASES 能识别的规范值）
    chest = {"名称": "测试胸甲", "部位": "护甲", "效果": []}
    glove = {"名称": "测试护手", "部位": "护手", "效果": []}
    acc_a = {"名称": "测试配件A", "部位": "配件", "效果": []}
    acc_b = {"名称": "测试配件B", "部位": "配件", "效果": []}
    return (weapon, (chest, glove, acc_a, acc_b))


def make_context():
    return DamageContext(
        final_attack=1200.0,
        skill_multiplier=2.0,
        damage_type="物理",
        skill_type="战技",
        enemy_defense=200.0,
    )


def bench(use_rust: bool, n: int = 5000):
    """运行基准测试。"""
    if use_rust:
        os.environ.pop("RUST_SEARCH_FALLBACK", None)
    else:
        os.environ["RUST_SEARCH_FALLBACK"] = "1"

    # 重新加载模块以触发正确的导入路径
    import games.endfield.calc.loadout.optimizer.evaluate as ev_mod

    importlib.reload(ev_mod)
    from games.endfield.calc.loadout.optimizer.evaluate import evaluate_task as fn

    task = make_task()
    ctx = make_context()

    # 预热
    for _ in range(200):
        fn(base_context=ctx, crit_mode="non_crit", task=task)

    # 正式计时
    t0 = time.perf_counter()
    for _ in range(n):
        fn(base_context=ctx, crit_mode="non_crit", task=task)
    dt = time.perf_counter() - t0

    return dt, n / dt


def verify_correctness(n: int = 1000) -> int:
    """Python vs Rust 逐结果对比验证。"""
    os.environ["RUST_SEARCH_FALLBACK"] = "1"
    import games.endfield.calc.loadout.optimizer.evaluate as ev_mod

    importlib.reload(ev_mod)
    from games.endfield.calc.loadout.optimizer.evaluate import evaluate_task as py_fn

    os.environ.pop("RUST_SEARCH_FALLBACK", None)
    importlib.reload(ev_mod)
    from games.endfield.calc.loadout.optimizer.evaluate import evaluate_task as rs_fn

    task = make_task()
    ctx = make_context()
    errors = 0
    for i in range(n):
        r_py = py_fn(base_context=ctx, crit_mode="non_crit", task=task)
        r_rs = rs_fn(base_context=ctx, crit_mode="non_crit", task=task)
        if abs(r_py.final_damage - r_rs.final_damage) > 1e-9:
            print(f"  差异! #{i}: Python={r_py.final_damage} Rust={r_rs.final_damage}")
            errors += 1
            if errors >= 5:
                break
    return errors


def main():
    n = 10000

    print("=" * 60)
    print("Rust 搜索加速 — 性能基准测试")
    print("=" * 60)
    print(f"测试量: evaluate_task x {n}")
    print()

    dt_py, rate_py = bench(use_rust=False, n=n)
    label_py = f"Python evaluate_task: {dt_py:.3f}s  ({rate_py:.0f} 次/s)"
    print(label_py)

    dt_rs, rate_rs = bench(use_rust=True, n=n)
    label_rs = f"Rust   evaluate_task: {dt_rs:.3f}s  ({rate_rs:.0f} 次/s)"
    print(label_rs)

    speedup = rate_rs / rate_py
    print(f"\n加速比: {speedup:.1f}x")

    if "--ci" in sys.argv:
        print(f"\nCI_RESULT: Py={rate_py:.0f}/s Rs={rate_rs:.0f}/s Sp={speedup:.1f}x")

    print("\n--- 正确性验证 ---")
    errors = verify_correctness(1000)
    if errors:
        print(f"  FAIL: {errors}/1000 结果不一致!")
    else:
        print("  PASS: 1000/1000 结果完全一致")

    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
