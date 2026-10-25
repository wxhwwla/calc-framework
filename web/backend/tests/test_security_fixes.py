# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""CodeQL / Dependabot 安全修复回归测试。"""

from __future__ import annotations

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
from api.internal.safe_http import ValidatedOutboundHost, validate_outbound_api_base
from api.internal.safe_paths import (
    build_contribute_filename,
    resolve_staging_file,
    write_json_to_staging,
)
from fastapi import HTTPException


class TestAdminScryptHash:
    def test_hash_deterministic_with_pepper(self) -> None:
        with patch.dict(os.environ, {"CALC_API_KEY_PEPPER": "test-pepper-32-chars-minimum!!"}):
            a = _hash_key("cf_test_key")
            b = _hash_key("cf_test_key")
            assert a == b
            assert len(a) == 128  # 64 bytes hex

    def test_hash_differs_for_different_keys(self) -> None:
        with patch.dict(os.environ, {"CALC_API_KEY_PEPPER": "test-pepper-32-chars-minimum!!"}):
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
