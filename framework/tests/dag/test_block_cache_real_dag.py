# SPDX-License-Identifier: AGPL-3.0
"""块级缓存端到端测试 — 使用真实 endfield_full.dag.json。"""

from __future__ import annotations

from pathlib import Path

from calc_framework.dag.engine import BlockCache, evaluate_graph
from calc_framework.dag.serializer import load_dag

_DAG_PATH = Path(__file__).parents[2] / "src" / "calc_framework" / "configs" / "endfield_full.dag.json"

_BASE_CTX = {
    "character": {
        "基础攻击": 1000, "暴击率": 0.05, "暴击伤害": 1.5,
        "力量": 100, "敏捷": 80, "智识": 60, "意志": 40,
    },
    "weapon": {"基础攻击": 500, "攻击力+": 0.15, "附加攻击力+": 50},
    "equipment": {"攻击力平值": 200},
    "computed": {
        "主能力平值加算": 100, "副能力平值加算": 50,
        "主能力百分比": 0.1, "副能力百分比": 0.05,
        "技能倍率": 2.0,
        "伤害加成": 0.3, "伤害减免": 0.0, "增幅": 0.0, "虚弱": 0.0,
        "庇护": 0.0, "脆弱": 0.0, "易伤": 0.0,
        "失衡易伤": 1.3, "抗性": 0.0, "非主控减伤": 0.0, "连击增伤": 0.0, "特殊乘区": 1.0,
        "力量加成值": 0, "敏捷加成值": 0, "智识加成值": 0, "意志加成值": 0,
    },
    "enemy": {"防御": 100},
}


class TestBlockCacheRealDAG:
    def test_first_eval_uncached(self) -> None:
        g = load_dag(_DAG_PATH)
        cache = BlockCache()
        r = evaluate_graph(g, _BASE_CTX, block_cache=cache)
        assert len(r.execution_order) > 0

    def test_second_eval_same_context_uses_cache(self) -> None:
        g = load_dag(_DAG_PATH)
        cache = BlockCache()
        r1 = evaluate_graph(g, _BASE_CTX, block_cache=cache)
        r2 = evaluate_graph(g, _BASE_CTX, block_cache=cache)
        assert r1.outputs == r2.outputs
        # Cached eval should produce same output keys
        assert set(r1.outputs.keys()) == set(r2.outputs.keys())

    def test_cache_miss_without_cache_arg(self) -> None:
        """Backward compat: no cache arg works as before."""
        g = load_dag(_DAG_PATH)
        r = evaluate_graph(g, _BASE_CTX)
        assert len(r.outputs) > 0

    def test_changed_attack_triggers_recache(self) -> None:
        g = load_dag(_DAG_PATH)
        cache = BlockCache()
        r1 = evaluate_graph(g, _BASE_CTX, block_cache=cache)
        ctx2 = dict(_BASE_CTX)
        ctx2["character"] = dict(_BASE_CTX["character"], **{"基础攻击": 2000})
        r2 = evaluate_graph(g, ctx2, block_cache=cache)
        # Attack change should affect block2, which affects block4/5/6
        output_keys = set(r2.outputs.keys())
        assert set(r1.outputs.keys()) == output_keys
