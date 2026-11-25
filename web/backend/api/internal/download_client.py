# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""本地搜索服务器 zip 下载（FastAPI + WSGI 共用）。"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def find_local_backend_zip() -> Path | None:
    """在已知目录中查找预编译的本地后端 zip 文件。"""
    for directory in (
        REPO_ROOT / "dist" / "终末地本地搜索服务器",
        REPO_ROOT / "web" / "frontend" / "dist",
        REPO_ROOT / "web" / "frontend" / "public",
        REPO_ROOT / "web" / "static",
        REPO_ROOT / "static",
    ):
        candidate = directory / "local-backend.zip"
        if candidate.is_file():
            return candidate
    return None


def build_client_download() -> tuple[bytes, str, str]:
    """返回真实后端制品；缺失时由上层映射为 404。"""
    found = find_local_backend_zip()
    if not found:
        raise FileNotFoundError("本地后端制品尚未构建或上传")
    return found.read_bytes(), "local-backend.zip", "application/zip"


__all__: list[str] = []
