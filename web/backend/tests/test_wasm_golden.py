#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""WASM golden 回归 — Python 基准 + 曲线物化一致性。"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_FRAMEWORK_SRC = _REPO / "framework" / "src"
_BACKEND = _REPO / "web" / "backend"
for _p in (str(_FRAMEWORK_SRC), str(_REPO), str(_BACKEND)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

_GOLDEN = _REPO / "web" / "wasm" / "golden" / "canonical_loadout.json"


class TestWasmGolden(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not _GOLDEN.is_file():
            subprocess.run(
                [sys.executable, str(_REPO / "web" / "wasm" / "export_loadout_golden.py")],
                cwd=str(_REPO),
                check=True,
            )
        cls.golden = json.loads(_GOLDEN.read_text(encoding="utf-8"))

    def test_golden_outputs_non_empty(self) -> None:
        outputs = self.golden.get("outputs") or {}
        self.assertGreater(len(outputs), 0)

    def test_python_re_eval_matches_golden(self) -> None:
        from api.admin import RateLimitMiddleware
        from fastapi.testclient import TestClient

        from web.backend.main import app

        RateLimitMiddleware.enabled = False
        client = TestClient(app)
        payload = self.golden["payload"]
        resp = client.post("/api/compute/evaluate-loadout", json=payload)
        self.assertEqual(resp.status_code, 200, resp.text)
        fresh = resp.json()["outputs"]
        for key, expected in self.golden["outputs"].items():
            self.assertIn(key, fresh)
            self.assertAlmostEqual(float(fresh[key]), float(expected), places=4, msg=key)

    def test_compact_weapon_materialize_matches_context(self) -> None:
        from web.backend.data_materialize import prepare_weapon_for_compute

        payload = self.golden["payload"]
        weapon = prepare_weapon_for_compute(payload["weapon_data"])
        level = int(payload["weapon_level"])
        idx = max(0, min(len(weapon.get("基础攻击力", [])) - 1, level - 1))
        baked = float(weapon["基础攻击力"][idx])
        ctx_weapon = (self.golden.get("context") or {}).get("weapon") or {}
        if "基础攻击" in ctx_weapon:
            self.assertAlmostEqual(baked, float(ctx_weapon["基础攻击"]), delta=0.1)

    def test_loadout_context_endpoint(self) -> None:
        from api.admin import RateLimitMiddleware
        from fastapi.testclient import TestClient

        from web.backend.main import app

        RateLimitMiddleware.enabled = False
        client = TestClient(app)
        payload = self.golden["payload"]
        resp = client.post("/api/compute/loadout-context", json=payload)
        self.assertEqual(resp.status_code, 200, resp.text)
        ctx = resp.json().get("context") or {}
        golden_ctx = self.golden.get("context") or {}
        weapon = ctx.get("weapon") or {}
        golden_weapon = golden_ctx.get("weapon") or {}
        if "基础攻击" in golden_weapon:
            self.assertAlmostEqual(
                float(weapon["基础攻击"]),
                float(golden_weapon["基础攻击"]),
                delta=0.1,
            )

    def test_python_dag_eval_matches_golden(self) -> None:
        from api.adapter_lib.assets import get_adapter_dag
        from calc_framework.dag.engine import evaluate_graph
        from calc_framework.dag.graph_types import validate_graph

        dag_dict = get_adapter_dag("endfield")
        graph = validate_graph(dag_dict)
        ctx = self.golden.get("context") or {}
        result = evaluate_graph(graph, ctx)
        for key, expected in self.golden["outputs"].items():
            self.assertIn(key, result.outputs)
            self.assertAlmostEqual(float(result.outputs[key]), float(expected), places=4, msg=key)

    def test_loadout_context_computed_matches_golden(self) -> None:
        from api.search_lib.loadout_schemas import WebLoadoutBody

        from games.endfield.data_loading.web_loadout_bridge import (
            build_adapter_context_from_loadout,
            build_loadout_state_from_web,
        )

        body = WebLoadoutBody(**self.golden["payload"])
        loadout = build_loadout_state_from_web(
            char_data=body.char_data,
            weapon_data=body.weapon_data,
            body=body.to_loadout_dict(),
        )
        ctx = build_adapter_context_from_loadout(loadout, layout_calc_mode="zone_snapshot")
        golden_ctx = self.golden.get("context") or {}
        for section in ("character", "weapon", "computed"):
            for key, expected in (golden_ctx.get(section) or {}).items():
                actual = (ctx.get(section) or {}).get(key)
                if actual is None:
                    continue
                if isinstance(expected, int | float) and isinstance(actual, int | float):
                    self.assertAlmostEqual(float(actual), float(expected), places=3, msg=f"{section}.{key}")
                else:
                    self.assertEqual(actual, expected, f"{section}.{key}")

    def test_node_verify_script(self) -> None:
        script = _REPO / "web" / "wasm" / "verify_golden.mjs"
        if not script.is_file():
            self.skipTest("verify_golden.mjs 不存在")
        proc = subprocess.run(
            ["node", str(script)],
            cwd=str(_REPO),
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)


if __name__ == "__main__":
    unittest.main()
