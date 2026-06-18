#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""DAG 引擎性能基准测试。

依赖: pytest-benchmark (pip install pytest-benchmark)
运行: pytest framework/tests/benchmark/ --benchmark-only
"""

import pytest

from calc_framework.dag.engine import evaluate_graph, topological_sort
from calc_framework.dag.serializer import dag_from_dict


def _large_linear_dag(node_count: int = 100) -> dict:
    """构建 N 节点线性 DAG：const → binary(+) → binary(+) → ..."""
    nodes: dict = {}
    nodes["start"] = {"type": "const", "value": 1.0}
    for i in range(node_count - 2):
        nodes[f"add_{i}"] = {
            "type": "binary",
            "op": "+",
            "lhs": "start" if i == 0 else f"add_{i - 1}",
            "rhs": "start",
        }
    last_key = f"add_{node_count - 3}" if node_count > 2 else "start"
    return {
        "schema_version": "dag-v1",
        "name": f"linear_{node_count}",
        "nodes": nodes,
        "outputs": {"o": {"node": last_key, "label": "o"}},
    }


def _wide_dag(width: int = 20) -> dict:
    """构建宽 DAG：N 条独立链并行求值。"""
    nodes: dict = {}
    outputs: dict = {}
    for i in range(width):
        nodes[f"c_{i}"] = {"type": "const", "value": float(i)}
        nodes[f"r_{i}"] = {"type": "unary", "op": "neg", "input": f"c_{i}"}
        outputs[f"o_{i}"] = {"node": f"r_{i}", "label": str(i)}
    return {
        "schema_version": "dag-v1",
        "name": f"wide_{width}",
        "nodes": nodes,
        "outputs": outputs,
    }


class TestDAGBenchmark:
    """DAG 引擎性能基准。"""

    def test_topological_sort_small(self, benchmark) -> None:
        g = dag_from_dict(_large_linear_dag(50))
        benchmark(topological_sort, g)

    def test_topological_sort_large(self, benchmark) -> None:
        g = dag_from_dict(_large_linear_dag(500))
        benchmark(topological_sort, g)

    def test_evaluate_linear_50(self, benchmark) -> None:
        g = dag_from_dict(_large_linear_dag(50))
        benchmark(evaluate_graph, g, {})

    def test_evaluate_linear_200(self, benchmark) -> None:
        g = dag_from_dict(_large_linear_dag(200))
        benchmark(evaluate_graph, g, {})

    def test_evaluate_wide_20(self, benchmark) -> None:
        g = dag_from_dict(_wide_dag(20))
        benchmark(evaluate_graph, g, {})

    def test_evaluate_wide_100(self, benchmark) -> None:
        g = dag_from_dict(_wide_dag(100))
        benchmark(evaluate_graph, g, {})


class TestEndfieldBenchmark:
    """终末地完整 DAG 基准。"""

    @pytest.mark.skip(reason="TODO: benchmark 上下文不完整（需补全终末地 DAG 所有变量路径）")
    def test_endfield_full_dag_evaluate(self, benchmark) -> None:
        import json
        from pathlib import Path

        from calc_framework.dag.serializer import dag_from_dict

        dag_path = (
            Path(__file__).resolve().parents[3] / "framework" / "src" / "calc_framework" / "configs" / "endfield_full.dag.json"
        )  # noqa: E501
        dag_dict = json.loads(dag_path.read_text(encoding="utf-8"))
        g = dag_from_dict(dag_dict)
        ctx = {
            "character": {"基础攻击": 500, "力量": 100, "敏捷": 80, "智识": 60, "意志": 70},
            "weapon": {"基础攻击": 300},
            "equipment": {"攻击力百分比": 0.3, "暴击率": 0.05},
            "enemy": {"防御": 200, "抗性": 0.1},
            "skill": {"倍率": 2.5, "技能类型": "战技"},
        }
        benchmark(evaluate_graph, g, ctx)
