# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""AI 公式响应的完整 JSON 解析契约。"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import pytest

_REPO = Path(__file__).resolve().parents[4]
for _path in (str(_REPO), str(_REPO / "framework" / "src"), str(_REPO / "web" / "backend")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from api.admin import RateLimitMiddleware
from fastapi.testclient import TestClient

from web.backend.main import app

RateLimitMiddleware.enabled = False


def _response(content: str) -> httpx.Response:
    return httpx.Response(
        200,
        request=httpx.Request("POST", "https://example.test/chat/completions"),
        json={"choices": [{"message": {"content": content}}]},
    )


def test_nested_ai_json_keeps_complete_formula() -> None:
    content = """以下是解析结果：
```json
{
  "variables": [{"name": "ATK", "default": 100, "meta": {"unit": "点"}}],
  "formula_steps": [{"id": "step1", "op": "expr", "expr": "atk * rate", "input_map": {"atk": "ATK", "rate": "2"}}],
  "outputs": [{"name": "最终伤害", "node": "step1", "is_primary": true}]
}
```
以上。
"""
    with patch("api.generator.post_chat_completions", new=AsyncMock(return_value=_response(content))):
        response = TestClient(app).post(
            "/api/generator/ai/parse",
            json={"api_key": "sk-test", "formula_description": "攻击力乘倍率"},
        )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["variables"][0]["meta"] == {"unit": "点"}
    assert body["formula_steps"][0]["input_map"] == {"atk": "ATK", "rate": "2"}
    assert body["outputs"][0]["name"] == "最终伤害"


def test_prose_does_not_let_unrelated_json_shadow_formula() -> None:
    content = '说明 {"note": "忽略"}，随后是配方 {"variables": [{"name": "ATK"}], "formula_steps": [], "outputs": []}'
    with patch("api.generator.post_chat_completions", new=AsyncMock(return_value=_response(content))):
        response = TestClient(app).post(
            "/api/generator/ai/parse",
            json={"api_key": "sk-test", "formula_description": "含前置说明"},
        )

    assert response.status_code == 200, response.text
    assert response.json()["variables"] == [{"name": "ATK"}]


@pytest.mark.parametrize(
    "content",
    [
        "没有 JSON",
        "[]",
        '{"variables": [',
        '[{"variables": [], "formula_steps": [], "outputs": []}]',
        '{"recipe": {"variables": [], "formula_steps": [], "outputs": []}, "broken": }',
    ],
)
def test_invalid_ai_json_returns_readable_502(content: str) -> None:
    with patch("api.generator.post_chat_completions", new=AsyncMock(return_value=_response(content))):
        response = TestClient(app).post(
            "/api/generator/ai/parse",
            json={"api_key": "sk-test", "formula_description": "无效响应"},
        )

    assert response.status_code == 502
    assert "JSON" in response.json()["detail"]
