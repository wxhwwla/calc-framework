#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""导出 evaluate-loadout golden 夹具（Python 基准 → TS/WASM 对照）。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_BACKEND = _REPO / "web" / "backend"
for _p in (str(_REPO), str(_BACKEND)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

GOLDEN_DIR = Path(__file__).resolve().parent / "golden"


def _find_working_payload():
    from api.admin import RateLimitMiddleware
    from api.compute import evaluate_loadout
    from api.loadout_schemas import WebLoadoutBody
    from fastapi.testclient import TestClient

    from web.backend.data_materialize import compact_entity_for_transport
    from web.backend.main import app

    RateLimitMiddleware.enabled = False
    client = TestClient(app)
    chars = client.get("/api/data/characters/detail/all?format=runtime").json()
    weapons = client.get("/api/data/weapons/detail/all?format=runtime").json()
    if not chars or not weapons:
        raise RuntimeError("无可用角色/武器数据")

    last_error: Exception | None = None
    for char in chars:
        for weapon in weapons:
            payload = {
                "char_data": compact_entity_for_transport(char, kind="character"),
                "weapon_data": compact_entity_for_transport(weapon, kind="weapon"),
                "calc_mode": "zone_snapshot",
                "char_level": 90,
                "weapon_level": 90,
                "trust_level": 0,
                "skill_1_level": 8,
                "skill_2_level": 8,
                "skill_3_level": 8,
                "damage_component_mode": "skill_and_abnormal",
                "enemy_params": {
                    "enemy_defense": 100.0,
                    "enemy_resistance": 0.0,
                    "ignore_resistance": 0.0,
                    "imbalance_vulnerability_coeff": 1.3,
                    "is_unbalanced": False,
                    "is_true_damage": False,
                    "combo_stacks": 0,
                    "break_defense_stacks": 0,
                    "attached_effect_multiplier": 1.0,
                    "corrosion_duration_seconds": 15.0,
                },
            }
            try:
                body = WebLoadoutBody(**payload)
                response = evaluate_loadout(body)
                return payload, body, response
            except Exception as exc:
                last_error = exc
                continue
    raise RuntimeError(f"无可用角色/武器组合可求值: {last_error}")


def export_golden() -> Path:
    from api.adapter_assets import get_adapter_dag

    from games.endfield.data_loading.web_loadout_bridge import (
        build_adapter_context_from_loadout,
        build_loadout_state_from_web,
    )

    payload, body, response = _find_working_payload()
    loadout = build_loadout_state_from_web(
        char_data=body.char_data,
        weapon_data=body.weapon_data,
        body=body.to_loadout_dict(),
    )
    context = build_adapter_context_from_loadout(loadout, layout_calc_mode="zone_snapshot")
    dag = get_adapter_dag("endfield")

    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    out = {
        "version": 1,
        "payload": payload,
        "outputs": response.outputs,
        "node_values": response.node_values,
        "execution_order": response.execution_order,
        "context": context,
        "dag_meta": {"name": dag.get("name"), "schema_version": dag.get("schema_version")},
    }
    path = GOLDEN_DIR / "canonical_loadout.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    public_path = _REPO / "web" / "frontend" / "public" / "wasm-golden" / "canonical_loadout.json"
    public_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

    dag_src = _REPO / "framework" / "adapters" / "endfield" / "dag" / "endfield_full.dag.json"
    dag_public = _REPO / "web" / "frontend" / "public" / "endfield-dag.json"
    if dag_src.is_file():
        dag_public.write_text(dag_src.read_text(encoding="utf-8"), encoding="utf-8")
    return path


def main() -> int:
    path = export_golden()
    print(f"[完成] golden 已写入 {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
