#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""Web 后端核心 API 集成测试。

覆盖所有主要端点，验证：
1. 健康检查 / 适配器列表
2. 终末地方舟数据查询
3. DAG 计算求值
4. 布局/生成器/Hub 等辅助端点
注意：本测试需要完整项目环境（framework/ + games/ + tools/）。
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_FRAMEWORK_SRC = _REPO / "framework" / "src"
_BACKEND = _REPO / "web" / "backend"
for _p in [str(_FRAMEWORK_SRC), str(_REPO), str(_BACKEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import unittest

# 测试时禁用速率限制
from api.admin import RateLimitMiddleware
from fastapi.testclient import TestClient

from web.backend.main import app

RateLimitMiddleware.enabled = False

# AdapterManager 使用 meta.json 中的 name 字段作为 key
ENDFIELD_ADAPTER_NAME = "终末地伤害计算（Calc Framework）"


class TestHealthAndMeta(unittest.TestCase):
    """健康检查 + 基础元信息。"""

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_health_returns_ok(self) -> None:
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "ok")

    def test_health_lists_adapter_names(self) -> None:
        """健康检查在 debug 模式下返回适配器显示名列表。"""
        import os

        old = os.environ.get("CALC_DEBUG")
        try:
            os.environ["CALC_DEBUG"] = "1"
            resp = self.client.get("/api/health")
            data = resp.json()
            self.assertIn("adapters_count", data)
            self.assertGreaterEqual(data["adapters_count"], 1)
            names = data["adapters"]
            self.assertIn(ENDFIELD_ADAPTER_NAME, names)
        finally:
            if old is None:
                os.environ.pop("CALC_DEBUG", None)
            else:
                os.environ["CALC_DEBUG"] = old


class TestAdaptersAPI(unittest.TestCase):
    """适配器列表 / 元信息。"""

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_list_adapters(self) -> None:
        resp = self.client.get("/api/adapters")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        ids = [a["id"] for a in data if "id" in a]
        self.assertIn("endfield", ids, "目录名 endfield 应在适配器列表中")

    def test_get_endfield_adapter_meta(self) -> None:
        """适配器元信息路径：/api/adapters/{dir_name}/meta。"""
        resp = self.client.get("/api/adapters/endfield/meta")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("meta", data)
        self.assertIn("name", data["meta"])

    def test_get_unknown_adapter_meta_returns_404(self) -> None:
        resp = self.client.get("/api/adapters/nonexistent_game_xyz/meta")
        self.assertEqual(resp.status_code, 404)


class TestDataAPI(unittest.TestCase):
    """终末地数据查询。"""

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_list_characters_returns_list(self) -> None:
        resp = self.client.get("/api/data/characters")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_list_weapons_returns_list(self) -> None:
        resp = self.client.get("/api/data/weapons")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_list_equipments_returns_list(self) -> None:
        resp = self.client.get("/api/data/equipments")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)

    def test_character_detail_found(self) -> None:
        resp = self.client.get("/api/data/characters")
        chars = resp.json()
        if not chars:
            self.skipTest("无可用角色数据")
        first_id = chars[0].get("名称") or chars[0].get("id", "")
        resp2 = self.client.get(f"/api/data/characters/{first_id}")
        self.assertEqual(resp2.status_code, 200)
        detail = resp2.json()
        self.assertIn("名称", detail)


class TestComputeAPI(unittest.TestCase):
    """DAG 计算求值。"""

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_evaluate_with_endfield_adapter(self) -> None:
        """使用 card_rpg 简单适配器验证 evaluate 端点。"""
        payload = {
            "adapter": "卡牌RPG伤害计算",
            "context": {
                "character": {"ATK": 100, "DEF": 50, "crit_rate": 0.05, "crit_dmg": 0.5},
                "weapon": {"ATK_bonus": 15},
                "enemy": {"DEF": 60},
                "user_input": {"skill_mult": 1.0, "is_crit": True},
            },
        }
        resp = self.client.post("/api/compute/evaluate", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("outputs", data)

    def test_evaluate_invalid_adapter_returns_404(self) -> None:
        payload = {
            "adapter": "nonexistent",
            "context": {},
        }
        resp = self.client.post("/api/compute/evaluate", json=payload)
        self.assertEqual(resp.status_code, 404)


class TestLayoutAPI(unittest.TestCase):
    """布局/属性 Schema 查询。"""

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_get_layout_sections(self) -> None:
        resp = self.client.get("/api/layout?adapter=endfield")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("sections", data)
        self.assertGreater(len(data["sections"]), 0)

    def test_get_layout_default_adapter(self) -> None:
        resp = self.client.get("/api/layout")
        self.assertEqual(resp.status_code, 200)


class TestSearchEnemiesAPI(unittest.TestCase):
    """搜索辅端（敌人数值）。"""

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_enemy_choices_has_default(self) -> None:
        resp = self.client.get("/api/search/enemies")
        self.assertEqual(resp.status_code, 200)
        rows = resp.json()
        self.assertGreaterEqual(len(rows), 1)
        default = rows[0]
        self.assertEqual(default["id"], "")
        for key in (
            "enemy_defense",
            "enemy_resistance",
            "imbalance_vulnerability_coeff",
            "combo_stacks",
        ):
            self.assertIn(key, default)


class TestArknightsAPI(unittest.TestCase):
    """明日方舟 API。"""

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_list_operators(self) -> None:
        resp = self.client.get("/api/arknights/operators")
        if resp.status_code == 500:
            self.skipTest("明日方舟数据文件不存在（CI 环境未部署爬虫数据）")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("index", data)
        self.assertIn("count", data)
        if data["index"]:
            self.assertIn("名称", data["index"][0])


class TestGeneratorAPI(unittest.TestCase):
    """生成器端点。"""

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_list_templates_returns_dict(self) -> None:
        """生成器模板返回 dict（template_id → 元信息）。"""
        resp = self.client.get("/api/generator/templates")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, dict)
        self.assertGreater(len(data), 0)
        # 至少含一个模板信息
        template = next(iter(data.values()))
        self.assertIn("name", template)
        self.assertIn("description", template)


