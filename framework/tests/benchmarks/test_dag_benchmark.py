#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""DAG 引擎性能基准测试。

运行方式::

    pytest framework/tests/benchmarks/ --benchmark-only
    pytest framework/tests/benchmarks/ --benchmark-only --benchmark-json=bench.json

基线（参考值，CI 中对比）：
- card_rpg (10 节点): < 0.05 ms
- endfield_full (51 节点): < 0.5 ms
- 1000 次增量求值: < 100 ms
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_FRAMEWORK = _REPO_ROOT / "framework"
_ADAPTERS = _FRAMEWORK / "adapters"

if str(_FRAMEWORK / "src") not in sys.path:
    sys.path.insert(0, str(_FRAMEWORK / "src"))


# ── 共享 fixture ──────────────────────────────────────


def _load_dag(adapter_name: str, dag_filename: str) -> tuple[dict, dict]:
    """加载适配器的 DAG JSON 和 meta。"""
    adapter_dir = _ADAPTERS / adapter_name
    dag_path = adapter_dir / dag_filename
    if not dag_path.exists():
        dag_path = adapter_dir / "dag" / dag_filename
    dag = json.loads(dag_path.read_text(encoding="utf-8"))
    meta = json.loads((adapter_dir / "meta.json").read_text(encoding="utf-8"))
    return dag, meta


def _build_context(dag: dict) -> dict:
    """从 DAG 变量声明构建最小可用的求值上下文。"""
    ctx: dict[str, dict] = {}
    for var_path, var_def in dag.get("variables", {}).items():
        parts = var_path.split(".", 1)
        section = parts[0]
        field = parts[1] if len(parts) > 1 else var_path
        if section not in ctx:
            ctx[section] = {}
        ctx[section][field] = var_def.get("default", 0)
    return ctx


# ── 基准测试 ──────────────────────────────────────────


class TestDAGSingleEval:
    """单次 DAG 求值性能。"""

    @pytest.fixture(scope="class")
    def card_rpg_dag(self):
        from framework.adapters.card_rpg.functions import clamp

        from calc_framework.dag.sandbox import register_function
        from calc_framework.dag.schema import validate_graph

        register_function("clamp", clamp)
        dag_dict, _ = _load_dag("card_rpg", "card_rpg.dag.json")
        graph = validate_graph(dag_dict)
        return graph, _build_context(dag_dict)

    @pytest.fixture(scope="class")
    def endfield_dag(self):
        from calc_framework.dag.schema import validate_graph

        dag_dict, _ = _load_dag("endfield", "endfield_full.dag.json")
        graph = validate_graph(dag_dict)
        return graph, _build_context(dag_dict)

    def test_bench_card_rpg_single(self, benchmark, card_rpg_dag):
        """card_rpg (10 节点) 单次求值。"""
        from calc_framework.dag.engine import evaluate_graph

        graph, ctx = card_rpg_dag
        result = benchmark(lambda: evaluate_graph(graph, ctx))
        assert len(result.outputs) > 0

    def test_bench_endfield_single(self, benchmark, endfield_dag):
        """endfield (51 节点) 单次求值。"""
        from calc_framework.dag.engine import evaluate_graph

        graph, ctx = endfield_dag
        result = benchmark(lambda: evaluate_graph(graph, ctx))
        assert len(result.outputs) > 0


class TestDAGIncremental:
    """增量求值性能（DAGState 复用）。"""

    @pytest.fixture(scope="class")
    def endfield_dag(self):
        from calc_framework.dag.schema import validate_graph

        dag_dict, _ = _load_dag("endfield", "endfield_full.dag.json")
        graph = validate_graph(dag_dict)
        return graph, _build_context(dag_dict)

    def test_bench_1000_incremental(self, benchmark, endfield_dag):
        """1000 次增量求值（同一上下文），DAGState 复用。"""
        from calc_framework.dag.engine import evaluate_graph
        from calc_framework.dag.state import DAGState

        graph, ctx = endfield_dag

        def run_1000():
            state = DAGState()
            for _ in range(1000):
                evaluate_graph(graph, ctx, dag_state=state)

        benchmark(run_1000)


class TestDAGBlockCache:
    """块级缓存性能。"""

    @pytest.fixture(scope="class")
    def endfield_dag(self):
        from calc_framework.dag.schema import validate_graph

        dag_dict, _ = _load_dag("endfield", "endfield_full.dag.json")
        graph = validate_graph(dag_dict)
        return graph, _build_context(dag_dict)

    def test_bench_cache_miss(self, benchmark, endfield_dag):
        """无缓存（首次求值）。"""
        from calc_framework.dag.engine import evaluate_graph

        graph, ctx = endfield_dag

        def fresh_eval():
            evaluate_graph(graph, ctx)

        benchmark(fresh_eval)

    def test_bench_cache_hit(self, benchmark, endfield_dag):
        """增量求值缓存命中（同一上下文 → 跳过全部计算）。"""
        from calc_framework.dag.engine import evaluate_graph
        from calc_framework.dag.state import DAGState

        graph, ctx = endfield_dag

        # 预热
        state = DAGState()
        evaluate_graph(graph, ctx, dag_state=state)

        def cached_eval():
            evaluate_graph(graph, ctx, dag_state=state)

        benchmark(cached_eval)
