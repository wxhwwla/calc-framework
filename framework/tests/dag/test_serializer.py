#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""DAG 序列化（JSON ↔ DAGGraph）单元测试。"""

import jsonimport tempfilefrom pathlib import Pathfrom calc_framework.dag.serializer import dag_from_dict, dag_to_dict, load_dag, save_dag_MINIMAL_DICT: dict = {
    "schema_version": "dag-v1",
    "name": "测试图",
    "nodes": {"c": {"type": "const", "value": 1}},
    "outputs": {"o": {"node": "c", "label": "输出"}},
}

_COMPLEX_DICT: dict = {
    "schema_version": "dag-v1",
    "name": "复杂图",
    "description": "含子图的完整测试",
    "variables": {
        "角色.基础攻击": {"type": "float", "source": "character", "description": "角色基础攻击"},
    },
    "subgraphs": {
        "double": {
            "description": "翻倍",
            "parameters": {"val": {"type": "float"}},
            "nodes": {
                "two": {"type": "const", "value": 2},
                "result": {"type": "binary", "op": "*", "lhs": "val", "rhs": "two"},
            },
            "outputs": {"doubled": {"node": "result", "label": "x2"}},
        },
    },
    "nodes": {
        "atk": {"type": "var", "path": "角色.基础攻击"},
        "doubled_atk": {"type": "call", "subgraph": "double", "bindings": {"val": "atk"}},
        "atk_expr": {"type": "expr", "expr": "x / 100", "inputs": {"x": "atk"}},
    },
    "outputs": {
        "final": {"node": "doubled_atk.doubled", "label": "最终"},
        "expr_out": {"node": "atk_expr", "label": "表达式"},
    },
}


class TestRoundTrip:
    """JSON ↔ DAGGraph 往返一致性。"""

    def test_minimal_round_trip(self) -> None:
        g1 = dag_from_dict(_MINIMAL_DICT)
        d = dag_to_dict(g1)
        g2 = dag_from_dict(d)
        assert g2.name == g1.name
        assert len(g2.nodes) == len(g1.nodes)

    def test_complex_round_trip(self) -> None:
        g1 = dag_from_dict(_COMPLEX_DICT)
        d = dag_to_dict(g1)
        g2 = dag_from_dict(d)
        assert g2.name == g1.name
        assert len(g2.subgraphs) == 1
        assert len(g2.variables) == 1
        assert len(g2.nodes) == 3

    def test_file_round_trip(self) -> None:
        g1 = dag_from_dict(_COMPLEX_DICT)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            save_dag(g1, f.name)
            tmp_path = f.name
        try:
            g2 = load_dag(tmp_path)
            assert g2.name == g1.name
            assert len(g2.subgraphs) == len(g1.subgraphs)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_saved_json_is_readable(self) -> None:
        g = dag_from_dict(_COMPLEX_DICT)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            save_dag(g, f.name)
            tmp_path = f.name
        try:
            text = Path(tmp_path).read_text(encoding="utf-8")
            raw = json.loads(text)
            assert raw["schema_version"] == "dag-v1"
            assert raw["name"] == "复杂图"
        finally:
            Path(tmp_path).unlink(missing_ok=True)
