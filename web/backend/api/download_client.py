# SPDX-License-Identifier: AGPL-3.0
"""本地搜索服务器 zip 下载（FastAPI + WSGI 共用）。"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def find_local_backend_zip() -> Path | None:
    """在已知目录中查找预编译的本地后端 zip 文件。"""
    for directory in (
        REPO_ROOT / "dist" / "终末地本地搜索服务器",
        REPO_ROOT / "web" / "static",
        REPO_ROOT / "static",
    ):
        candidate = directory / "local-backend.zip"
        if candidate.is_file():
            return candidate
    return None


def build_client_download() -> tuple[bytes, str, str]:
    """返回 (body, filename, content_type)。"""
    found = find_local_backend_zip()
    if found:
        return found.read_bytes(), "local-backend.zip", "application/zip"

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "README.txt",
            "END FIELD DAMAGE CALCULATOR - Local Backend Server\n"
            "===============================================\n\n"
            "The pre-packaged local backend is not yet available.\n\n"
            "For developers, run in the project root:\n"
            "  python web/build_local_backend.py\n\n"
            "Then upload the zip to the server.\n",
        )
    body = buf.getvalue()
    return body, "local-backend-readme.zip", "application/zip"
