# SPDX-License-Identifier: AGPL-3.0
"""DAG 引擎结构化日志单元测试。"""

from __future__ import annotations

import pytest

from calc_framework.dag.engine import evaluate_graph, topological_sort
from calc_framework.dag.errors import DAGRuntimeError
from calc_framework.dag.serializer import dag_from_dict


def _make_simple_graph():
    return dag_from_dict({
        "schema_version": "dag-v1",
        "name": "测试图",
        "variables": {"a": {"type": "float", "source": "computed"}},
        "nodes": {
            "a_node": {"type": "var", "path": "a"},
            "two": {"type": "const", "value": 2},
            "result": {"type": "binary", "op": "*", "lhs": "a_node", "rhs": "two"},
        },
        "outputs": {"prod": {"node": "result", "label": "乘积"}},
    })


class TestTopologicalSortLogging:
    """拓扑排序日志增强。"""

    def test_info_logs_degree_distribution(self, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(10)  # DEBUG
        g = _make_simple_graph()
        topological_sort(g)
        combined = "\n".join(caplog.messages)
        assert any("节点" in m for m in caplog.messages)

    def test_debug_logs_full_order(self, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(10)
        g = _make_simple_graph()
        topological_sort(g)
        order_msgs = [m for m in caplog.messages if "执行顺序" in m]
        assert len(order_msgs) == 1


class TestNodeTimingLogging:
    """节点求值计时日志。"""

    def test_debug_logs_evaluation_time(self, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(10)
        g = _make_simple_graph()
        evaluate_graph(g, {"a": 5.0})
        timing_msgs = [m for m in caplog.messages if any(x in m for x in ("ms", "耗时", "秒"))]
        assert len(timing_msgs) >= 1

    def test_info_logs_graph_summary(self, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(20)
        g = _make_simple_graph()
        evaluate_graph(g, {"a": 5.0})
        combined = "\n".join(caplog.messages)
        assert "开始 DAG 求值" in combined
        assert "完成" in combined


class TestExceptionContextLogging:
    """异常上下文增强日志。"""

    def test_node_failure_logs_full_context(self, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(40)
        g = dag_from_dict({
            "schema_version": "dag-v1",
            "name": "错误图",
            "variables": {"nonexistent.key": {"type": "float", "source": "computed"}},
            "nodes": {
                "bad": {"type": "var", "path": "nonexistent.key"},
                "two": {"type": "const", "value": 2},
            },
            "outputs": {"x": {"node": "bad", "label": "x"}},
        })
        with pytest.raises(DAGRuntimeError):
            evaluate_graph(g, {})
        combined = "\n".join(caplog.messages)
        assert "bad" in combined or "变量" in combined

    def test_divide_by_zero_logs_operands(self, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(30)
        g = dag_from_dict({
            "schema_version": "dag-v1",
            "name": "除零图",
            "nodes": {
                "one": {"type": "const", "value": 1},
                "zero": {"type": "const", "value": 0},
                "div": {"type": "binary", "op": "/", "lhs": "one", "rhs": "zero"},
            },
            "outputs": {"x": {"node": "div", "label": "x"}},
        })
        with pytest.raises(DAGRuntimeError):
            evaluate_graph(g, {})
        combined = "\n".join(caplog.messages)
        assert "除零" in combined or "ZeroDivision" in combined or "zero" in combined


if __name__ == "__main__":
    pytest.main([__file__])
