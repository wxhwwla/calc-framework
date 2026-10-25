#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test process + batch integration via real search pipeline."""

import sys
import time

sys.path.insert(0, "games/endfield")
sys.path.insert(0, "framework/src")
sys.path.insert(0, ".")

from games.endfield.calc.damage.engine import DamageContext
from games.endfield.calc.loadout.in_memory_optimizer import run_enumerated_optimizer_parallel
from games.endfield.calc.loadout.optimizer import OptimizerConfig
from games.endfield.calc.loadout.optimizer.types import WeaponCandidate

# Build catalog with proper structure (at least 1 item per slot)
chests = [{"名称": f"胸甲{i}", "装备种类": "护甲", "部位": "护甲", "效果": []} for i in range(5)]
gloves = [{"名称": f"护手{i}", "装备种类": "护手", "部位": "护手", "效果": []} for i in range(5)]
accs = [{"名称": f"配件{i}", "装备种类": "配件", "部位": "配件", "效果": []} for i in range(3)]

catalog = {"chest": chests, "gloves": gloves, "accessories": accs}
weapons = [WeaponCandidate(name=f"武器{i}", final_attack=1000.0 + i * 50) for i in range(3)]
ctx = DamageContext(
    final_attack=1000.0, skill_multiplier=2.0, damage_type="物理", skill_type="战技", enemy_defense=200.0
)

config = OptimizerConfig(
    top_n=3,
    crit_mode="non_crit",
    sort_equipment_by_priority=False,
    prune_non_beneficial=False,
)

print("=== 线程+批量 ===")
t0 = time.perf_counter()
r1, tot1, proc1, canc1, w1 = run_enumerated_optimizer_parallel(
    base_context=ctx,
    weapons=weapons,
    equipment_catalog=catalog,
    config=config,
    max_workers=4,
    parallel_backend="thread",
    batch_size=200,
)
t1 = time.perf_counter() - t0
print(f"  {tot1} 组合, {t1:.3f}s ({tot1 / t1:.0f}/s), Top3: {[f'{s.final_damage:.0f}' for s in r1]}")

print("=== 进程+批量 ===")
t0 = time.perf_counter()
r2, tot2, proc2, canc2, w2 = run_enumerated_optimizer_parallel(
    base_context=ctx,
    weapons=weapons,
    equipment_catalog=catalog,
    config=config,
    max_workers=4,
    parallel_backend="process",
    batch_size=200,
)
t2 = time.perf_counter() - t0
print(f"  {tot2} 组合, {t2:.3f}s ({tot2 / t2:.0f}/s), Top3: {[f'{s.final_damage:.0f}' for s in r2]}")

# 正确性验证
print("\n=== 正确性 ===")
match = True
for i in range(min(len(r1), len(r2))):
    if abs(r1[i].final_damage - r2[i].final_damage) > 1e-6:
        print(f"  #{i}: thread={r1[i].final_damage:.3f} process={r2[i].final_damage:.3f} MISMATCH")
        match = False
if match:
    print("  Top-N 完全一致 PASS")
