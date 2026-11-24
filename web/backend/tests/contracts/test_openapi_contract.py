# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""OpenAPI 契约测试：提交的 schema 必须与 FastAPI app 完全一致。"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
for _path in (_REPO, _REPO / "framework" / "src", _REPO / "web" / "backend"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from tools.quality.contracts import check_openapi
from web.backend.main import app


def test_committed_openapi_contract_matches_app() -> None:
    """路由、方法、参数、请求/响应模型或错误码变化都必须更新契约文件。"""
    expected = check_openapi.load_contract(check_openapi.CONTRACT_PATH)
    actual = check_openapi.contract_from_schema(app.openapi())

    differences = check_openapi.diff_contracts(expected, actual)

    assert not differences, "OpenAPI 契约已漂移，请运行 python tools/quality/check_openapi.py --write：\n" + "\n".join(
        differences[:20]
    )


def test_contract_covers_known_routes() -> None:
    """契约至少覆盖健康检查与数据端点，防止空契约蒙混通过。"""
    contract = check_openapi.contract_from_schema(app.openapi())

    assert "/api/health" in contract["paths"]
    assert any(path.startswith("/api/data/") for path in contract["paths"])
