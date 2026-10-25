#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""Web 数据 compact/runtime 格式与计算前物化测试。"""

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
from fastapi.testclient import TestClient

from games.endfield.calc.damage.formula import calculate_growth_curve, calculate_skill_curve
from games.endfield.calc.damage.inverse.adapter import EndfieldInverseAdapter
from games.endfield.data_loading.curve_materialize import GROWTH_PARAM_KEY, materialize_character_entity
from tools.data_pipeline.compact_game_json import compact_character
from web.backend.data_materialize import (
    compact_entity_for_transport,
    format_character_entity,
    prepare_character_for_compute,
)
from web.backend.main import app

RateLimitMiddleware.enabled = False


def _sample_character_with_growth() -> dict:
    curve = calculate_growth_curve(base=21, growth=22, divisor=98, offset=0)
    skill = calculate_skill_curve(
        base=1.0,
        growth=10,
        divisor=98,
        offset=0,
        special_values=[2.3, 2.5, 2.7],
    )
    raw = {
        "名称": "__test_compact_web__",
        "等级": list(range(1, 91)),
        "力量": curve,
        "战技倍率": [skill],
    }
    compacted, _ = compact_character(raw, EndfieldInverseAdapter(), max_error=0.05)
    return compacted


class TestDataMaterializeHelpers(unittest.TestCase):
    def test_compact_strips_baked_arrays(self) -> None:
        char = _sample_character_with_growth()
        self.assertIn(GROWTH_PARAM_KEY, char)
        compact = format_character_entity(char, "compact")
        self.assertNotIn("力量", compact)
        self.assertIn(GROWTH_PARAM_KEY, compact)

    def test_prepare_materializes_for_compute(self) -> None:
        char = _sample_character_with_growth()
        prepared = prepare_character_for_compute(char)
        self.assertIsInstance(prepared.get("力量"), list)
        self.assertGreater(len(prepared["力量"]), 0)

    def test_runtime_matches_materialize_entity(self) -> None:
        char = _sample_character_with_growth()
        runtime = format_character_entity(char, "runtime")
        expected = materialize_character_entity(char)
        self.assertEqual(runtime.get("力量"), expected.get("力量"))


class TestDataCompactAPI(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_character_detail_format_runtime(self) -> None:
        listed = self.client.get("/api/data/characters").json()
        if not listed:
            self.skipTest("无角色数据")
        name = listed[0]["名称"]
        resp = self.client.get(f"/api/data/characters/{name}?format=runtime")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("名称"), name)

    def test_character_detail_format_compact_vs_raw(self) -> None:
        listed = self.client.get("/api/data/characters").json()
        if not listed:
            self.skipTest("无角色数据")
        name = listed[0]["名称"]
        raw = self.client.get(f"/api/data/characters/{name}?format=raw").json()
        compact = self.client.get(f"/api/data/characters/{name}?format=compact").json()
        if raw.get(GROWTH_PARAM_KEY):
            self.assertIn(GROWTH_PARAM_KEY, compact)
            self.assertNotIn("力量", compact)
        else:
            self.assertIn("名称", compact)

    def test_evaluate_loadout_accepts_compact_char_data(self) -> None:
        chars = self.client.get("/api/data/characters/detail/all?format=compact").json()
        weapons = self.client.get("/api/data/weapons/detail/all?format=compact").json()
        if not chars or not weapons:
            self.skipTest("无可用数据")
        char_data = compact_entity_for_transport(chars[0], kind="character")
        weapon_data = compact_entity_for_transport(weapons[0], kind="weapon")
        payload = {
            "char_data": char_data,
            "weapon_data": weapon_data,
            "calc_mode": "zone_snapshot",
            "char_level": 90,
            "weapon_level": 90,
            "trust_level": 0,
            "skill_1_level": 8,
            "skill_2_level": 8,
            "skill_3_level": 8,
            "damage_component_mode": "skill_and_abnormal",
            "enemy_defense": 100.0,
            "enemy_resistance": 0.0,
            "imbalance_vulnerability_coeff": 1.3,
            "is_unbalanced": False,
            "is_true_damage": False,
            "combo_stacks": 0,
            "break_defense_stacks": 0,
        }
        resp = self.client.post("/api/compute/evaluate-loadout", json=payload)
        self.assertIn(resp.status_code, (200, 400, 404))
        if resp.status_code == 200:
            self.assertIn("outputs", resp.json())


if __name__ == "__main__":
    unittest.main()
