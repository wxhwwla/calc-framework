# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""生成器 UI 操作符到引擎协议的契约测试。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
for _path in (str(_REPO), str(_REPO / "framework" / "src"), str(_REPO / "web" / "backend")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from api.admin import RateLimitMiddleware
from fastapi.testclient import TestClient

from web.backend.main import app

RateLimitMiddleware.enabled = False


def test_ui_operation_aliases_generate_real_dag_nodes() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/generator/generate",
        json={
            "template_id": "simple",
            "game_name": "协议测试",
            "variables": [
                {"name": "ATK", "source": "input", "default": 100},
                {"name": "倍率", "source": "input", "default": 2},
            ],
            "formula_steps": [
                {"id": "step1", "op": "multiply", "lhs": "ATK", "rhs": "倍率"},
                {"id": "step2", "op": "cond", "cond": "ATK", "true_val": "step1", "false_val": "倍率"},
            ],
            "outputs": [{"name": "最终伤害", "node": "step2"}],
        },
    )

    assert response.status_code == 200, response.text
    files = response.json()["files"]
    meta = json.loads(files["meta.json"])
    dag = json.loads(files[meta["entry_dag"]])
    assert dag["nodes"]["step1"]["type"] == "binary"
    assert dag["nodes"]["step1"]["op"] == "*"
    assert dag["nodes"]["step2"]["type"] == "condition"
