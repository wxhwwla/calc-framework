#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""DAGService 封装层测试。"""

from pathlib import Pathimport pytestfrom calc_framework.dag.schema import (    BinaryNode,    ConstNode,    DAGGraph,    DAGOutput,    DAGVariable,    VarNode,)class TestDAGService:
    @pytest.fixture
    def simple_dag(self) -> DAGGraph:
        return DAGGraph(
            schema_version="dag-v1",
            name="test",
            variables={"x": DAGVariable(type="float", source="computed")},
            nodes={
                "x_node": VarNode(type="var", path="x"),
                "c2": ConstNode(type="const", value=2),
                "result": BinaryNode(type="binary", op="*", lhs="x_node", rhs="c2"),
            },
            outputs={"y": DAGOutput(node="result")},
        )

    @pytest.fixture
    def fixture_dag_path(self) -> Path:
        return Path(__file__).resolve().parents[1] / "fixtures" / "endfield_attack_chain.dag.json"

    def test_from_dag_graph_evaluates(self, simple_dag):
        from calc_framework.dag.service import DAGService

        svc = DAGService(simple_dag)
        result = svc.evaluate({"x": 5})
        assert result.outputs["y"] == pytest.approx(10.0)

    def test_from_file_loads_and_evaluates(self, fixture_dag_path):
        from calc_framework.dag.service import DAGService

        svc = DAGService.from_file(fixture_dag_path)
        result = svc.evaluate({
            "character": {"基础攻击": 123},
            "weapon": {"基础攻击": 456, "攻击加成": 1.15, "附加攻击": 80},
            "computed": {"能力乘数": 1.12},
        })
        assert result.outputs["最终攻击力"] is not None

    def test_from_file_missing_raises(self, tmp_path):
        from calc_framework.dag.service import DAGService

        bad_path = tmp_path / "nonexistent.dag.json"
        with pytest.raises(FileNotFoundError):
            DAGService.from_file(bad_path)

    def test_evaluate_missing_variable_raises(self, simple_dag):
        from calc_framework.dag.service import DAGService

        svc = DAGService(simple_dag)
        with pytest.raises(Exception):
            svc.evaluate({})

    def test_evaluate_returns_output_keys(self, simple_dag):
        from calc_framework.dag.service import DAGService

        svc = DAGService(simple_dag)
        result = svc.evaluate({"x": 3})
        assert "y" in result.outputs

    def test_from_dict_parses_and_evaluates(self):
        from calc_framework.dag.service import DAGService

        d = {
            "schema_version": "dag-v1",
            "name": "dict-test",
            "variables": {"v": {"type": "float", "source": "computed"}},
            "nodes": {
                "v_node": {"type": "var", "path": "v"},
                "c1": {"type": "const", "value": 1},
                "out": {"type": "binary", "op": "+", "lhs": "v_node", "rhs": "c1"},
            },
            "outputs": {"o": {"node": "out", "label": "output"}},
        }
        svc = DAGService.from_dict(d)
        result = svc.evaluate({"v": 10})
        assert result.outputs["o"] == 11