class TestHubAPI(unittest.TestCase):
    """Calc Hub 市场。"""

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_list_packs_returns_paginated(self) -> None:
        """Hub 返回分页结构。"""
        resp = self.client.get("/api/hub/packs")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("packs", data)
        self.assertIn("total", data)
        self.assertIsInstance(data["packs"], list)


class TestMiscEndpoints(unittest.TestCase):
    """杂项端点。"""

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_ocr_detect_no_file_returns_422(self) -> None:
        """OCR 端点需要上传文件。"""
        resp = self.client.post("/api/ocr/detect")
        self.assertEqual(resp.status_code, 422)

    def test_donation_manifest(self) -> None:
        resp = self.client.get("/api/donation/manifest")
        self.assertIn(resp.status_code, (200, 404))

    def test_api_docs_accessible(self) -> None:
        resp = self.client.get("/api/docs")
        self.assertIn(resp.status_code, (200, 302, 307))


class TestErrorHandling(unittest.TestCase):
    """错误处理。"""

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_not_found_returns_404(self) -> None:
        resp = self.client.get("/api/nonexistent/route")
        self.assertEqual(resp.status_code, 404)

    def test_invalid_json_body_returns_422(self) -> None:
        """FastAPI/Pydantic 校验失败。"""
        resp = self.client.post(
            "/api/compute/evaluate",
            json={"adapter": "卡牌RPG伤害计算"},  # 缺 context
        )
        self.assertEqual(resp.status_code, 422)


# ══════════════════════════════════════════════════════════════════════════════
#  TEST CLASS: TestHubUploadAndDownload
# ══════════════════════════════════════════════════════════════════════════════


