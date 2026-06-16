"""Quick search test to verify Python path works."""

import os
import sys
import time

sys.path.insert(0, "games/endfield")
sys.path.insert(0, "framework/src")
sys.path.insert(0, ".")

os.environ["RUST_SEARCH_FALLBACK"] = "1"

from games.endfield.calc.damage.engine import DamageContext
from games.endfield.calc.loadout.in_memory_optimizer import run_enumerated_optimizer_parallel
from games.endfield.calc.loadout.optimizer import OptimizerConfig, WeaponCandidate

weapons = [WeaponCandidate(name=f"w{i}", final_attack=1000.0) for i in range(5)]
chests = [{"名称": f"c{i}", "部位": "护甲", "效果": []} for i in range(5)]
gloves = [{"名称": f"g{i}", "部位": "护手", "效果": []} for i in range(5)]
accs = [{"名称": f"a{i}", "部位": "配件", "效果": []} for i in range(3)]
catalog = {"chest": chests, "gloves": gloves, "accessories": accs}
ctx = DamageContext(
    final_attack=1000.0, skill_multiplier=2.0, damage_type="物理", skill_type="战技", enemy_defense=200.0
)
config = OptimizerConfig(top_n=3, crit_mode="non_crit", sort_equipment_by_priority=False, prune_non_beneficial=False)

print("开始搜索...")
t0 = time.perf_counter()
r, total, processed, cancelled, warns = run_enumerated_optimizer_parallel(
    base_context=ctx,
    weapons=weapons,
    equipment_catalog=catalog,
    config=config,
    max_workers=4,
    parallel_backend="thread",
    batch_size=500,
)
t = time.perf_counter() - t0
print(f"完成: {total} 组合, {t:.2f}s, Top={[f'{s.final_damage:.0f}' for s in r]}")
print("PASS")
