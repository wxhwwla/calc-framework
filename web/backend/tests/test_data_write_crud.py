# SPDX-License-Identifier: AGPL-3.0
"""数据写接口认证与隔离 CRUD 测试（Phase 2 Step 2.4）。"""

from __future__ import annotations

import json
import sys
from collections.abc import Iterator
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_BACKEND = _REPO / "web" / "backend"
for _p in (str(_REPO / "framework" / "src"), str(_REPO), str(_BACKEND)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pytest  # noqa: I001
from api.admin import RateLimitMiddleware
from api.entity.profiles import EntityDef, ProfileDef, PROFILES
from fastapi.testclient import TestClient

from web.backend.main import app
from web.backend.tests._admin_test_env import admin_headers, install_test_admin_token, remove_test_admin_token

RateLimitMiddleware.enabled = False

_TEST_CHAR = "__pytest_write_crud_char__"


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def _clean_admin_env() -> Iterator[None]:
    remove_test_admin_token()
    yield
    remove_test_admin_token()


@pytest.fixture()
def isolated_endfield_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """将 endfield 三实体 JSON 指向临时目录，避免污染仓库数据。"""
    import api.data as data_mod

    for name in ("characters.json", "weapons.json", "equipments.json"):
        (tmp_path / name).write_text("[]", encoding="utf-8")

    profile = ProfileDef(
        id="endfield",
        label="终末地",
        entities=(
            EntityDef(
                "characters",
                "角色",
                tmp_path / "characters.json",
                ("名称", "类型", "星级", "主能力", "副能力"),
            ),
            EntityDef("weapons", "武器", tmp_path / "weapons.json", ("名称", "类型", "星级")),
            EntityDef("equipments", "装备", tmp_path / "equipments.json", ("名称", "部位", "稀有度")),
        ),
    )
    monkeypatch.setitem(PROFILES, "endfield", profile)
    monkeypatch.setattr(data_mod, "CHARACTERS_PATH", tmp_path / "characters.json")
    monkeypatch.setattr(data_mod, "WEAPONS_PATH", tmp_path / "weapons.json")
    monkeypatch.setattr(data_mod, "EQUIPMENTS_PATH", tmp_path / "equipments.json")
    return tmp_path


class TestDataWriteRequiresAdminToken:
    def test_post_character_without_token_returns_401(self, client: TestClient) -> None:
        install_test_admin_token()
        resp = client.post("/api/data/characters", json={"名称": _TEST_CHAR})
        assert resp.status_code == 401

    def test_post_weapon_without_token_returns_401(self, client: TestClient) -> None:
        install_test_admin_token()
        resp = client.post("/api/data/weapons", json={"名称": "test-wep"})
        assert resp.status_code == 401

    def test_post_equipment_without_token_returns_401(self, client: TestClient) -> None:
        install_test_admin_token()
        resp = client.post("/api/data/equipments", json={"名称": "test-eq"})
        assert resp.status_code == 401

    def test_post_profile_entity_without_token_returns_401(self, client: TestClient) -> None:
        install_test_admin_token()
        resp = client.post(
            "/api/data/profiles/endfield/characters",
            json={"名称": _TEST_CHAR},
        )
        assert resp.status_code == 401


class TestDataWriteCrudWithToken:
    def test_create_update_delete_character(
        self,
        client: TestClient,
        isolated_endfield_data: Path,
    ) -> None:
        install_test_admin_token()
        headers = admin_headers()
        payload = {
            "名称": _TEST_CHAR,
            "类型": "测试",
            "星级": 6,
            "主能力": "力量",
            "副能力": "敏捷",
        }

        create = client.post("/api/data/characters", json=payload, headers=headers)
        assert create.status_code == 200

        chars_path = isolated_endfield_data / "characters.json"
        stored = json.loads(chars_path.read_text(encoding="utf-8"))
        assert any(row.get("名称") == _TEST_CHAR for row in stored)

        update = client.put(
            f"/api/data/characters/{_TEST_CHAR}",
            json={"类型": "更新类型"},
            headers=headers,
        )
        assert update.status_code == 200
        stored = json.loads(chars_path.read_text(encoding="utf-8"))
        row = next(r for r in stored if r.get("名称") == _TEST_CHAR)
        assert row.get("类型") == "更新类型"

        delete = client.delete(f"/api/data/characters/{_TEST_CHAR}", headers=headers)
        assert delete.status_code == 200
        stored = json.loads(chars_path.read_text(encoding="utf-8"))
        assert not any(r.get("名称") == _TEST_CHAR for r in stored)

    def test_create_duplicate_character_returns_409(
        self,
        client: TestClient,
        isolated_endfield_data: Path,
    ) -> None:
        install_test_admin_token()
        headers = admin_headers()
        payload = {"名称": _TEST_CHAR, "类型": "测试", "星级": 6}

        first = client.post("/api/data/characters", json=payload, headers=headers)
        assert first.status_code == 200

        second = client.post("/api/data/characters", json=payload, headers=headers)
        assert second.status_code == 409

    def test_create_character_missing_name_returns_400(
        self,
        client: TestClient,
        isolated_endfield_data: Path,
    ) -> None:
        install_test_admin_token()
        resp = client.post(
            "/api/data/characters",
            json={"类型": "无名称"},
            headers=admin_headers(),
        )
        assert resp.status_code == 400

    def test_create_weapon_with_token(
        self,
        client: TestClient,
        isolated_endfield_data: Path,
    ) -> None:
        install_test_admin_token()
        headers = admin_headers()
        payload = {"名称": "__pytest_weapon__", "类型": "单手剑", "星级": 5}
        resp = client.post("/api/data/weapons", json=payload, headers=headers)
        assert resp.status_code == 200
        stored = json.loads((isolated_endfield_data / "weapons.json").read_text(encoding="utf-8"))
        assert any(row.get("名称") == "__pytest_weapon__" for row in stored)

    def test_validate_data_empty_list(
        self,
        client: TestClient,
        isolated_endfield_data: Path,
    ) -> None:
        resp = client.post(
            "/api/data/validate",
            json={"profile_id": "endfield", "entity_key": "characters"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 0
        assert body["valid"] == 0

    def test_list_profiles_metadata(self, client: TestClient) -> None:
        resp = client.get("/api/data/profiles")
        assert resp.status_code == 200
        ids = [p["id"] for p in resp.json()]
        assert "endfield" in ids
