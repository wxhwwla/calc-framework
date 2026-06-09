#!/usr/bin/env python3
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

from fastapi.testclient import TestClient

from web.backend.main import app

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
        self.assertIn("adapters_count", data)
        self.assertIn("adapters", data)

    def test_health_lists_adapter_names(self) -> None:
        """健康检查返回适配器显示名列表（非目录 ID）。"""
        resp = self.client.get("/api/health")
        data = resp.json()
        self.assertGreaterEqual(data["adapters_count"], 1)
        names = data["adapters"]
        self.assertIn(ENDFIELD_ADAPTER_NAME, names)


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


if __name__ == "__main__":
    unittest.main()
