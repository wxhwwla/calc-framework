# SPDX-License-Identifier: AGPL-3.0
"""adapter_assets — 配置包按适配器导出。"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_BACKEND = _REPO / "web" / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from api.adapter_lib.assets import (
    data_entity_summary,
    get_adapter_dag,
    get_adapter_layout,
    get_pack_export_bundle,
)


def test_endfield_layout_and_dag():
    layout = get_adapter_layout("endfield")
    assert isinstance(layout.get("sections"), list)
    assert len(layout["sections"]) > 0

    dag = get_adapter_dag("endfield")
    assert "nodes" in dag or "variables" in dag


def test_fps_has_layout_no_data():
    layout = get_adapter_layout("fps")
    assert layout.get("sections")
    assert data_entity_summary("fps") == []


def test_endfield_pack_bundle():
    bundle = get_pack_export_bundle("endfield")
    assert bundle["adapter_id"] == "endfield"
    assert bundle["meta"]["entry_dag"] == "dag/formula.dag.json"
    assert "characters" in bundle["data_summary"]


def test_arknights_operators_in_bundle():
    bundle = get_pack_export_bundle("arknights")
    assert bundle["adapter_id"] == "arknights"
    if bundle["data_summary"].get("operators", 0) > 0:
        assert len(bundle["data_files"]["operators"]) > 0
