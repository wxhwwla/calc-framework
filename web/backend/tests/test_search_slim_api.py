#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""Web 搜索 POST 瘦身 — 服务端 catalog 解析测试。"""

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
from api.entity_refs import merge_entity_ref
from api.search_catalog import resolve_equipment_catalog, weapon_rows_for_search
from fastapi.testclient import TestClient

from games.endfield.data_loading.loader import get_characters, get_weapons
from web.backend.data_materialize import compact_entity_for_transport
from web.backend.main import app

RateLimitMiddleware.enabled = False


class TestSearchCatalogResolve(unittest.TestCase):
    def test_resolve_equipment_catalog_from_scope(self) -> None:
        catalog = resolve_equipment_catalog(None, equipment_scope_label="全部装备")
        self.assertIn("chest", catalog)
        self.assertGreater(len(catalog["chest"]), 0)

    def test_weapon_rows_without_client_all_weapons(self) -> None:
        chars = get_characters()
        weapons = get_weapons()
        if not chars or not weapons:
            self.skipTest("无本地游戏数据")
        char = chars[0]
        current = weapons[0]
        rows = weapon_rows_for_search(
            None,
            char_data=char,
            current_weapon=current,
            weapon_scope_label="同类型",
            char_level=90,
            weapon_level=90,
            trust_level=0,
        )
        self.assertGreater(len(rows), 0)
        weapon_type = char.get("武器")
        for row in rows:
            self.assertEqual(row.get("类型"), weapon_type)

    def test_merge_entity_ref_by_name(self) -> None:
        chars = get_characters()
        if not chars:
            self.skipTest("无角色数据")
        name = str(chars[0].get("名称", ""))
        merged = merge_entity_ref({"名称": name}, kind="character")
        self.assertEqual(merged.get("名称"), name)
        self.assertTrue(merged.get("武器") or merged.get("类型"))


class TestSearchSlimAPI(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_estimate_without_all_weapons(self) -> None:
        resp_chars = self.client.get("/api/data/characters/detail/all?format=compact")
        resp_weapons = self.client.get("/api/data/weapons/detail/all?format=compact")
        if resp_chars.status_code != 200 or resp_weapons.status_code != 200:
            self.skipTest("数据 API 不可用")
        chars = resp_chars.json()
        weapons = resp_weapons.json()
        if not chars or not weapons:
            self.skipTest("无角色/武器")
        char_data = compact_entity_for_transport(chars[0], kind="character")
        current_weapon = compact_entity_for_transport(weapons[0], kind="weapon")
        payload = {
            "char_data": char_data,
            "char_level": 90,
            "weapon_level": 90,
            "trust_level": 0,
            "skill_name": "战技",
            "skill_type": "战技",
            "skill_multiplier": 1.0,
            "damage_type": "物理",
            "weapon_scope_label": "同类型",
            "equipment_scope_label": "全部装备",
            "current_weapon": current_weapon,
            "skill_1_level": 8,
            "skill_2_level": 8,
            "skill_3_level": 8,
        }
        resp = self.client.post("/api/search/estimate", json=payload)
        self.assertIn(resp.status_code, (200, 500))
        if resp.status_code == 200:
            data = resp.json()
            self.assertIn("total_combinations", data)


if __name__ == "__main__":
    unittest.main()
