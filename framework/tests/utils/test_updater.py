# SPDX-License-Identifier: AGPL-3.0
"""自动更新模块测试。"""

from __future__ import annotations

import json
import zipfile
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from utils.updater import (
    GITHUB_OWNER,
    GITHUB_REPO,
    RELEASE_API,
    UpdateInfo,
    _generate_replace_script,
    _get_target_dir,
    check_update,
    download_update,
    extract_and_replace,
    verify_zip,
)

# ── Test fixtures ──────────────────────────────────


@pytest.fixture
def mock_release_data() -> dict:
    return {
        "tag_name": "v0.7.0-beta",
        "published_at": "2026-06-01T00:00:00Z",
        "body": "修复了50个bug\n新增了100个feature",
        "assets": [
            {
                "name": "终末地伤害计算器_v0.7.0-beta.zip",
                "size": 5_242_880,
                "browser_download_url": "https://github.com/wxhwwla/calc-framework/releases/download/v0.7.0-beta/终末地伤害计算器_v0.7.0-beta.zip",
            }
        ],
    }


@pytest.fixture
def mock_http_response() -> bytes:
    """创建一个测试 ZIP 文件内容。"""
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("dummy.txt", "hello world")
    return buf.getvalue()


# ── UpdateInfo tests ──────────────────────────────


class TestUpdateInfo:
    def test_creation(self) -> None:
        info = UpdateInfo(
            latest_version="0.7.0-beta",
            download_url="https://example.com/test.zip",
            asset_name="test.zip",
            asset_size=1024,
            release_notes="Some notes",
        )
        assert info.latest_version == "0.7.0-beta"
        assert info.download_url == "https://example.com/test.zip"
        assert info.asset_size == 1024

    def test_with_published_at(self) -> None:
        info = UpdateInfo(
            latest_version="0.7.0-beta",
            download_url="https://example.com/test.zip",
            asset_name="test.zip",
            asset_size=1024,
            release_notes="Notes",
            published_at="2026-06-01",
        )
        assert info.published_at == "2026-06-01"


# ── check_update tests ───────────────────────────


class TestCheckUpdate:
    @patch("utils.updater.urlopen")
    def test_new_version_found(self, mock_urlopen: MagicMock, mock_release_data: dict) -> None:
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(mock_release_data).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        info = check_update("0.6.0-beta")
        assert info is not None
        assert info.latest_version == "0.7.0-beta"
        assert info.asset_name == "终末地伤害计算器_v0.7.0-beta.zip"

        called_url = mock_urlopen.call_args[0][0].full_url
        assert "releases/latest" in called_url

    @patch("utils.updater.urlopen")
    def test_same_version(self, mock_urlopen: MagicMock, mock_release_data: dict) -> None:
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(mock_release_data).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        info = check_update("0.7.0-beta")
        assert info is None

    @patch("utils.updater.urlopen")
    def test_no_assets(self, mock_urlopen: MagicMock) -> None:
        data = {"tag_name": "v0.7.0-beta", "body": "", "assets": []}
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(data).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        info = check_update("0.6.0-beta")
        assert info is None

    @patch("utils.updater.urlopen")
    def test_api_failure(self, mock_urlopen: MagicMock) -> None:
        from urllib.error import URLError
        mock_urlopen.side_effect = URLError("timeout")

        info = check_update("0.6.0-beta")
        assert info is None


# ── download_update tests ─────────────────────────


class TestDownloadUpdate:
    @patch("utils.updater.urlopen")
    def test_download_with_progress(self, mock_urlopen: MagicMock, mock_http_response: bytes) -> None:
        info = UpdateInfo(
            latest_version="0.7.0-beta",
            download_url="https://example.com/test.zip",
            asset_name="test.zip",
            asset_size=len(mock_http_response),
            release_notes="",
        )

        mock_resp = MagicMock()
        mock_resp.read.side_effect = [mock_http_response[i:i+8] for i in range(0, len(mock_http_response), 8)] + [b""]
        mock_resp.headers = {"content-length": str(len(mock_http_response))}
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        progress_values: list[tuple[int, int]] = []

        def track(d: int, t: int) -> None:
            progress_values.append((d, t))

        path = download_update(info, progress=track)
        assert path.exists()
        assert path.name == "test.zip"
        assert path.stat().st_size == len(mock_http_response)
        assert len(progress_values) > 0
        assert progress_values[-1] == (len(mock_http_response), len(mock_http_response))

        path.unlink(missing_ok=True)


# ── verify_zip tests ──────────────────────────────


class TestVerifyZip:
    def test_valid_zip(self, tmp_path: Path, mock_http_response: bytes) -> None:
        p = tmp_path / "test.zip"
        p.write_bytes(mock_http_response)
        assert verify_zip(p) is True

    def test_invalid_zip(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.zip"
        p.write_bytes(b"this is not a zip file")
        assert verify_zip(p) is False


# ── extract_and_replace tests ─────────────────────


class TestExtractAndReplace:
    def test_extract_to_target(self, tmp_path: Path, mock_http_response: bytes) -> None:
        zip_path = tmp_path / "update.zip"
        zip_path.write_bytes(mock_http_response)

        target = tmp_path / "install"
        success = extract_and_replace(zip_path, target_dir=str(target))
        assert success is True
        assert (target / "dummy.txt").exists()
        assert (target / "dummy.txt").read_text() == "hello world"


# ── Helper tests ──────────────────────────────────


class TestHelpers:
    def test_get_target_dir(self) -> None:
        # Should return the repo root (parent of utils/)
        target = _get_target_dir()
        assert (target / "utils").is_dir()
        assert (target / "main_launcher.py").exists()

    def test_generate_replace_script(self) -> None:
        script = _generate_replace_script(
            Path("C:/temp/source.exe"),
            Path("C:/Program Files/dest.exe"),
        )
        assert "source.exe" in script
        assert "dest.exe" in script
        assert script.startswith("@echo off")

    def test_github_constants(self) -> None:
        assert GITHUB_OWNER == "wxhwwla"
        assert GITHUB_REPO == "calc-framework"
        assert "releases/latest" in RELEASE_API
