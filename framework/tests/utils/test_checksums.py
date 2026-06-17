# SPDX-License-Identifier: AGPL-3.0
"""checksums 模块测试。"""

from __future__ import annotations

from pathlib import Path

from utils.checksums import (
    checksum_asset_name,
    find_checksum_in_assets,
    parse_sha256_sidecar_text,
    require_https_url,
    sha256_hex,
    write_sha256_sidecar,
)


def test_require_https_url() -> None:
    assert require_https_url("https://github.com/wxhwwla/calc-framework/releases/download/v1/a.zip")
    assert not require_https_url("http://example.com/a.zip")
    assert not require_https_url("ftp://example.com/a.zip")


def test_sha256_sidecar_roundtrip(tmp_path: Path) -> None:
    artifact = tmp_path / "GameCalcPlatform_v1.0.0.zip"
    artifact.write_bytes(b"hello launcher")
    sidecar = write_sha256_sidecar(artifact)
    assert sidecar.name == "GameCalcPlatform_v1.0.0.zip.sha256"
    parsed = parse_sha256_sidecar_text(sidecar.read_text(encoding="utf-8"))
    assert parsed == sha256_hex(artifact)


def test_find_checksum_in_assets() -> None:
    assets = [
        {"name": "GameCalcPlatform_v1.zip", "browser_download_url": "https://x/a.zip"},
        {"name": "GameCalcPlatform_v1.zip.sha256", "browser_download_url": "https://x/a.sha256"},
    ]
    url = find_checksum_in_assets(assets, "GameCalcPlatform_v1.zip")
    assert url == "https://x/a.sha256"
    assert checksum_asset_name("GameCalcPlatform_v1.zip") == "GameCalcPlatform_v1.zip.sha256"