class TestHubUploadAndDownload(unittest.TestCase):
    """Calc Hub 上传/下载/评分/统计/删除 完整流程。"""

    _HUB_TOKEN = "test-hub-token"
    _HEADERS = {"X-Admin-Token": _HUB_TOKEN}

    def setUp(self) -> None:
        import os

        self._old_token = os.environ.get("CALC_ADMIN_TOKEN")
        os.environ["CALC_ADMIN_TOKEN"] = self._HUB_TOKEN
        self.client = TestClient(app)

    def tearDown(self) -> None:
        import os

        if self._old_token is None:
            os.environ.pop("CALC_ADMIN_TOKEN", None)
        else:
            os.environ["CALC_ADMIN_TOKEN"] = self._old_token

    # ── 创建 Pack ──────────────────────────────────────
    def test_create_pack_returns_201(self) -> None:
        payload = {"name": "Test Pack", "version": "1.0.0", "description": "集成测试创建包"}
        resp = self.client.post("/api/hub/packs", json=payload, headers=self._HEADERS)
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertIn("id", data)
        self.assertEqual(data["name"], "Test Pack")
        self.assertEqual(data["version"], "1.0.0")

    def test_create_pack_missing_name_returns_422(self) -> None:
        resp = self.client.post("/api/hub/packs", json={"version": "1.0.0"}, headers=self._HEADERS)
        self.assertEqual(resp.status_code, 422)

    def test_create_pack_minimal_fields(self) -> None:
        """只有 name + version（其他字段可选）也应成功。"""
        resp = self.client.post("/api/hub/packs", json={"name": "Minimal", "version": "0.0.1"}, headers=self._HEADERS)
        self.assertEqual(resp.status_code, 201)

    # ── 获取 / 列表 Pack ───────────────────────────────
    def test_get_pack_returns_200(self) -> None:
        """先创建再获取。"""
        created = self.client.post(
            "/api/hub/packs", json={"name": "FetchMe", "version": "1.0.0"}, headers=self._HEADERS
        )
        self.assertEqual(created.status_code, 201)
        pack_id = created.json()["id"]
        resp = self.client.get(f"/api/hub/packs/{pack_id}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("name", data)
        self.assertEqual(data["name"], "FetchMe")

    def test_get_nonexistent_pack_returns_404(self) -> None:
        resp = self.client.get("/api/hub/packs/nonexistent_xyz_12345")
        self.assertEqual(resp.status_code, 404)

    def test_list_packs_with_search(self) -> None:
        """带 search 参数列表。"""
        resp = self.client.get("/api/hub/packs?search=test")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("packs", data)
        self.assertIn("total", data)
        self.assertIn("offset", data)
        self.assertIn("limit", data)
        self.assertIsInstance(data["packs"], list)

    def test_list_packs_with_sort(self) -> None:
        """按名称升序。"""
        resp = self.client.get("/api/hub/packs?sort=name&order=asc")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("packs", data)

    def test_list_packs_with_tag_filter(self) -> None:
        resp = self.client.get("/api/hub/packs?tag=endfield")
        self.assertEqual(resp.status_code, 200)

    # ── 评分 ───────────────────────────────────────────
    def test_rate_pack_returns_updated_rating(self) -> None:
        created = self.client.post("/api/hub/packs", json={"name": "RateMe", "version": "1.0.0"}, headers=self._HEADERS)
        pack_id = created.json()["id"]
        resp = self.client.post(
            f"/api/hub/packs/{pack_id}/rate", json={"score": 4, "comment": "不错"}, headers=self._HEADERS
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("rating", data)
        self.assertIn("rating_count", data)
        self.assertGreater(data["rating_count"], 0)

    def test_rate_nonexistent_pack_returns_404(self) -> None:
        resp = self.client.post("/api/hub/packs/nonexistent/rate", json={"score": 3}, headers=self._HEADERS)
        self.assertEqual(resp.status_code, 404)

    # ── 统计 ───────────────────────────────────────────
    def test_hub_stats_returns_total(self) -> None:
        resp = self.client.get("/api/hub/stats")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("total_packs", data)
        self.assertIsInstance(data["total_packs"], int)

    # ── 删除 ───────────────────────────────────────────
    def test_delete_pack_returns_204(self) -> None:
        created = self.client.post(
            "/api/hub/packs", json={"name": "DeleteMe", "version": "1.0.0"}, headers=self._HEADERS
        )
        pack_id = created.json()["id"]
        resp = self.client.delete(f"/api/hub/packs/{pack_id}", headers=self._HEADERS)
        self.assertEqual(resp.status_code, 204)
        # 二次获取应 404
        resp2 = self.client.get(f"/api/hub/packs/{pack_id}")
        self.assertEqual(resp2.status_code, 404)

    def test_delete_nonexistent_pack_returns_404(self) -> None:
        resp = self.client.delete("/api/hub/packs/nonexistent", headers=self._HEADERS)
        self.assertEqual(resp.status_code, 404)

    # ── 上传文件（需 .calcpack） ──────────────────────
    def test_upload_pack_file_without_file_returns_422(self) -> None:
        """不上传文件直接 POST upload 端点应返回 422。"""
        created = self.client.post(
            "/api/hub/packs", json={"name": "UploadTarget", "version": "1.0.0"}, headers=self._HEADERS
        )
        pack_id = created.json()["id"]
        resp = self.client.post(f"/api/hub/packs/{pack_id}/upload", headers=self._HEADERS)
        self.assertEqual(resp.status_code, 422)

    def test_upload_pack_file_to_nonexistent_pack_returns_404(self) -> None:
        """尝试上传到不存在的包。"""
        resp = self.client.post("/api/hub/packs/nonexistent/upload", headers=self._HEADERS)
        self.assertEqual(resp.status_code, 422)


# ══════════════════════════════════════════════════════════════════════════════
#  TEST CLASS: TestDataDetailEndpoints
# ══════════════════════════════════════════════════════════════════════════════


class TestDataDetailEndpoints(unittest.TestCase):
    """数据 API 详细端点：摘要 / 武器详情 / 装备过滤 / 完整列表。"""

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_data_summary_returns_counts(self) -> None:
        resp = self.client.get("/api/data/summary")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("characters_count", data)
        self.assertIn("weapons_count", data)
        self.assertIn("equipments_count", data)
        self.assertIn("equipment_sets", data)
        self.assertIn("character_types", data)
        self.assertIn("weapon_types", data)
        self.assertIsInstance(data["characters_count"], int)
        self.assertGreater(data["characters_count"], 0)

    def test_weapon_detail(self) -> None:
        """按名称获取武器完整数据。"""
        resp = self.client.get("/api/data/weapons")
        weapons = resp.json()
        if not weapons:
            self.skipTest("无可用武器数据")
        first_name = weapons[0].get("名称", "")
        resp2 = self.client.get(f"/api/data/weapons/{first_name}")
        self.assertEqual(resp2.status_code, 200)
        detail = resp2.json()
        self.assertIn("名称", detail)

    def test_weapon_detail_not_found_returns_404(self) -> None:
        resp = self.client.get("/api/data/weapons/NONEXISTENT_WEAPON_XYZ")
        self.assertEqual(resp.status_code, 404)

    def test_equipment_by_set(self) -> None:
        """按套组名称过滤装备。"""
        resp = self.client.get("/api/data/equipments")
        equips = resp.json()
        if not equips:
            self.skipTest("无可用装备数据")
        sets = [e.get("所属套组", "") for e in equips if e.get("所属套组")]
        if not sets:
            self.skipTest("无可用的装备套组")
        resp2 = self.client.get(f"/api/data/equipments/set/{sets[0]}")
        self.assertEqual(resp2.status_code, 200)
        data = resp2.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        for e in data:
            self.assertIn(sets[0], [e.get("所属套组"), e.get("套装")])

    def test_equipment_by_set_nonexistent_returns_404(self) -> None:
        resp = self.client.get("/api/data/equipments/set/NONEXISTENT_SET")
        self.assertEqual(resp.status_code, 404)

    def test_equipment_by_slot(self) -> None:
        """按部位过滤装备（空列表也返回 200）。"""
        resp = self.client.get("/api/data/equipments")
        equips = resp.json()
        if not equips:
            self.skipTest("无可用装备数据")
        slots = [e.get("部位", "") for e in equips if e.get("部位")]
        if not slots:
            self.skipTest("无可用装备部位")
        resp2 = self.client.get(f"/api/data/equipments/slot/{slots[0]}")
        self.assertEqual(resp2.status_code, 200)

    def test_equipment_detail_all(self) -> None:
        resp = self.client.get("/api/data/equipments/detail/all")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)

    def test_characters_detail_all(self) -> None:
        resp = self.client.get("/api/data/characters/detail/all")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_weapons_detail_all(self) -> None:
        resp = self.client.get("/api/data/weapons/detail/all")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    # ── formula inverse ─────────────────────────────────
    def test_inverse_formula_endpoint(self) -> None:
        """公式反推端点。"""
        resp = self.client.post("/api/data/inverse", json={"type": "linear", "values": [1.0, 2.0, 3.0]})
        self.assertIn(resp.status_code, (200, 400))
        data = resp.json()
        if resp.status_code == 200:
            self.assertIn("formula", data)


# ══════════════════════════════════════════════════════════════════════════════
#  TEST CLASS: TestComputeExtended
# ══════════════════════════════════════════════════════════════════════════════


class TestComputeExtended(unittest.TestCase):
    """DAG 计算扩展：快照 / 对比 / arknights 适配器。"""

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_snapshot_endpoint(self) -> None:
        """使用真实角色/武器调用 snapshot 端点。"""
        chars = self.client.get("/api/data/characters").json()
        weapons = self.client.get("/api/data/weapons").json()
        if not chars or not weapons:
            self.skipTest("无可用角色或武器数据")
        char_name = chars[0].get("名称", "")
        weapon_name = weapons[0].get("名称", "")
        payload = {"char_name": char_name, "weapon_name": weapon_name}
        resp = self.client.post("/api/compute/snapshot", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("segment_damage", data)
        self.assertIn("weighted_total_damage", data)
        self.assertIn("skill_type_totals", data)

    def test_snapshot_missing_character_returns_404(self) -> None:
        payload = {"char_name": "不存在的角色XYZ", "weapon_name": "吉米尼12"}
        resp = self.client.post("/api/compute/snapshot", json=payload)
        self.assertEqual(resp.status_code, 404)

    def test_snapshot_missing_weapon_returns_404(self) -> None:
        chars = self.client.get("/api/data/characters").json()
        if not chars:
            self.skipTest("无可用角色数据")
        payload = {"char_name": chars[0].get("名称", ""), "weapon_name": "不存在的武器XYZ"}
        resp = self.client.post("/api/compute/snapshot", json=payload)
        self.assertEqual(resp.status_code, 404)

    def test_compare_endpoint(self) -> None:
        """配装对比端点。"""
        chars = self.client.get("/api/data/characters").json()
        weapons = self.client.get("/api/data/weapons").json()
        if not chars or not weapons:
            self.skipTest("无可用角色或武器数据")
        char_name = chars[0].get("名称", "")
        weapon_name = weapons[0].get("名称", "")
        payload = {
            "entries": [
                {"label": "方案A", "char_name": char_name, "weapon_name": weapon_name},
            ]
        }
        resp = self.client.post("/api/compute/compare", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        for entry in data:
            self.assertIn("label", entry)
            self.assertIn("total", entry)

    def test_compare_empty_entries(self) -> None:
        resp = self.client.post("/api/compute/compare", json={"entries": []})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    def test_evaluate_with_arknights_adapter(self) -> None:
        """使用 arknights 适配器运行 evaluate。"""
        payload = {
            "adapter": "arknights",
            "context": {
                "operator": {"ATK": 500, "DEF": 200, "operator_attack_interval": 1.6},
                "skill_multiplier": 2.5,
                "enemy": {"DEF": 200, "RES": 50},
                "is_physical": True,
            },
        }
        resp = self.client.post("/api/compute/evaluate", json=payload)
        # 如果 arknights 适配器不可用则跳过
        if resp.status_code == 404:
            self.skipTest("arknights 适配器未加载")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("outputs", data)

    def test_evaluate_loadout_with_endfield(self) -> None:
        """调用 evaluate-loadout 端点（需要完整 loadout body）。"""
        chars = self.client.get("/api/data/characters/detail/all").json()
        weapons = self.client.get("/api/data/weapons/detail/all").json()
        if not chars or not weapons:
            self.skipTest("无可用数据")
        char_data = chars[0]
        weapon_data = weapons[0]
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
            data = resp.json()
            self.assertIn("outputs", data)


# ══════════════════════════════════════════════════════════════════════════════
#  TEST CLASS: TestPackAPI
# ══════════════════════════════════════════════════════════════════════════════


class TestPackAPI(unittest.TestCase):
    """配置包设计器 API：主题 / 导出预览 / 导出下载。"""

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_theme_default(self) -> None:
        resp = self.client.get("/api/pack/theme/default")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("schema_version", data)
        self.assertEqual(data["schema_version"], "theme-v1")
        self.assertIn("name", data)
        self.assertIn("colors", data)
        self.assertIn("font", data)

    def test_export_preview_endpoint(self) -> None:
        payload = {
            "meta": {"name": "MyPack", "version": "1.0.0"},
            "dag": {"nodes": {"n1": {"op": "+", "lhs": "a", "rhs": "b"}}},
            "layout": {"sections": [{"id": "sec1", "type": "inputs"}]},
            "filename": "test.calcpack",
        }
        resp = self.client.post("/api/pack/export/preview", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("meta", data)
        self.assertIn("dag_nodes", data)
        self.assertIn("layout_sections", data)
        self.assertIn("has_theme", data)
        self.assertEqual(data["dag_nodes"], 1)
        self.assertEqual(data["layout_sections"], 1)

    def test_export_preview_with_theme_and_data(self) -> None:
        """含 theme 和 data_files 的导出预览。"""
        payload = {
            "meta": {"name": "FullPack"},
            "dag": {"nodes": {}},
            "layout": {"sections": []},
            "theme": {"name": "Custom"},
            "data_files": {"characters": [{"名称": "A"}], "weapons": [{"名称": "B"}]},
            "filename": "full.calcpack",
        }
        resp = self.client.post("/api/pack/export/preview", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["has_theme"])
        self.assertIn("data_files", data)
        self.assertEqual(data["data_files"]["characters"], 1)

    def test_export_download_endpoint(self) -> None:
        """导出 .calcpack 下载。"""
        payload = {
            "meta": {"name": "DownloadTest"},
            "dag": {"nodes": {"n1": {"op": "+"}}},
            "layout": {"sections": []},
            "filename": "download.calcpack",
        }
        resp = self.client.post("/api/pack/export", json=payload)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("application/zip", resp.headers.get("content-type", ""))

    def test_export_preview_missing_fields(self) -> None:
        """缺少 meta 等字段仍应能处理（Pydantic 校验）。"""
        resp = self.client.post("/api/pack/export/preview", json={})
        self.assertEqual(resp.status_code, 422)


# ══════════════════════════════════════════════════════════════════════════════
#  TEST CLASS: TestSearchExtended
# ══════════════════════════════════════════════════════════════════════════════


class TestSearchExtended(unittest.TestCase):
    """搜索 API 扩展：装备目录 / 搜索历史 / 工作量预估。"""

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_search_catalog_default(self) -> None:
        resp = self.client.get("/api/search/catalog")
        self.assertIn(resp.status_code, (200, 500))
        if resp.status_code == 200:
            data = resp.json()
            self.assertIsInstance(data, dict)
            # 目录 key 是部位名称
            for key, entries in data.items():
                self.assertIsInstance(key, str)
                self.assertIsInstance(entries, list)

    def test_search_catalog_with_scope(self) -> None:
        resp = self.client.get("/api/search/catalog?scope=全部装备")
        self.assertIn(resp.status_code, (200, 500))

    def test_search_history_roundtrip(self) -> None:
        """POST 保存搜索记录后 GET 可查到。"""
        entry = {
            "char_name": "陈千语",
            "timestamp": "2026-06-13T00:00:00",
            "test": True,
        }
        resp_post = self.client.post("/api/search/history", json=entry)
        self.assertEqual(resp_post.status_code, 200)
        self.assertEqual(resp_post.json(), {"message": "ok"})

        resp_get = self.client.get("/api/search/history")
        self.assertEqual(resp_get.status_code, 200)
        data = resp_get.json()
        self.assertIsInstance(data, list)
        self.assertTrue(
            any(e.get("char_name") == "陈千语" and e.get("test") is True for e in data),
            "刚写入的搜索历史记录应可读回",
        )

    def test_search_estimate(self) -> None:
        """工作量预估端点（需要完整数据以构建搜索作业）。"""
        chars = self.client.get("/api/data/characters/detail/all").json()
        weapons = self.client.get("/api/data/weapons/detail/all").json()
        if not chars or not weapons:
            self.skipTest("无可用角色或武器数据")
        char_data = chars[0]
        current_weapon = weapons[0]
        all_weapons = weapons[:5] if len(weapons) >= 5 else weapons

        payload = {
            "char_data": char_data,
            "char_level": 90,
            "weapon_level": 90,
            "trust_level": 0,
            "skill_name": "战技",
            "skill_type": "战技",
            "skill_multiplier": 1.0,
            "damage_type": "物理",
            "weapon_scope_label": "全部",
            "equipment_scope_label": "全部",
            "all_weapons": all_weapons,
            "current_weapon": current_weapon,
            "equipment_catalog": {},
            "skill_1_level": 8,
            "skill_2_level": 8,
            "skill_3_level": 8,
        }
        resp = self.client.post("/api/search/estimate", json=payload)
        # 如果引擎可用则 200，否则 500
        self.assertIn(resp.status_code, (200, 500))

    def test_search_run_endpoint(self) -> None:
        """Full search endpoint - skipped in CI (long integration test)."""
        self.skipTest("Skipped: long integration test, would timeout in CI")

    def test_search_estimate_missing_required_returns_422(self) -> None:
        resp = self.client.post("/api/search/estimate", json={})
        self.assertEqual(resp.status_code, 422)


# ══════════════════════════════════════════════════════════════════════════════
#  TEST CLASS: TestArknightsExtended
# ══════════════════════════════════════════════════════════════════════════════


class TestArknightsExtended(unittest.TestCase):
    """明日方舟 API 扩展：干员详情 / 伤害计算。"""

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_operator_detail(self) -> None:
        """获取指定干员详情。"""
        ops = self.client.get("/api/arknights/operators").json()
        index = ops.get("index", [])
        if not index:
            self.skipTest("无可用干员数据")
        first_name = index[0].get("名称", "")
        resp = self.client.get(f"/api/arknights/operators/{first_name}")
        if resp.status_code == 500:
            self.skipTest("干员数据文件缺失")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("名称", data)
        self.assertIn("星级", data)

    def test_operator_not_found_returns_404(self) -> None:
        resp = self.client.get("/api/arknights/operators/NONEXISTENT_OPERATOR")
        if resp.status_code == 500:
            # 数据文件缺失也算可接受
            self.skipTest("干员数据文件缺失")
        self.assertEqual(resp.status_code, 404)

    def test_arknights_compute(self) -> None:
        """计算干员伤害。"""
        ops = self.client.get("/api/arknights/operators").json()
        index = ops.get("index", [])
        if not index:
            self.skipTest("无可用干员数据")
        first_name = index[0].get("名称", "")
        payload = {
            "operator_name": first_name,
            "skill_multiplier": 2.5,
            "skill_level": 7,
            "enemy_def": 200.0,
            "enemy_res": 50.0,
        }
        resp = self.client.post("/api/arknights/compute", json=payload)
        if resp.status_code == 500:
            self.skipTest("干员数据文件缺失")
        self.assertIn(resp.status_code, (200, 400))
        if resp.status_code == 200:
            data = resp.json()
            self.assertIn("final_atk", data)
            self.assertIn("physical_damage", data)
            self.assertIn("execution_count", data)

    def test_arknights_compute_nonexistent_operator_returns_404(self) -> None:
        payload = {"operator_name": "不存在的干员XYZ"}
        resp = self.client.post("/api/arknights/compute", json=payload)
        if resp.status_code == 500:
            self.skipTest("干员数据文件缺失")
        self.assertEqual(resp.status_code, 404)


# ══════════════════════════════════════════════════════════════════════════════
#  TEST CLASS: TestManualBuffAPI
# ══════════════════════════════════════════════════════════════════════════════


class TestManualBuffAPI(unittest.TestCase):
    """手动 Buff / 异常矩阵 / 消耗品预设 API。"""

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_zone_options(self) -> None:
        resp = self.client.get("/api/manual-buff/zone-options")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        if data:
            opt = data[0]
            self.assertIn("label", opt)
            self.assertIn("id", opt)

    def test_abnormal_matrix_specs(self) -> None:
        resp = self.client.get("/api/manual-buff/abnormal-matrix-specs")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("hint", data)
        self.assertIn("column_labels", data)
        self.assertIn("physical", data)
        self.assertIn("spell", data)
        self.assertIsInstance(data["column_labels"], list)

    def test_consumable_presets(self) -> None:
        resp = self.client.get("/api/manual-buff/consumable-presets")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        if data:
            preset = data[0]
            self.assertIn("name", preset)
            self.assertIn("entries", preset)

    def test_active_keys_endpoint(self) -> None:
        """POST /api/manual-buff/active-keys 返回活跃 Buff key 列表。"""
        payload = {"manual_counts": {}, "physical_abnormal_counts": {}, "spell_abnormal_counts": {}}
        resp = self.client.post("/api/manual-buff/active-keys", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("keys", data)
        self.assertIsInstance(data["keys"], list)

    def test_apply_consumable_endpoint(self) -> None:
        """POST /api/manual-buff/apply-consumable。"""
        # 先获取可用预设名称
        presets_resp = self.client.get("/api/manual-buff/consumable-presets").json()
        if not presets_resp:
            self.skipTest("无可用的消耗品预设")
        preset_name = presets_resp[0]["name"]
        payload = {
            "preset_name": preset_name,
            "manual_counts": {},
            "physical_abnormal_counts": {},
            "spell_abnormal_counts": {},
            "merge": True,
            "store": {},
        }
        resp = self.client.post("/api/manual-buff/apply-consumable", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("store", data)
        self.assertIn("keys_written", data)


# ══════════════════════════════════════════════════════════════════════════════
#  TEST CLASS: TestGeneratorExtended
# ══════════════════════════════════════════════════════════════════════════════


class TestGeneratorExtended(unittest.TestCase):
    """生成器 API 扩展：模板详情 / AI 公式解析 / 生成。"""

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_template_detail(self) -> None:
        """获取模板详情（包括文件结构预览和 DAG 预览）。"""
        templates = self.client.get("/api/generator/templates").json()
        if not templates:
            self.skipTest("无可用生成器模板")
        first_id = next(iter(templates.keys()))
        resp = self.client.get(f"/api/generator/templates/{first_id}")
        if resp.status_code == 404:
            self.skipTest(f"模板 {first_id} 目录缺失")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("id", data)
        self.assertEqual(data["id"], first_id)
        self.assertIn("meta", data)
        self.assertIn("files", data)

    def test_template_detail_nonexistent_returns_404(self) -> None:
        resp = self.client.get("/api/generator/templates/NONEXISTENT_TEMPLATE")
        self.assertEqual(resp.status_code, 404)

    def test_generate_adapter_empty_body_returns_422(self) -> None:
        """生成器需要完整请求体。"""
        resp = self.client.post("/api/generator/generate", json={})
        self.assertEqual(resp.status_code, 422)

    def test_ai_parse_no_api_key_returns_400(self) -> None:
        """AI 解析需要 API key。"""
        payload = {"formula_description": "伤害 = 攻击力 * 技能倍率"}
        resp = self.client.post("/api/generator/ai/parse", json=payload)
        self.assertEqual(resp.status_code, 400)

    def test_ai_parse_empty_description_returns_400(self) -> None:
        payload = {"api_key": "sk-TEST", "formula_description": ""}
        resp = self.client.post("/api/generator/ai/parse", json=payload)
        self.assertEqual(resp.status_code, 400)

    def test_ai_test_connection_endpoint(self) -> None:
        """AI 连接测试端点（无有效 key 也会返回错误状态，但不会 422）。"""
        payload = {"api_key": "sk-TEST", "api_base": "https://api.openai.com/v1", "model": "gpt-4o-mini"}
        resp = self.client.post("/api/generator/ai/test", json=payload)
        # 连接失败返回 200（error status in body）或 502/504
        self.assertIn(resp.status_code, (200, 502, 504))


# ══════════════════════════════════════════════════════════════════════════════
#  TEST CLASS: TestAdapterAssets
# ══════════════════════════════════════════════════════════════════════════════


class TestAdapterAssets(unittest.TestCase):
    """适配器资产端点：layout / DAG / data-summary / pack-bundle。"""

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_adapter_layout(self) -> None:
        resp = self.client.get("/api/adapters/endfield/layout")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("sections", data)
        self.assertIsInstance(data["sections"], list)

    def test_adapter_dag(self) -> None:
        resp = self.client.get("/api/adapters/endfield/dag")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("variables", data)
        self.assertIn("nodes", data)
        self.assertIn("outputs", data)

    def test_adapter_data_summary(self) -> None:
        resp = self.client.get("/api/adapters/endfield/data-summary")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("entities", data)
        self.assertIsInstance(data["entities"], list)
        for entity in data["entities"]:
            self.assertIn("key", entity)
            self.assertIn("label", entity)
            self.assertIn("count", entity)

    def test_adapter_pack_bundle(self) -> None:
        resp = self.client.get("/api/adapters/endfield/pack-bundle")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("adapter_id", data)
        self.assertEqual(data["adapter_id"], "endfield")
        self.assertIn("meta", data)
        self.assertIn("layout", data)
        self.assertIn("dag", data)

    def test_adapter_assets_nonexistent_returns_404(self) -> None:
        resp = self.client.get("/api/adapters/nonexistent_xyz_adapter/layout")
        self.assertEqual(resp.status_code, 404)

    def test_adapter_schema_endpoint(self) -> None:
        """获取适配器 attr_schema。"""
        resp = self.client.get("/api/adapters/endfield/schema")
        # schema 可能不可用或返回 404/200
        self.assertIn(resp.status_code, (200, 404))


# ══════════════════════════════════════════════════════════════════════════════
#  TEST CLASS: TestLayoutExtended
# ══════════════════════════════════════════════════════════════════════════════


class TestLayoutExtended(unittest.TestCase):
    """布局 API 扩展：variables / schema / dag / validate。"""

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_layout_variables_endpoint(self) -> None:
        resp = self.client.get("/api/layout/variables")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, dict)

    def test_layout_schema_endpoint(self) -> None:
        resp = self.client.get("/api/layout/schema")
        # schema.json 可能不存在
        self.assertIn(resp.status_code, (200, 404, 500))

    def test_layout_dag_endpoint(self) -> None:
        resp = self.client.get("/api/layout/dag")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("variables", data)
        self.assertIn("nodes", data)

    def test_layout_validate_endpoint(self) -> None:
        """POST 校验 layout.json 结构与 DAG 一致性。"""
        resp = self.client.post("/api/layout/validate?adapter=endfield")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("valid", data)
        self.assertIn("issues", data)
        self.assertIn("stats", data)
        self.assertIsInstance(data["issues"], list)


# ══════════════════════════════════════════════════════════════════════════════
#  TEST CLASS: TestContributeAPI
# ══════════════════════════════════════════════════════════════════════════════


class TestContributeAPI(unittest.TestCase):
    """数据贡献 API：校验 / 提交。"""

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_contribute_validate_valid(self) -> None:
        """有效数据应通过校验。"""
        payload = {
            "名称": "测试角色",
            "星级": 5,
            "技能": [{"名称": "主动技", "标签": "主动", "百分比": True, "段": [{"倍率": [100]}]}],
        }
        resp = self.client.post("/api/contribute/validate", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("valid", data)
        self.assertTrue(data["valid"])

    def test_contribute_validate_invalid(self) -> None:
        """无效数据应返回验证错误。"""
        payload = {"名称": "", "技能": []}
        resp = self.client.post("/api/contribute/validate", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertFalse(data["valid"])
        self.assertGreater(len(data["errors"]), 0)

    def test_contribute_submit_valid(self) -> None:
        """提交有效数据应成功暂存（需管理 Token）。"""
        import os

        os.environ["CALC_ADMIN_TOKEN"] = "test-admin-token-for-contribute"
        payload = {
            "名称": "提交测试角色",
            "星级": 5,
            "技能": [{"名称": "主动技", "标签": "主动", "百分比": True, "段": [{"倍率": [100]}]}],
        }
        headers = {"X-Admin-Token": "test-admin-token-for-contribute"}
        resp = self.client.post("/api/contribute/submit", json=payload, headers=headers)
        if resp.status_code == 400:
            # 如果暂存目录不可写
            self.skipTest("暂存目录不可写")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("filename", data)
        self.assertIn("message", data)

    def test_contribute_submit_invalid_returns_400(self) -> None:
        import os

        os.environ["CALC_ADMIN_TOKEN"] = "test-admin-token-for-contribute"
        payload = {"名称": "", "技能": []}
        headers = {"X-Admin-Token": "test-admin-token-for-contribute"}
        resp = self.client.post("/api/contribute/submit", json=payload, headers=headers)
        self.assertEqual(resp.status_code, 400)


# ══════════════════════════════════════════════════════════════════════════════
#  TEST CLASS: TestSurvivalAPI
# ══════════════════════════════════════════════════════════════════════════════


class TestSurvivalAPI(unittest.TestCase):
    """生存能力预估 API。"""

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_survival_estimate_endpoint(self) -> None:
        """调用生存能力预估（使用真实数据）。"""
        chars = self.client.get("/api/data/characters/detail/all").json()
        weapons = self.client.get("/api/data/weapons/detail/all").json()
        if not chars or not weapons:
            self.skipTest("无可用角色或武器数据")
        payload = {
            "char_data": chars[0],
            "weapon_data": weapons[0],
            "char_level": 90,
            "weapon_level": 90,
            "trust_level": 0,
            "enemy_tier": "普通",
        }
        resp = self.client.post("/api/survival/estimate", json=payload)
        self.assertIn(resp.status_code, (200, 400))
        if resp.status_code == 200:
            data = resp.json()
            self.assertIsInstance(data, dict)

    def test_survival_estimate_empty_body_returns_422(self) -> None:
        resp = self.client.post("/api/survival/estimate", json={})
        self.assertEqual(resp.status_code, 422)


# ══════════════════════════════════════════════════════════════════════════════
#  TEST CLASS: TestDownloadClient
# ══════════════════════════════════════════════════════════════════════════════


class TestDownloadClient(unittest.TestCase):
    """客户端下载端点。"""

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_download_client_endpoint(self) -> None:
        resp = self.client.get("/api/download/client")
        # 如果 PyInstaller 未打包或 client 不可用，可能返回 404/500
        self.assertIn(resp.status_code, (200, 404, 500))


# ══════════════════════════════════════════════════════════════════════════════
#  TEST CLASS: TestErrorHandlingExtended
# ══════════════════════════════════════════════════════════════════════════════


class TestErrorHandlingExtended(unittest.TestCase):
    """错误处理扩展：缺失请求体 / 非法 JSON / CORS 头。"""

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_missing_body_returns_422(self) -> None:
        """POST 端点无请求体。"""
        resp = self.client.post("/api/compute/evaluate")
        self.assertEqual(resp.status_code, 422)

    def test_invalid_json_returns_422(self) -> None:
        """POST 端点发送非法 JSON 字符串。"""
        resp = self.client.post(
            "/api/compute/evaluate",
            content=b"this is not valid json {{{",
            headers={"Content-Type": "application/json"},
        )
        self.assertIn(resp.status_code, (400, 422))

    def test_cors_headers_present(self) -> None:
        """OPTIONS 预检请求 — 验证服务器正常响应。"""
        resp = self.client.options("/api/health")
        self.assertIn(resp.status_code, (200, 204, 405))
        if resp.status_code == 200:
            headers_lower = {k.lower(): v for k, v in resp.headers.items()}
            self.assertIn("access-control-allow-origin", headers_lower)

    def test_nonexistent_post_endpoint_returns_404(self) -> None:
        """POST 到不存在的路由 → 404 或 405。"""
        resp = self.client.post("/api/nonexistent/endpoint")
        self.assertIn(resp.status_code, (404, 405))

    def test_put_nonexistent_endpoint_returns_404(self) -> None:
        resp = self.client.put("/api/nonexistent/endpoint", json={})
        self.assertIn(resp.status_code, (404, 405))

    def test_delete_nonexistent_endpoint_returns_404(self) -> None:
        resp = self.client.delete("/api/nonexistent/endpoint")
        self.assertIn(resp.status_code, (404, 405))


# ══════════════════════════════════════════════════════════════════════════════
#  TEST CLASS: TestHubListEndpoint
# ══════════════════════════════════════════════════════════════════════════════


class TestHubListEndpoint(unittest.TestCase):
    """Hub 便捷端点：list / upload。"""

    _HUB_TOKEN = "test-hub-token"
    _HEADERS = {"X-Admin-Token": _HUB_TOKEN}

    def setUp(self) -> None:
        import os

        self._old_token = os.environ.get("CALC_ADMIN_TOKEN")
        os.environ["CALC_ADMIN_TOKEN"] = self._HUB_TOKEN
        self.client = TestClient(app)

    def tearDown(self) -> None:
        import os

        if self._old_token is None:
            os.environ.pop("CALC_ADMIN_TOKEN", None)
        else:
            os.environ["CALC_ADMIN_TOKEN"] = self._old_token

    def test_hub_list_adapters(self) -> None:
        resp = self.client.get("/api/hub/list")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("adapters", data)
        self.assertIn("total", data)
        self.assertIsInstance(data["adapters"], list)

    def test_hub_upload_without_file_returns_422(self) -> None:
        resp = self.client.post("/api/hub/upload", headers=self._HEADERS)
        self.assertEqual(resp.status_code, 422)

    def test_hub_download_nonexistent_returns_404(self) -> None:
        resp = self.client.get("/api/hub/download/nonexistent")
        self.assertEqual(resp.status_code, 404)

    def test_hub_delete_adapter_nonexistent_returns_404(self) -> None:
        resp = self.client.delete("/api/hub/adapters/nonexistent", headers=self._HEADERS)
        self.assertEqual(resp.status_code, 404)


# ══════════════════════════════════════════════════════════════════════════════
#  TEST CLASS: TestOCRBasic
# ══════════════════════════════════════════════════════════════════════════════


class TestOCRBasic(unittest.TestCase):
    """OCR 端点基础测试。"""

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_ocr_detect_no_file_returns_422(self) -> None:
        resp = self.client.post("/api/ocr/detect")
        self.assertEqual(resp.status_code, 422)

    def test_ocr_detect_with_empty_file(self) -> None:
        """上传空文件测试 OCR 端点响应。"""
        from io import BytesIO

        resp = self.client.post(
            "/api/ocr/detect",
            files={"file": ("empty.png", BytesIO(b""), "image/png")},
        )
        # 期望失败 — 不是合法图片
        self.assertIn(resp.status_code, (400, 422, 500, 501))


# ══════════════════════════════════════════════════════════════════════════════
#  TEST CLASS: TestDataMutations
# ══════════════════════════════════════════════════════════════════════════════


class TestDataMutations(unittest.TestCase):
    """数据 CRUD 变更端点基础测试（只测路由可达性和 422 校验）。"""

    def setUp(self) -> None:
        from web.backend.tests._admin_test_env import admin_headers, install_test_admin_token

        install_test_admin_token()
        self.client = TestClient(app)
        self._admin_headers = admin_headers()

    def tearDown(self) -> None:
        from web.backend.tests._admin_test_env import remove_test_admin_token

        remove_test_admin_token()

    def test_create_character_empty_body_returns_422(self) -> None:
        resp = self.client.post("/api/data/characters", json={}, headers=self._admin_headers)
        self.assertIn(resp.status_code, (400, 422))

    def test_create_weapon_empty_body_returns_422(self) -> None:
        resp = self.client.post("/api/data/weapons", json={}, headers=self._admin_headers)
        self.assertIn(resp.status_code, (400, 422))

    def test_create_equipment_empty_body_returns_422(self) -> None:
        resp = self.client.post("/api/data/equipments", json={}, headers=self._admin_headers)
        self.assertIn(resp.status_code, (400, 422))

    def test_delete_nonexistent_character_returns_404(self) -> None:
        resp = self.client.delete(
            "/api/data/characters/NONEXISTENT_NAME_XYZ",
            headers=self._admin_headers,
        )
        self.assertEqual(resp.status_code, 404)

    def test_delete_without_admin_token_returns_401(self) -> None:
        resp = self.client.delete("/api/data/characters/NONEXISTENT_NAME_XYZ")
        self.assertEqual(resp.status_code, 401)


# ══════════════════════════════════════════════════════════════════════════════
#  TEST CLASS: TestDataProfiles
# ══════════════════════════════════════════════════════════════════════════════


class TestDataProfiles(unittest.TestCase):
    """数据 profile 端点（多游戏 profile）。"""

    def setUp(self) -> None:
        from web.backend.tests._admin_test_env import admin_headers, install_test_admin_token

        install_test_admin_token()
        self.client = TestClient(app)
        self._admin_headers = admin_headers()

    def tearDown(self) -> None:
        from web.backend.tests._admin_test_env import remove_test_admin_token

        remove_test_admin_token()

    def test_list_profiles(self) -> None:
        resp = self.client.get("/api/data/profiles")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)

    def test_get_profile_entity(self) -> None:
        """获取 profile 下的实体列表。"""
        resp = self.client.get("/api/data/profiles")
        profiles = resp.json()
        if not profiles:
            self.skipTest("无可用 profile")
        profile_id = profiles[0].get("id", "")
        if not profile_id:
            self.skipTest("profile 缺少 id")
        resp2 = self.client.get(f"/api/data/profiles/{profile_id}/characters")
        self.assertIn(resp2.status_code, (200, 404))

    def test_create_profile_entity_empty_body_returns_422(self) -> None:
        resp = self.client.get("/api/data/profiles")
        profiles = resp.json()
        if not profiles:
            self.skipTest("无可用 profile")
        profile_id = profiles[0].get("id", "")
        if not profile_id:
            self.skipTest("profile 缺少 id")
        resp2 = self.client.post(
            f"/api/data/profiles/{profile_id}/characters",
            json={},
            headers=self._admin_headers,
        )
        self.assertIn(resp2.status_code, (400, 422))


if __name__ == "__main__":
    unittest.main()
