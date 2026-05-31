#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0

# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""解析 BWIKI 同步目标：本地已有条目 + 可选 manifest 中的新条目。"""



from __future__ import annotations



import json

from pathlib import Path

from typing import Any



from bwiki_scout.detail_levels import OPERATOR_SKIP_DETAIL, operator_detail_title

from bwiki_scout.storage import load_page_bundle

from bwiki_scout.weapon_wiki import has_weapon_growth_block





def load_manifest_titles(output_root: Path, kind: str) -> list[str]:

    """读取 scout manifest 中某类条目的 Wiki 标题列表。"""

    path = output_root / "manifest.json"

    if not path.is_file():

        return []

    with path.open(encoding="utf-8") as f:

        manifest = json.load(f)

    block = (manifest.get("kinds") or {}).get(kind) or {}

    titles = block.get("titles") or []

    return [str(t) for t in titles]





def filter_operator_titles(titles: list[str]) -> list[str]:

    """排除图鉴中的非干员说明页。"""

    return [t for t in titles if t not in OPERATOR_SKIP_DETAIL]





def operator_wiki_cache_ready(raw_dir: Path, name: str) -> bool:

    """干员主页与「详细数据」子页缓存是否齐全。"""

    main = load_page_bundle(raw_dir, name)

    detail = load_page_bundle(raw_dir, operator_detail_title(name))

    return main is not None and detail is not None





def weapon_wiki_import_ready(raw_dir: Path, name: str) -> bool:

    """武器页缓存存在且含可反推的成长块。"""

    bundle = load_page_bundle(raw_dir, name)

    if not bundle:

        return False

    return has_weapon_growth_block(bundle.get("wikitext") or "")





def resolve_operator_sync_names(

    *,

    local_names: set[str],

    manifest_titles: list[str],

    raw_dir: Path,

    only: list[str] | None = None,

    include_new: bool = False,

) -> list[str]:

    """

    干员同步名称列表：默认仅本地已有；``include_new`` 时并入 manifest 中缓存齐全的新干员。

    """

    names = set(local_names)

    if include_new:

        for title in filter_operator_titles(manifest_titles):

            if title not in names and operator_wiki_cache_ready(raw_dir, title):

                names.add(title)

    if only is not None:

        names &= set(only)

    return sorted(names)





def resolve_weapon_sync_names(

    *,

    local_names: set[str],

    manifest_titles: list[str],

    raw_dir: Path,

    only: list[str] | None = None,

    include_new: bool = False,

) -> list[str]:

    """

    武器同步名称列表：默认仅本地已有；``include_new`` 时并入 manifest 中可反推的新武器。

    """

    names = set(local_names)

    if include_new:

        for title in manifest_titles:

            if title not in names and weapon_wiki_import_ready(raw_dir, title):

                names.add(title)

    if only is not None:

        names &= set(only)

    return sorted(names)





def summarize_importable_from_manifest(

    output_root: Path,

    *,

    local_operator_names: set[str],

    local_weapon_names: set[str],

) -> dict[str, Any]:

    """预览 manifest 中可 ``--new`` 导入、但本地尚无的条目（须有完整缓存）。"""

    raw_dir = output_root / "raw"

    op_titles = load_manifest_titles(output_root, "operator")

    wep_titles = load_manifest_titles(output_root, "weapon")

    new_ops = [

        t

        for t in filter_operator_titles(op_titles)

        if t not in local_operator_names and operator_wiki_cache_ready(raw_dir, t)

    ]

    new_weps = [

        t

        for t in wep_titles

        if t not in local_weapon_names and weapon_wiki_import_ready(raw_dir, t)

    ]

    return {"operators": sorted(new_ops), "weapons": sorted(new_weps)}

