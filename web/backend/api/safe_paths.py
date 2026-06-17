# SPDX-License-Identifier: AGPL-3.0
"""安全路径工具 — 防止路径穿越写入。"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import HTTPException

# 仅允许 contribute_{stem}_{timestamp}.json，stem 已消毒
_STAGING_FILENAME = re.compile(r"^contribute_[a-zA-Z0-9_-]{1,64}_\d{8}_\d{6}\.json$")


def sanitize_contribute_stem(name: str) -> str:
    """将实体名称转为安全文件名片段。"""
    safe = re.sub(r"[^a-zA-Z0-9_-]", "_", str(name))[:64]
    return safe or "unnamed"


def build_contribute_filename(entity_name: str, *, now: datetime | None = None) -> str:
    """生成贡献暂存文件名（不含目录成分）。"""
    ts = (now or datetime.now()).strftime("%Y%m%d_%H%M%S")
    return f"contribute_{sanitize_contribute_stem(entity_name)}_{ts}.json"


def resolve_staging_file(staging_dir: Path, filename: str) -> Path:
    """在 staging 根目录下解析文件名，拒绝穿越与非法字符。

    Raises:
        HTTPException: 文件名不符合白名单或解析后逃逸 staging 根目录。
    """
    if not _STAGING_FILENAME.fullmatch(filename):
        raise HTTPException(status_code=400, detail="无效的文件名")

    root = staging_dir.resolve()
    target = (root / filename).resolve()

    if not target.is_relative_to(root):
        raise HTTPException(status_code=400, detail="无效的文件名")

    return target


def write_json_to_staging(staging_dir: Path, filename: str, payload: dict[str, Any]) -> Path:
    """将 JSON 写入 staging 目录（路径穿越安全）。"""
    target = resolve_staging_file(staging_dir, filename)
    staging_dir.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    return target


__all__ = [
    "build_contribute_filename",
    "resolve_staging_file",
    "sanitize_contribute_stem",
    "write_json_to_staging",
]
