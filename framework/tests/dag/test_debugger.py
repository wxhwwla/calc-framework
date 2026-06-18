# SPDX-License-Identifier: AGPL-3.0
"""DAG 分步调试器 — 单元测试。"""

from __future__ import annotations

import pytest

from calc_framework.dag.debugger import StepDebugger, StepStatus
from calc_framework.dag.serializer import dag_from_dict

_LINEAR_GRAPH = {
    "schema_version": "dag-v1",
    "name": "线性图",
    "variables": {"a": {"type": "float", "source": "computed", "default": 0}},
    "nodes": {
        "a_node": {"type": "var", "path": "a"},
        "two": {"type": "const", "value": 2},
        "result": {"type": "binary", "op": "*", "lhs": "a_node", "rhs": "two"},
    },
    "outputs": {"prod": {"node": "result", "label": "乘积"}},
}


class TestStepDebugger:
    def test_step_through_linear_graph(self):
        graph = dag_from_dict(_LINEAR_GRAPH)

        debugger = StepDebugger(graph, {"a": 5})

        assert debugger.progress == (0, 3)

        assert not debugger.finished

        r1 = debugger.step()

        assert r1 is not None

        assert r1.node_id == "a_node"

        assert r1.value == 5.0

        assert r1.status == StepStatus.STEPPED

        assert debugger.progress == (1, 3)

        r2 = debugger.step()

        assert r2 is not None

        assert r2.node_id == "two"

        assert r2.value == 2.0

        assert r2.status == StepStatus.STEPPED

        assert debugger.progress == (2, 3)

        r3 = debugger.step()

        assert r3 is not None

        assert r3.node_id == "result"

        assert r3.value == 10.0

        assert r3.status == StepStatus.STEPPED

        assert debugger.progress == (3, 3)

        r4 = debugger.step()

        assert r4 is None

        assert debugger.finished

    def test_peek_returns_next_node(self):
        graph = dag_from_dict(_LINEAR_GRAPH)

        debugger = StepDebugger(graph, {"a": 5})

        assert debugger.peek() == "a_node"

        debugger.step()

        assert debugger.peek() == "two"

        debugger.step()

        assert debugger.peek() == "result"

    def test_peek_when_finished(self):
        graph = dag_from_dict(_LINEAR_GRAPH)

        debugger = StepDebugger(graph, {"a": 5})

        debugger.run_all()

        assert debugger.peek() is None

    def test_run_all_returns_all_results(self):
        graph = dag_from_dict(_LINEAR_GRAPH)

        debugger = StepDebugger(graph, {"a": 5})

        results = debugger.run_all()

        assert len(results) == 3

        assert results[-1].node_id == "result"

        assert results[-1].value == 10.0

        assert debugger.finished

    def test_run_to_specific_node(self):
        graph = dag_from_dict(_LINEAR_GRAPH)

        debugger = StepDebugger(graph, {"a": 5})

        results = debugger.run_to("result")

        assert results[-1].node_id == "result"

        assert len(results) == 3

    def test_run_to_unknown_node_raises(self):
        graph = dag_from_dict(_LINEAR_GRAPH)

        debugger = StepDebugger(graph, {"a": 5})

        with pytest.raises(ValueError, match="不在执行顺序中"):
            debugger.run_to("nonexistent")

    def test_reset_clears_progress(self):
        graph = dag_from_dict(_LINEAR_GRAPH)

        debugger = StepDebugger(graph, {"a": 5})

        debugger.run_all()

        assert debugger.finished

        debugger.reset()

        assert debugger.progress == (0, 3)

        assert not debugger.finished

        assert debugger.node_values == {}

    def test_node_values_accumulate(self):
        graph = dag_from_dict(_LINEAR_GRAPH)

        debugger = StepDebugger(graph, {"a": 5})

        debugger.run_all()

        assert debugger.node_values["a_node"] == 5.0

        assert debugger.node_values["two"] == 2.0

        assert debugger.node_values["result"] == 10.0

    def test_breakpoint_pauses_execution(self):
        graph = dag_from_dict(_LINEAR_GRAPH)

        debugger = StepDebugger(graph, {"a": 5})

        debugger.add_breakpoint("two")

        r1 = debugger.step()

        assert r1.node_id == "a_node"

        assert r1.status == StepStatus.STEPPED

        r2 = debugger.step()

        assert r2.node_id == "two"

        assert r2.status == StepStatus.BREAKPOINT

    def test_remove_breakpoint(self):
        graph = dag_from_dict(_LINEAR_GRAPH)

        debugger = StepDebugger(graph, {"a": 5})

        debugger.add_breakpoint("two")

        debugger.remove_breakpoint("two")

        debugger.run_all()

        assert debugger.finished

    def test_list_breakpoints(self):
        graph = dag_from_dict(_LINEAR_GRAPH)

        debugger = StepDebugger(graph, {"a": 5})

        assert debugger.list_breakpoints() == []

        debugger.add_breakpoint("a_node")

        debugger.add_breakpoint("result")

        assert set(debugger.list_breakpoints()) == {"a_node", "result"}

    def test_run_all_with_breakpoints_stops(self):
        graph = dag_from_dict(_LINEAR_GRAPH)

        debugger = StepDebugger(graph, {"a": 5})

        debugger.add_breakpoint("two")

        results = debugger.run_all()

        assert results[-1].node_id == "two"

        assert results[-1].status == StepStatus.BREAKPOINT

        assert len(results) == 2

    def test_run_to_with_breakpoint(self):
        graph = dag_from_dict(_LINEAR_GRAPH)

        debugger = StepDebugger(graph, {"a": 5})

        debugger.add_breakpoint("two")

        results = debugger.run_to("result")

        assert results[-1].node_id == "two"

        assert results[-1].status == StepStatus.BREAKPOINT

    def test_context_defaults_applied(self):
        graph = dag_from_dict(
            {
                "schema_version": "dag-v1",
                "name": "带默认值的图",
                "variables": {"computed.a": {"type": "float", "source": "computed", "default": 0}},
                "nodes": {
                    "a_node": {"type": "var", "path": "computed.a"},
                    "two": {"type": "const", "value": 2},
                    "result": {"type": "binary", "op": "*", "lhs": "a_node", "rhs": "two"},
                },
                "outputs": {"prod": {"node": "result", "label": "乘积"}},
            }
        )

        debugger = StepDebugger(graph, {})

        debugger.run_all()

        assert debugger.node_values["a_node"] == 0.0

    def test_step_dag_with_subgraph(self):
        graph = dag_from_dict(
            {
                "schema_version": "dag-v1",
                "name": "子图测试",
                "subgraphs": {
                    "double": {
                        "parameters": {"val": {"type": "float"}},
                        "nodes": {
                            "two": {"type": "const", "value": 2},
                            "result": {"type": "binary", "op": "*", "lhs": "val", "rhs": "two"},
                        },
                        "outputs": {"doubled": {"node": "result", "label": "两倍值"}},
                    },
                },
                "nodes": {
                    "in_val": {"type": "const", "value": 5},
                    "call_double": {"type": "call", "subgraph": "double", "bindings": {"val": "in_val"}},
                },
                "outputs": {"main_out": {"node": "call_double.doubled", "label": "结果"}},
            }
        )

        debugger = StepDebugger(graph, {})

        debugger.run_all()

        assert debugger.node_values["call_double.two"] == 2.0

        assert debugger.node_values["call_double.result"] == 10.0

    def test_get_node_info(self):
        graph = dag_from_dict(_LINEAR_GRAPH)

        debugger = StepDebugger(graph, {"a": 5})

        info = debugger.get_node_info("a_node")

        assert info is not None

        assert info.type == "var"

        info2 = debugger.get_node_info("nonexistent")

        assert info2 is None

    def test_outputs_available_after_done(self):
        graph = dag_from_dict(_LINEAR_GRAPH)

        debugger = StepDebugger(graph, {"a": 5})

        debugger.run_all()

        outputs = debugger.outputs

        assert outputs == {"prod": 10.0}
