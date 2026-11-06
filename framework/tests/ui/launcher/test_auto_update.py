# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""启动器 auto_update 模块测试。"""

from __future__ import annotations

import json
import zipfile
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from utils.checksums import sha256_hex

from calc_framework.ui.launcher import auto_update
from calc_framework.ui.launcher.auto_update import (
    _find_launcher_asset,
    _is_newer,
    download_and_replace,
    fetch_latest_release,
)


def _zip_bytes() -> bytes:
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("Game Calc Platform.exe", b"fake exe")
    return buf.getvalue()


@patch("calc_framework.ui.launcher.auto_update._local_exe_version", return_value="0.1.0")
@patch("calc_framework.ui.launcher.auto_update.urlopen")
def test_fetch_latest_release_prefers_launcher_asset(
    mock_urlopen: MagicMock,
    _mock_version: MagicMock,
) -> None:
    payload = {
        "tag_name": "v0.2.0",
        "html_url": "https://github.com/wxhwwla/calc-framework/releases/tag/v0.2.0",
        "body": "notes",
        "assets": [
            {
                "name": "终末地伤害计算器_v0.2.0.zip",
                "size": 100,
                "browser_download_url": "https://github.com/x/old.zip",
            },
            {
                "name": "GameCalcPlatform_v0.2.0.zip",
                "size": 200,
                "browser_download_url": "https://github.com/x/launcher.zip",
            },
            {
                "name": "GameCalcPlatform_v0.2.0.zip.sha256",
                "size": 64,
                "browser_download_url": "https://github.com/x/launcher.zip.sha256",
            },
        ],
    }
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(payload).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    info = fetch_latest_release()
    assert info is not None
    assert info.zip_name == "GameCalcPlatform_v0.2.0.zip"
    assert info.zip_url == "https://github.com/x/launcher.zip"
    assert info.checksum_url == "https://github.com/x/launcher.zip.sha256"
    assert info.is_newer is True


def test_find_launcher_asset() -> None:
    assets = [{"name": "other.zip"}, {"name": "GameCalcPlatform_v1.zip"}]
    found = _find_launcher_asset({"assets": assets})
    assert found is not None
    assert found["name"] == "GameCalcPlatform_v1.zip"


@patch("calc_framework.ui.launcher.auto_update._fetch_expected_sha256", return_value=None)
@patch("calc_framework.ui.launcher.auto_update._download_with_progress")
def test_download_and_replace_rejects_http(
    mock_download: MagicMock,
    _mock_checksum: MagicMock,
    tmp_path: Path,
) -> None:
    exe = tmp_path / "launcher.exe"
    exe.write_bytes(b"old")
    ok = download_and_replace("http://insecure.example/update.zip", exe)
    assert ok is False
    mock_download.assert_not_called()


@patch("calc_framework.ui.launcher.auto_update._fetch_expected_sha256")
@patch("calc_framework.ui.launcher.auto_update._download_with_progress")
def test_download_and_replace_verifies_sha256(
    mock_download: MagicMock,
    mock_expected: MagicMock,
    tmp_path: Path,
) -> None:
    zip_path = tmp_path / "update.zip"
    zip_path.write_bytes(_zip_bytes())
    mock_download.side_effect = lambda url, dest, cb: dest.write_bytes(zip_path.read_bytes())

    mock_expected.return_value = sha256_hex(zip_path)

    exe = tmp_path / "launcher.exe"
    exe.write_bytes(b"old")
    ok = download_and_replace(
        "https://github.com/x/GameCalcPlatform_v1.zip",
        exe,
        checksum_url="https://github.com/x/GameCalcPlatform_v1.zip.sha256",
    )
    assert ok is True
    assert exe.read_bytes() == b"fake exe"


def test_is_newer_prefers_stable_over_prerelease() -> None:
    assert _is_newer("0.7.0", "0.7.0-beta") is True
    assert _is_newer("0.7.0-beta", "0.7.0") is False
    assert _is_newer("0.7.1", "0.7.0-beta") is True


@patch("calc_framework.ui.launcher.auto_update._download_with_progress")
def test_download_and_replace_requires_checksum(
    mock_download: MagicMock,
    tmp_path: Path,
) -> None:
    zip_path = tmp_path / "update.zip"
    zip_path.write_bytes(_zip_bytes())
    mock_download.side_effect = lambda url, dest, cb: dest.write_bytes(zip_path.read_bytes())

    exe = tmp_path / "launcher.exe"
    exe.write_bytes(b"old")

    ok = download_and_replace("https://github.com/x/GameCalcPlatform_v1.zip", exe)

    assert ok is False
    assert exe.read_bytes() == b"old"


@patch("calc_framework.ui.launcher.auto_update._fetch_expected_sha256", return_value=None)
@patch("calc_framework.ui.launcher.auto_update._download_with_progress")
def test_download_and_replace_rejects_unreadable_checksum(
    mock_download: MagicMock,
    _mock_expected: MagicMock,
    tmp_path: Path,
) -> None:
    zip_path = tmp_path / "update.zip"
    zip_path.write_bytes(_zip_bytes())
    mock_download.side_effect = lambda url, dest, cb: dest.write_bytes(zip_path.read_bytes())

    exe = tmp_path / "launcher.exe"
    exe.write_bytes(b"old")

    ok = download_and_replace(
        "https://github.com/x/GameCalcPlatform_v1.zip",
        exe,
        checksum_url="https://github.com/x/GameCalcPlatform_v1.zip.sha256",
    )

    assert ok is False
    assert exe.read_bytes() == b"old"


@patch("calc_framework.ui.launcher.auto_update._fetch_expected_sha256")
@patch("calc_framework.ui.launcher.auto_update._download_with_progress")
def test_download_and_replace_rejects_sibling_prefix_traversal(
    mock_download: MagicMock,
    mock_expected: MagicMock,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    update_root = tmp_path / "gcp_update"
    extract_root = tmp_path / "gcp_extract"
    update_root.mkdir()
    extract_root.mkdir()
    roots = iter([str(update_root), str(extract_root)])
    monkeypatch.setattr(auto_update.tempfile, "mkdtemp", lambda prefix="": next(roots))

    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("../gcp_extract_evil/pwn.exe", b"pwn")
    zip_bytes = buf.getvalue()
    zip_path = tmp_path / "update.zip"
    zip_path.write_bytes(zip_bytes)
    mock_download.side_effect = lambda url, dest, cb: dest.write_bytes(zip_bytes)
    mock_expected.return_value = sha256_hex(zip_path)

    exe = tmp_path / "launcher.exe"
    exe.write_bytes(b"old")

    ok = download_and_replace(
        "https://github.com/x/GameCalcPlatform_v1.zip",
        exe,
        checksum_url="https://github.com/x/GameCalcPlatform_v1.zip.sha256",
    )

    assert ok is False
    assert not (tmp_path / "gcp_extract_evil" / "pwn.exe").exists()
    assert exe.read_bytes() == b"old"
