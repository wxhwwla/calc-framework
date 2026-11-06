# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""export_calcpack — 子图与附加 JSON 打包测试。"""

from __future__ import annotations

from pathlib import Path

from calc_framework.ui.viewer_pack_utils import load_calcpack
from tools.designer.exporter import export_calcpack


def _minimal_parts() -> tuple[dict, dict, dict]:
    meta = {"name": "Demo", "schema_version": "dag-v1", "entry_dag": "dag/formula.dag.json"}
    dag = {
        "schema_version": "dag-v1",
        "name": "Demo",
        "variables": {},
        "nodes": {"c": {"type": "const", "value": 1.0}},
        "outputs": {"out": {"node": "c"}},
    }
    layout = {
        "schema_version": "ui-v1",
        "name": "Demo",
        "sections": [{"id": "out", "type": "outputs", "title": "结果", "outputs": ["out"]}],
    }
    return meta, dag, layout


def test_export_includes_subgraphs_and_extra_json(tmp_path: Path) -> None:
    meta, dag, layout = _minimal_parts()
    pack = tmp_path / "demo.calcpack"

    export_calcpack(
        pack,
        meta,
        dag,
        layout,
        subgraphs={"@模拟计算/模拟计算_node_1": {"name": "@模拟计算/模拟计算_node_1"}},
        extra_json={"attr_schema.json": {"attributes": []}},
    )

    loaded = load_calcpack(pack)
    assert "dag/subgraphs/模拟计算_模拟计算_node_1.dag.json" in loaded
    assert loaded["attr_schema.json"] == {"attributes": []}


def test_export_without_extras_keeps_original_layout(tmp_path: Path) -> None:
    meta, dag, layout = _minimal_parts()
    pack = tmp_path / "demo.calcpack"

    export_calcpack(pack, meta, dag, layout)

    loaded = load_calcpack(pack)
    assert set(loaded) == {"meta.json", "dag/formula.dag.json", "ui/layout.json"}
