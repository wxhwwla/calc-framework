#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""AI 推荐契约测试 — 确保不再把基线估算伪装成「最优 TopN」。

审查项 R-02：``/api/ai/recommend`` 没有执行真实搜索时，不得返回名为
``top_results`` 的伪推荐，也不得输出伪组合数。只允许返回
「候选数量 + 固定参数基线 + 明确免责声明」。
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_FRAMEWORK_SRC = _REPO / "framework" / "src"
_BACKEND = _REPO / "web" / "backend"
for _p in [str(_FRAMEWORK_SRC), str(_REPO), str(_BACKEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from api.admin import RateLimitMiddleware
from fastapi.testclient import TestClient

from web.backend.main import app

RateLimitMiddleware.enabled = False

_CHARS_PATH = _REPO / "games" / "endfield" / "data" / "characters.json"


def _first_character_name() -> str:
    data = json.loads(_CHARS_PATH.read_text(encoding="utf-8"))
    return data[0]["名称"]


class TestAiRecommendContract(unittest.TestCase):
    """AI 推荐响应必须如实描述能力边界。"""

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_recommend_returns_baseline_not_pseudo_top_results(self) -> None:
        resp = self.client.post(
            "/api/ai/recommend",
            json={"character_name": _first_character_name(), "query": "暴击流怎么配"},
        )
        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()

        self.assertNotIn("top_results", data)
        self.assertNotIn("total_combinations", data)
        self.assertIn("baseline_result", data)
        self.assertIn("candidate_weapons", data)
        self.assertIn("candidate_equipments", data)
        self.assertGreaterEqual(data["candidate_weapons"], 1)
        self.assertGreaterEqual(data["candidate_equipments"], 1)
        self.assertIn("不是最优搜索", data["notice"])
        self.assertIn("基线", data["notice"])

        baseline = data["baseline_result"]
        if baseline is not None:
            self.assertIn("label", baseline)
            self.assertIn("damage", baseline)
            self.assertIn("非当前配装", baseline["note"])

    def test_recommend_unknown_character_returns_404(self) -> None:
        resp = self.client.post(
            "/api/ai/recommend",
            json={"character_name": "不存在的角色XYZ", "query": "测试"},
        )
        self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()
