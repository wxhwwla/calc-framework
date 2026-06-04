#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0

# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""读取本地 characters.json / weapons.json 的 schema 与名称列表。"""

import json

from pathlib import Path

from typing import Any


def _keys_of_record(record: dict[str, Any]) -> list[str]:
    """_keys_of_record 实现。"""
    return sorted(record.keys())


def load_local_name_sets(
    characters_path: Path,
    weapons_path: Path,
) -> dict[str, set[str]]:
    """返回 operator / weapon 的本地「名称」集合（已规范化键为原名，值存规范化）。"""

    with characters_path.open(encoding="utf-8") as f:
        characters = json.load(f)

    with weapons_path.open(encoding="utf-8") as f:
        weapons = json.load(f)

    def names_from(rows: list[dict[str, Any]]) -> set[str]:
        """names_from 实现。

        Args:
            rows: 参数描述。

        Returns:
            返回值描述。
        """
        return {str(row["名称"]) for row in rows if row.get("名称")}

    return {
        "operator": names_from(characters),
        "weapon": names_from(weapons),
    }


def summarize_local_schema(characters_path: Path, weapons_path: Path) -> dict[str, Any]:
    """汇总本地 JSON 顶层字段（取首条记录作代表）。"""

    with characters_path.open(encoding="utf-8") as f:
        characters = json.load(f)

    with weapons_path.open(encoding="utf-8") as f:
        weapons = json.load(f)

    char_sample = characters[0] if characters else {}

    weapon_sample = weapons[0] if weapons else {}

    return {
        "operator": {
            "path": str(characters_path),
            "count": len(characters),
            "top_level_keys": _keys_of_record(char_sample) if char_sample else [],
            "sample_name": char_sample.get("名称", ""),
        },
        "weapon": {
            "path": str(weapons_path),
            "count": len(weapons),
            "top_level_keys": _keys_of_record(weapon_sample) if weapon_sample else [],
            "sample_name": weapon_sample.get("名称", ""),
        },
        "equipment": {
            "path": None,
            "count": 0,
            "top_level_keys": [],
            "sample_name": "",
            "note": "本地尚无 equipment.json 基准文件",
        },
    }


def compare_name_sets(
    wiki_titles: set[str],
    local_names: set[str],
    *,
    normalize,
) -> dict[str, Any]:
    """

    比较 Wiki 标题与本地名称。



    返回 original 名称列表与 normalized 映射下的交集/差集。

    """

    wiki_norm = {normalize(t): t for t in wiki_titles}

    local_norm = {normalize(n): n for n in local_names}

    wiki_keys = set(wiki_norm.keys())

    local_keys = set(local_norm.keys())

    both_norm = sorted(wiki_keys & local_keys)

    only_wiki_norm = sorted(wiki_keys - local_keys)

    only_local_norm = sorted(local_keys - wiki_keys)

    unmapped_pairs = [
        {"wiki_title": wiki_norm[k], "local_name": local_norm[k]} for k in both_norm if wiki_norm[k] != local_norm[k]
    ]

    return {
        "matched": [
            {"wiki_title": wiki_norm[k], "local_name": local_norm[k]}
            for k in both_norm
            if wiki_norm[k] == local_norm[k]
        ],
        "title_matches_name_different": unmapped_pairs,
        "only_wiki": [wiki_norm[k] for k in only_wiki_norm],
        "only_local": [local_norm[k] for k in only_local_norm],
    }
