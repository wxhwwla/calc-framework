# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""SPA 深链接回退测试（FastAPI StaticFiles 不处理前端路由）。"""

from __future__ import annotations

import sys
from pathlib import Path

from starlette.applications import Starlette
from starlette.testclient import TestClient

_REPO = Path(__file__).resolve().parents[3]
_BACKEND = _REPO / "web" / "backend"
for _p in (str(_REPO / "framework" / "src"), str(_REPO), str(_BACKEND)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from api.internal.spa_static import SPAStaticFiles


def _build_client(tmp_path: Path, *, with_index: bool = True) -> TestClient:
    """构造挂载根路径的最小 SPA 应用。"""
    if with_index:
        (tmp_path / "index.html").write_text("<!doctype html><div id=root></div>", encoding="utf-8")
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "app.js").write_text("console.log(1)", encoding="utf-8")
    app = Starlette()
    app.mount("/", SPAStaticFiles(directory=str(tmp_path), html=True))
    return TestClient(app)


def test_deep_link_falls_back_to_index(tmp_path: Path) -> None:
    client = _build_client(tmp_path)
    response = client.get("/wjdlglr")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<div id=root>" in response.text


def test_existing_asset_is_served(tmp_path: Path) -> None:
    client = _build_client(tmp_path)
    response = client.get("/assets/app.js")
    assert response.status_code == 200
    assert "console.log(1)" in response.text


def test_missing_asset_still_returns_404(tmp_path: Path) -> None:
    client = _build_client(tmp_path)
    response = client.get("/assets/missing.js")
    assert response.status_code == 404


def test_unknown_api_path_still_returns_404(tmp_path: Path) -> None:
    client = _build_client(tmp_path)
    response = client.get("/api/unknown")
    assert response.status_code == 404


def test_missing_index_returns_404(tmp_path: Path) -> None:
    client = _build_client(tmp_path, with_index=False)
    response = client.get("/wjdlglr")
    assert response.status_code == 404
