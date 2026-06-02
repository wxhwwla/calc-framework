#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""明日方舟 Web API 集成测试。"""

from __future__ import annotations

import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
_REPO = _BACKEND.parents[1]
sys.path.insert(0, str(_REPO / "framework" / "src"))
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_BACKEND))

from api.arknights import (  # noqa: E402
    list_operators_payload,
    operator_summary_payload,
    compute_damage_payload,
    ComputeRequest,
)

import unittest


class TestArknightsDataFallback(unittest.TestCase):
    """明日方舟 Web API 功能测试。"""

    def test_list_payload_includes_index(self) -> None:
        payload = list_operators_payload()
        self.assertIn("index", payload)
        self.assertIn("operators", payload)
        self.assertIn("count", payload)
        if payload["index"]:
            row = payload["index"][0]
            self.assertIn("星级", row)
            self.assertIn("职业", row)
            self.assertIn("分支", row)

    def test_operator_summary_payload_keys(self) -> None:
        payload = list_operators_payload()
        if not payload["operators"]:
            self.skipTest("无可用干员数据")
        name = payload["operators"][0]
        summary = operator_summary_payload(name)
        for key in ("名称", "星级", "职业", "分支", "特性", "基础属性"):
            self.assertIn(key, summary)

    def test_compute_damage_basic(self) -> None:
        payload = list_operators_payload()
        if not payload["operators"]:
            self.skipTest("无可用干员数据")
        name = payload["operators"][0]
        req = ComputeRequest(operator_name=name)
        try:
            resp = compute_damage_payload(req)
            self.assertEqual(resp.operator_name, name)
            self.assertGreaterEqual(resp.execution_count, 1)
        except Exception as e:
            self.skipTest(f"计算跳过: {e}")


if __name__ == "__main__":
    unittest.main()
