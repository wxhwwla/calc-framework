#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""Web 多段逆推 API 测试。"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_FRAMEWORK_SRC = _REPO / "framework" / "src"
_BACKEND = _REPO / "web" / "backend"
for _p in (str(_FRAMEWORK_SRC), str(_REPO), str(_BACKEND)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import unittest

from api.admin import RateLimitMiddleware
from calc_framework.inverse.curve import GROWTH_PARAM_SEGMENTS_KEY
from fastapi.testclient import TestClient

from games.endfield.calc.damage.formula import calculate_growth_curve
from web.backend.main import app

RateLimitMiddleware.enabled = False


class TestInverseSegmentAPI(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_endfield_attr_90_segment(self) -> None:
        curve = calculate_growth_curve(base=21, growth=22, divisor=98, offset=0)
        resp = self.client.post(
            "/api/data/inverse/segment",
            json={
                "game": "endfield",
                "blueprint_id": "attr_90",
                "segment_key": "attr_90",
                "values": curve,
            },
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["segment_key"], "attr_90")
        self.assertTrue(data["valid"])
        self.assertAlmostEqual(data["base"], 21.0, delta=1.0)

    def test_arknights_e0_hp_segment(self) -> None:
        from calc_framework.inverse.curve import expand_segment_linear

        data = expand_segment_linear(711, 1016, 50)
        resp = self.client.post(
            "/api/data/inverse/segment",
            json={
                "game": "arknights",
                "blueprint_id": "attributes",
                "segment_key": "e0",
                "values": [float(x) for x in data],
                "rarity": 6,
            },
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["segment_key"], "e0")
        self.assertEqual(body["length"], 50)

    def test_inverse_milestones_exusiai(self) -> None:
        operator = {
            "名称": "能天使",
            "星级": 6,
            "属性里程碑": {
                "hp": {"e0_lv1": 711, "e0_max": 1016, "e1_max": 1338, "e2_max": 1673},
                "atk": {"e0_lv1": 217, "e0_max": 305, "e1_max": 437, "e2_max": 540},
            },
            "技能": [
                {
                    "名称": "过载模式",
                    "SP消耗": [50, 48, 46, 44, 42, 40, 38, 36, 34, 30],
                }
            ],
        }
        resp = self.client.post("/api/data/inverse/milestones", json={"operator": operator})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        segments = data["growth_params"].get(GROWTH_PARAM_SEGMENTS_KEY, [])
        self.assertGreater(data["segment_count"], 0)
        self.assertTrue(any(s["key"] == "e0.hp" for s in segments))

    def test_legacy_inverse_attribute(self) -> None:
        curve = calculate_growth_curve(base=10, growth=15, divisor=50, offset=0)
        resp = self.client.post(
            "/api/data/inverse",
            json={"type": "attribute", "values": curve},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("formula", data)
        self.assertTrue(data["valid"])


if __name__ == "__main__":
    unittest.main()
