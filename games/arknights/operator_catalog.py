# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""干员目录加载与筛选（Web API / 桌面 GUI 共用）。"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

from games.arknights.calc.inverse.materialize import materialize_operator_entity
from utils.game_data_paths import ARKNIGHTS_OPERATORS_STANDARD_REL
from utils.path_utils import get_application_dir, get_resource_path

REPO_ROOT = Path(__file__).resolve().parents[2]
STANDARD_OPERATORS_REL = ARKNIGHTS_OPERATORS_STANDARD_REL
SKIP_STEMS = frozenset({"_sync_summary", "operators"})
MIN_PARSED_COUNT = 100
STAR_TIERS = (6, 5, 4, 3, 2, 1)


def default_parsed_dir() -> Path:
    """干员 JSON 目录（开发=仓库；打包=exe 同级 tools/.../parsed）。"""
    return get_application_dir() / "tools" / "arknights_scout" / "output" / "parsed"


# 兼容 tools/compact_arknights_operators 等脚本
DEFAULT_PARSED_DIR = default_parsed_dir()


def default_zip_candidates() -> tuple[Path, ...]:
    """干员压缩包候选路径（exe 旁优先，其次仓库根）。"""
    app = get_application_dir()
    return (
        app / "tools" / "arknights_scout" / "arknights_parsed.zip",
        app / "dist_arknights_parsed.zip",
        REPO_ROOT / "tools" / "arknights_scout" / "arknights_parsed.zip",
        REPO_ROOT / "dist_arknights_parsed.zip",
    )


def find_zip_path(candidates: tuple[Path, ...] | None = None) -> Path | None:
    """查找可用的压缩数据文件路径。"""
    paths = candidates if candidates is not None else default_zip_candidates()
    for path in paths:
        if path.is_file():
            return path
    return None


def index_entry(data: dict[str, Any], fallback_name: str) -> dict[str, Any]:
    """从干员数据中提取索引条目。"""
    return {
        "名称": str(data.get("名称") or fallback_name),
        "星级": int(data.get("星级") or 0),
        "职业": str(data.get("职业") or ""),
        "分支": str(data.get("分支") or ""),
    }


def build_operator_index(operators: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """构建干员索引列表，按星级/职业/分支/名称排序。"""
    index = [index_entry(data, name) for name, data in operators.items()]
    index.sort(key=lambda x: (-x["星级"], x["职业"], x["分支"], x["名称"]))
    return index


def filter_operator_index(
    index: list[dict[str, Any]],
    *,
    active_stars: set[int],
    profession: str = "",
    branch: str = "",
    search: str = "",
) -> list[dict[str, Any]]:
    """按星级 / 主职业(职业) / 副职业(分支) / 名称搜索词 筛选。"""
    if profession in ("全部",):
        profession = ""
    if branch in ("全部", "全部分支"):
        branch = ""
    all_stars = len(active_stars) >= len(STAR_TIERS)
    needle = search.strip()
    result: list[dict[str, Any]] = []
    for op in index:
        if not all_stars and op["星级"] not in active_stars:
            continue
        if profession and op["职业"] != profession:
            continue
        if branch and op["分支"] != branch:
            continue
        if needle and needle not in op.get("名称", ""):
            continue
        result.append(op)
    return result


def list_professions(index: list[dict[str, Any]]) -> list[str]:
    """列出索引中所有职业。"""
    return sorted({op["职业"] for op in index if op["职业"]}, key=lambda s: s)


def list_branches(index: list[dict[str, Any]], profession: str = "") -> list[str]:
    """列出索引中所有分支（可选按职业筛选）。"""
    branches: set[str] = set()
    for op in index:
        if profession and op["职业"] != profession:
            continue
        if op["分支"]:
            branches.add(op["分支"])
    return sorted(branches, key=lambda s: s)


def _read_json_file(path: Path) -> dict[str, Any] | None:
    """读取并解析 JSON 文件，失败时返回 None。"""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _load_operators_standard_fallback() -> dict[str, dict[str, Any]]:
    """打包未随 scout 数据时，回退 framework 标准干员库。"""
    path = get_resource_path(STANDARD_OPERATORS_REL)
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    result: dict[str, dict[str, Any]] = {}
    items: list[Any]
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = list(data.values())
    else:
        return {}
    for item in items:
        if not isinstance(item, dict):
            continue
        name = str(item.get("名称") or "").strip()
        if not name:
            continue
        result[name] = materialize_operator_entity(item)
    return result


def load_operators_map(
    parsed_dir: Path | None = None,
    zip_candidates: tuple[Path, ...] | None = None,
) -> dict[str, dict[str, Any]]:
    """加载全部干员 JSON；目录不完整时合并 zip / 标准库。"""
    parsed_dir = parsed_dir or default_parsed_dir()
    zip_candidates = zip_candidates if zip_candidates is not None else default_zip_candidates()
    result: dict[str, dict[str, Any]] = {}
    if parsed_dir.is_dir():
        for f in sorted(parsed_dir.glob("*.json")):
            if f.stem in SKIP_STEMS:
                continue
            data = _read_json_file(f)
            if data is not None:
                name = str(data.get("名称") or f.stem)
                result[name] = materialize_operator_entity(data)

    if len(result) >= MIN_PARSED_COUNT:
        return result

    zip_path = find_zip_path(zip_candidates)
    if zip_path is not None:
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
                name = str(data.get("名称") or stem)
                result[name] = materialize_operator_entity(data)

    if len(result) < MIN_PARSED_COUNT:
        for name, entity in _load_operators_standard_fallback().items():
            result.setdefault(name, entity)
    return result
