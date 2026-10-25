# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""文件校验工具。"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

_SHA256_ASSET_SUFFIX = ".sha256"
_SHA256_HEX_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def sha256_hex(path: Path) -> str:
    """计算文件 SHA256（小写 hex）。"""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(8192):
            digest.update(chunk)
    return digest.hexdigest()


def write_sha256_sidecar(artifact: Path) -> Path:
    """写入 ``<artifact>.sha256`` 侧车文件（单行 hex）。"""
    sidecar = artifact.with_name(artifact.name + _SHA256_ASSET_SUFFIX)
    sidecar.write_text(sha256_hex(artifact) + "\n", encoding="utf-8")
    return sidecar


def parse_sha256_sidecar_text(text: str) -> str | None:
    """解析侧车文件内容。"""
    line = text.strip().splitlines()[0].strip() if text.strip() else ""
    if _SHA256_HEX_RE.fullmatch(line):
        return line.lower()
    return None


def checksum_asset_name(zip_name: str) -> str:
    """Release 资产侧车文件名。"""
    return f"{zip_name}{_SHA256_ASSET_SUFFIX}"


def find_checksum_in_assets(assets: list[dict], zip_name: str) -> str | None:
    """在 GitHub Release assets 中查找 ZIP 对应的 SHA256。"""
    sidecar = checksum_asset_name(zip_name)
    for asset in assets:
        if asset.get("name") == sidecar:
            url = asset.get("browser_download_url", "")
            if not url:
                return None
            return url
    return None


def require_https_url(url: str) -> bool:
    """仅允许 HTTPS 下载 URL。"""
    return url.startswith("https://")
