#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Profile the batch pipeline breakdown. Measures time per component."""

import sys
import time

sys.path.insert(0, "games/endfield")
sys.path.insert(0, "framework/src")
sys.path.insert(0, ".")

from games.endfield.calc.damage.engine import DamageContext
from games.endfield.calc.equipment.affix import aggregate_loadout_modifiers
from games.endfield.calc.equipment.system import build_four_slot_loadout
from games.endfield.calc.loadout.optimizer.evaluate import build_runtime_eval_snapshot, evaluate_task
from games.endfield.calc.loadout.optimizer.types import WeaponCandidate

# Mock data with realistic effects
weapon = WeaponCandidate(
    name="测试武器",
    final_attack=1200.0,
    effects=(),
)
chest = {"名称": "胸甲", "部位": "护甲", "效果": [], "套装": "A", "三件套效果": [], "属性词条": {"攻击力": 10}}
glove = {"名称": "护手", "部位": "护手", "效果": [], "套装": "A", "三件套效果": [], "属性词条": {}}
acc_a = {"名称": "配件A", "部位": "配件", "效果": [], "套装": "A", "三件套效果": [], "属性词条": {}}
acc_b = {"名称": "配件B", "部位": "配件", "效果": [], "套装": "B", "三件套效果": [], "属性词条": {}}

ctx = DamageContext(
    final_attack=1200.0, skill_multiplier=2.0, damage_type="物理", skill_type="战技", enemy_defense=200.0
)
task = (weapon, (chest, glove, acc_a, acc_b))

N = 10000

# Warm up
for _ in range(500):
    evaluate_task(base_context=ctx, crit_mode="non_crit", task=task)

# Profile: full evaluate_task
t0 = time.perf_counter()
for _ in range(N):
    evaluate_task(base_context=ctx, crit_mode="non_crit", task=task)
t_full = time.perf_counter() - t0
print(f"evaluate_task x {N}: {t_full * 1000:.1f}ms ({N / t_full:.0f}/s)")

# Profile: build_runtime_eval_snapshot only
t0 = time.perf_counter()
for _ in range(N):
    build_runtime_eval_snapshot(task=task)
t_snap = time.perf_counter() - t0
print(f"  build_runtime_eval_snapshot: {t_snap * 1000:.1f}ms ({t_snap / t_full * 100:.0f}%)")

# Profile: build_four_slot_loadout only
t0 = time.perf_counter()
for _ in range(N):
    build_four_slot_loadout(
        chest=chest, gloves=glove, accessory_a=acc_a, accessory_b=acc_b, allow_duplicate_accessory=True
    )
t_loadout = time.perf_counter() - t0
print(f"    build_four_slot_loadout:   {t_loadout * 1000:.1f}ms ({t_loadout / t_full * 100:.0f}%)")

# Profile: aggregate_loadout_modifiers only
loadout = build_four_slot_loadout(
    chest=chest, gloves=glove, accessory_a=acc_a, accessory_b=acc_b, allow_duplicate_accessory=True
)
t0 = time.perf_counter()
for _ in range(N):
    aggregate_loadout_modifiers(loadout)
t_agg = time.perf_counter() - t0
print(f"    aggregate_loadout_modifiers: {t_agg * 1000:.1f}ms ({t_agg / t_full * 100:.0f}%)")

# Measure cache D hit rate
_cache_hits = 0
for i in range(N):
    w2 = WeaponCandidate(name=f"武器{i % 10}", final_attack=1200.0)
    t2 = (weapon, (chest, glove, acc_a, acc_b))
    # build_runtime_eval_snapshot with cache
    r = build_runtime_eval_snapshot(task=t2)
print("Cache test: 10 weapons x same loadout")

print(f"\n综述: 预处理占 {t_snap / t_full * 100:.0f}%, 评估占 {(t_full - t_snap) / t_full * 100:.0f}%")
