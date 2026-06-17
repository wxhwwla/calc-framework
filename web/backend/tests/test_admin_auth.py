# SPDX-License-Identifier: AGPL-3.0
"""Admin Token 认证测试（Phase 0 Step 0.1）。"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_BACKEND = _REPO / "web" / "backend"
for _p in (str(_REPO / "framework" / "src"), str(_REPO), str(_BACKEND)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pytest
from api.admin import RateLimitMiddleware
from api.auth import ADMIN_TOKEN_HEADER
from fastapi.testclient import TestClient

from web.backend.main import app
from web.backend.tests._admin_test_env import admin_headers, install_test_admin_token, remove_test_admin_token

RateLimitMiddleware.enabled = False


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def _clean_admin_env() -> None:
    remove_test_admin_token()
    yield
    remove_test_admin_token()


class TestAdminTokenAuth:
    def test_create_key_without_env_returns_503(self, client: TestClient) -> None:
        resp = client.post("/api/admin/keys", json={"name": "t"})
        assert resp.status_code == 503

    def test_create_key_without_header_returns_401(self, client: TestClient) -> None:
        install_test_admin_token()
        resp = client.post("/api/admin/keys", json={"name": "t"})
        assert resp.status_code == 401

    def test_create_key_wrong_token_returns_401(self, client: TestClient) -> None:
        install_test_admin_token()
        resp = client.post(
            "/api/admin/keys",
            json={"name": "t"},
            headers={ADMIN_TOKEN_HEADER: "wrong-token"},
        )
        assert resp.status_code == 401

    def test_create_and_list_keys_with_valid_token(self, client: TestClient) -> None:
        install_test_admin_token()
        headers = admin_headers()
        create = client.post("/api/admin/keys", json={"name": "ci-key"}, headers=headers)
        assert create.status_code == 200
        assert "api_key" in create.json()

        listing = client.get("/api/admin/keys", headers=headers)
        assert listing.status_code == 200
        assert isinstance(listing.json(), list)

    def test_list_keys_without_token_returns_401(self, client: TestClient) -> None:
        install_test_admin_token()
        resp = client.get("/api/admin/keys")
        assert resp.status_code == 401


class TestDataWriteAuth:
    def test_delete_character_without_token_returns_401(self, client: TestClient) -> None:
        install_test_admin_token()
        resp = client.delete("/api/data/characters/NONEXISTENT_NAME_XYZ")
        assert resp.status_code == 401

    def test_delete_character_with_token_returns_404(self, client: TestClient) -> None:
        install_test_admin_token()
        resp = client.delete(
            "/api/data/characters/NONEXISTENT_NAME_XYZ",
            headers=admin_headers(),
        )
        assert resp.status_code == 404

    def test_get_characters_still_public(self, client: TestClient) -> None:
        install_test_admin_token()
        resp = client.get("/api/data/characters")
        assert resp.status_code == 200

    def test_inverse_still_public_without_admin_token(self, client: TestClient) -> None:
        install_test_admin_token()
        resp = client.post(
            "/api/data/inverse",
            json={"type": "linear", "values": [1.0, 2.0, 3.0]},
        )
        assert resp.status_code != 401
