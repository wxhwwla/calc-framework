# SPDX-License-Identifier: AGPL-3.0
"""compute API 异常响应不泄露内部信息。"""

from __future__ import annotations

import os
import sys
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

_REPO = Path(__file__).resolve().parents[3]
_BACKEND = _REPO / "web" / "backend"
for _p in (str(_REPO / "framework" / "src"), str(_REPO), str(_BACKEND)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pytest
from api._errors import CALC_DEBUG_ENV
from api.admin import RateLimitMiddleware
from fastapi.testclient import TestClient

from web.backend.main import app

RateLimitMiddleware.enabled = False

_LEAKY_MSG = "failed at E:\\endfield_damage_calculator\\games\\endfield\\secret.py:418"


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def _clean_debug_env() -> Iterator[None]:
    os.environ.pop(CALC_DEBUG_ENV, None)
    yield
    os.environ.pop(CALC_DEBUG_ENV, None)


class TestComputeErrorSafety:
    def test_evaluate_500_hides_internal_path_when_not_debug(self, client: TestClient) -> None:
        with patch("api.compute._manager") as mock_mgr:
            mock_mgr.load.side_effect = RuntimeError(_LEAKY_MSG)
            resp = client.post(
                "/api/compute/evaluate",
                json={"adapter": "test", "context": {}},
            )
        assert resp.status_code == 500
        detail = resp.json()["detail"]
        assert "endfield_damage_calculator" not in detail
        assert "secret.py" not in detail
        assert detail == "服务器内部错误"

    def test_evaluate_500_shows_detail_in_debug_mode(self, client: TestClient) -> None:
        os.environ[CALC_DEBUG_ENV] = "1"
        with patch("api.compute._manager") as mock_mgr:
            mock_mgr.load.side_effect = RuntimeError(_LEAKY_MSG)
            resp = client.post(
                "/api/compute/evaluate",
                json={"adapter": "test", "context": {}},
            )
        assert resp.status_code == 500
        assert _LEAKY_MSG in resp.json()["detail"]

    def test_evaluate_400_hides_internal_path_when_not_debug(self, client: TestClient) -> None:
        mock_pkg = MagicMock()
        mock_pkg.dag_service.evaluate.side_effect = ValueError(_LEAKY_MSG)
        with patch("api.compute._manager") as mock_mgr:
            mock_mgr.load.return_value = mock_pkg
            resp = client.post(
                "/api/compute/evaluate",
                json={"adapter": "test", "context": {}},
            )
        assert resp.status_code == 400
        detail = resp.json()["detail"]
        assert "secret.py" not in detail
        assert detail == "请求参数或计算数据无效"
