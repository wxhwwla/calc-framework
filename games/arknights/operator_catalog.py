# SPDX-License-Identifier: AGPL-3.0
"""干员目录加载与筛选（Web API / 桌面 GUI 共用）。"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PARSED_DIR = REPO_ROOT / "tools" / "arknights_scout" / "output" / "parsed"
DEFAULT_ZIP_CANDIDATES = (
    REPO_ROOT / "tools" / "arknights_scout" / "arknights_parsed.zip",
    REPO_ROOT / "dist_arknights_parsed.zip",
)
SKIP_STEMS = frozenset({"_sync_summary", "operators"})
MIN_PARSED_COUNT = 100
STAR_TIERS = (6, 5, 4, 3, 2, 1)


def find_zip_path(candidates: tuple[Path, ...] = DEFAULT_ZIP_CANDIDATES) -> Path | None:
    for path in candidates:
        if path.is_file():
            return path
    return None


def index_entry(data: dict[str, Any], fallback_name: str) -> dict[str, Any]:
    return {
        "名称": str(data.get("名称") or fallback_name),
        "星级": int(data.get("星级") or 0),
        "职业": str(data.get("职业") or ""),
        "分支": str(data.get("分支") or ""),
    }


def build_operator_index(operators: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    index = [index_entry(data, name) for name, data in operators.items()]
    index.sort(key=lambda x: (-x["星级"], x["职业"], x["分支"], x["名称"]))
    return index


def filter_operator_index(
    index: list[dict[str, Any]],
    *,
    active_stars: set[int],
    profession: str = "",
    branch: str = "",
) -> list[dict[str, Any]]:
    """按星级 / 主职业(职业) / 副职业(分支) 筛选。"""
    all_stars = len(active_stars) >= len(STAR_TIERS)
    result: list[dict[str, Any]] = []
    for op in index:
        if not all_stars and op["星级"] not in active_stars:
            continue
        if profession and op["职业"] != profession:
            continue
        if branch and op["分支"] != branch:
            continue
        result.append(op)
    return result


def list_professions(index: list[dict[str, Any]]) -> list[str]:
    return sorted({op["职业"] for op in index if op["职业"]}, key=lambda s: s)


def list_branches(index: list[dict[str, Any]], profession: str = "") -> list[str]:
    branches: set[str] = set()
    for op in index:
        if profession and op["职业"] != profession:
            continue
        if op["分支"]:
            branches.add(op["分支"])
    return sorted(branches, key=lambda s: s)


def _read_json_file(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def load_operators_map(
    parsed_dir: Path = DEFAULT_PARSED_DIR,
    zip_candidates: tuple[Path, ...] = DEFAULT_ZIP_CANDIDATES,
) -> dict[str, dict[str, Any]]:
    """加载全部干员 JSON；目录不完整时合并 zip。"""
    result: dict[str, dict[str, Any]] = {}
    if parsed_dir.is_dir():
        for f in sorted(parsed_dir.glob("*.json")):
            if f.stem in SKIP_STEMS:
                continue
            data = _read_json_file(f)
            if data is not None:
                result[str(data.get("名称") or f.stem)] = data

    if len(result) >= MIN_PARSED_COUNT:
        return result

    zip_path = find_zip_path(zip_candidates)
    if zip_path is None:
        return result

    with zipfile.ZipFile(zip_path) as zf:
        for arc in zf.namelist():
            if not arc.endswith(".json"):
                continue
            stem = Path(arc).stem
            if stem in SKIP_STEMS or stem in result:
                continue
            try:
                data = json.loads(zf.read(arc).decode("utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            result[str(data.get("名称") or stem)] = data
    return result
