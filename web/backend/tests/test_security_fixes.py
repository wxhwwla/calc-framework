# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""CodeQL / Dependabot 安全修复回归测试。"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import patch

_REPO = Path(__file__).resolve().parents[3]
_BACKEND = _REPO / "web" / "backend"
for _p in (str(_REPO / "framework" / "src"), str(_REPO), str(_BACKEND)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pytest
from api.admin import _hash_key
from api.internal.safe_http import (
    ValidatedOutboundHost,
    post_chat_completions,
    validate_outbound_api_base,
)
from api.internal.safe_paths import (
    build_contribute_filename,
    resolve_staging_file,
    write_json_to_staging,
)
from fastapi import HTTPException


class TestAdminScryptHash:
    def test_hash_deterministic_with_pepper(self) -> None:
        with patch.dict(os.environ, {"CALC_API_KEY_PEPPER": "test-pepper-32-chars-minimum-value!!"}):
            a = _hash_key("cf_test_key")
            b = _hash_key("cf_test_key")
            assert a == b
            assert len(a) == 128  # 64 bytes hex

    def test_hash_rejects_short_pepper(self) -> None:
        with (
            patch.dict(os.environ, {"CALC_API_KEY_PEPPER": "too-short"}),
            pytest.raises(RuntimeError, match="32"),
        ):
            _hash_key("cf_test_key")

    def test_hash_differs_for_different_keys(self) -> None:
        with patch.dict(os.environ, {"CALC_API_KEY_PEPPER": "test-pepper-32-chars-minimum-value!!"}):
            assert _hash_key("cf_a") != _hash_key("cf_b")


class TestSafePaths:
    def test_build_contribute_filename_safe(self) -> None:
        name = build_contribute_filename("../../etc/passwd")
        assert ".." not in name
        assert name.startswith("contribute_")
        assert name.endswith(".json")

    def test_resolve_staging_rejects_traversal(self, tmp_path: Path) -> None:
        with pytest.raises(HTTPException) as exc:
            resolve_staging_file(tmp_path, "../../../etc/passwd")
        assert exc.value.status_code == 400

    def test_write_json_stays_in_staging(self, tmp_path: Path) -> None:
        filename = build_contribute_filename("测试干员")
        write_json_to_staging(tmp_path, filename, {"名称": "测试干员"})
        written = tmp_path / filename
        assert written.is_file()
        assert written.resolve().is_relative_to(tmp_path.resolve())


class TestSafeHttp:
    def test_rejects_localhost(self) -> None:
        with pytest.raises(HTTPException) as exc:
            validate_outbound_api_base("http://localhost:8080")
        assert exc.value.status_code == 400

    def test_rejects_private_ip(self) -> None:
        with pytest.raises(HTTPException) as exc:
            validate_outbound_api_base("http://192.168.1.1")
        assert exc.value.status_code == 400

    def test_rejects_unknown_path(self) -> None:
        with pytest.raises(HTTPException) as exc:
            validate_outbound_api_base("https://api.example.com/v2")
        assert exc.value.status_code == 400

    def test_openai_v1_url_rebuild(self) -> None:
        with patch("api.internal.safe_http._resolve_hostname", return_value="104.20.22.46"):
            host = validate_outbound_api_base("https://api.openai.com/v1")
        assert host.chat_completions_url() == "https://api.openai.com/v1/chat/completions"
        assert host.resolved_ip == "104.20.22.46"

    def test_empty_path_url_rebuild(self) -> None:
        with patch("api.internal.safe_http._resolve_hostname", return_value="104.20.22.46"):
            host = validate_outbound_api_base("https://api.deepseek.com")
        assert isinstance(host, ValidatedOutboundHost)
        assert host.chat_completions_url() == "https://api.deepseek.com/chat/completions"
        assert host.resolved_ip == "104.20.22.46"


class _RecordingAsyncClient:
    """记录请求参数的假 httpx.AsyncClient。"""

    instances: list[_RecordingAsyncClient] = []

    def __init__(self, **kwargs: object) -> None:
        self.init_kwargs = kwargs
        self.calls: list[tuple[str, dict[str, object]]] = []
        _RecordingAsyncClient.instances.append(self)

    async def __aenter__(self) -> _RecordingAsyncClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        return None

    async def post(self, url: str, **kwargs: object) -> object:
        self.calls.append((url, kwargs))
        return object()


class TestSafeHttpTlsHostname:
    def _run(self, api_base: str) -> tuple[str, dict[str, object], _RecordingAsyncClient]:
        _RecordingAsyncClient.instances.clear()
        with (
            patch("api.internal.safe_http._resolve_hostname", return_value="104.20.22.46"),
            patch("api.internal.safe_http.httpx.AsyncClient", _RecordingAsyncClient),
        ):
            asyncio.run(
                post_chat_completions(
                    api_base,
                    json_body={"model": "test"},
                    headers={"Authorization": "Bearer test"},
                    timeout=10.0,
                )
            )
        client = _RecordingAsyncClient.instances[0]
        url, kwargs = client.calls[0]
        return url, kwargs, client

    def test_https_connects_to_pinned_ip_with_original_sni(self) -> None:
        url, kwargs, client = self._run("https://api.openai.com/v1")

        assert url == "https://104.20.22.46/v1/chat/completions"
        assert kwargs["extensions"] == {"sni_hostname": "api.openai.com"}
        headers = kwargs["headers"]
        assert isinstance(headers, dict)
        assert headers["Host"] == "api.openai.com"
        # 证书校验必须保持开启：通过 SNI 修复，而不是 verify=False
        assert client.init_kwargs.get("verify") is not False

    def test_host_header_does_not_override_caller_headers(self) -> None:
        url, kwargs, _client = self._run("https://api.deepseek.com")

        assert url == "https://104.20.22.46/chat/completions"
        headers = kwargs["headers"]
        assert isinstance(headers, dict)
        assert headers["Authorization"] == "Bearer test"
        assert headers["Host"] == "api.deepseek.com"

    def test_ipv6_pinned_ip_is_bracketed(self) -> None:
        _RecordingAsyncClient.instances.clear()
        with (
            patch(
                "api.internal.safe_http._resolve_hostname",
                return_value="2606:4700:4700::1111",
            ),
            patch("api.internal.safe_http.httpx.AsyncClient", _RecordingAsyncClient),
        ):
            asyncio.run(
                post_chat_completions(
                    "https://api.example.com/v1",
                    json_body={"model": "test"},
                    headers={"Authorization": "Bearer test"},
                    timeout=10.0,
                )
            )

        url, kwargs = _RecordingAsyncClient.instances[0].calls[0]
        assert url == "https://[2606:4700:4700::1111]/v1/chat/completions"
        assert kwargs["extensions"] == {"sni_hostname": "api.example.com"}
