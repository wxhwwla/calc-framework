#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0

# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""解析干员「详细数据」子页 wikitext（干员/逐级等级 模板）。"""



from __future__ import annotations



import json

import math

import re

from pathlib import Path

from typing import Any



# 干员图鉴中的非角色页，不请求 */详细数据

OPERATOR_SKIP_DETAIL: frozenset[str] = frozenset(

    {

        "后勤技能一览",

        "威胁图鉴",

        "干员送礼一览",

        "物品图鉴",

    }

)



OPERATOR_DETAIL_SUFFIX = "/详细数据"



# Wiki 模板键 -> 本地 characters.json 键

WIKI_ATTR_TO_LOCAL: dict[str, str] = {

    "攻击": "基础攻击力",

    "力量": "力量",

    "敏捷": "敏捷",

    "智识": "智识",

    "意志": "意志",

    "生命": "基础生命值",

    "防御": "基础防御力",

}



_ATTR_LEVEL_RE = re.compile(r"^(力量|敏捷|智识|意志|攻击|生命|防御)(\d+)$")

_PARAM_RE = re.compile(r"\|\s*([^|=]+?)\s*=\s*([^|\n]+)")





def operator_detail_title(operator_name: str) -> str:

    """MediaWiki 子页面标题。"""

    return f"{operator_name}{OPERATOR_DETAIL_SUFFIX}"





def operator_detail_titles(operator_names: list[str]) -> list[str]:

    """为干员列表生成应拉取的详细数据页标题。"""

    out: list[str] = []

    for name in operator_names:

        if name in OPERATOR_SKIP_DETAIL:

            continue

        out.append(operator_detail_title(name))

    return out





def _parse_number(text: str) -> float | None:

    text = text.strip().replace("×", "").strip()

    if not text:

        return None

    m = re.search(r"-?\d+(?:\.\d+)?", text)

    if not m:

        return None

    return float(m.group(0))





def parse_operator_detail_wikitext(wikitext: str, *, max_level: int = 90) -> dict[str, Any]:

    """

    从「干员/逐级等级」模板解析 1..max_level 各属性。



    返回含 ``levels`` 与本地同名字段（如 ``基础攻击力``）的数组；缺级为 None。

    """

    per_level: dict[int, dict[str, float]] = {}

    for raw_key, raw_val in _PARAM_RE.findall(wikitext or ""):

        key = raw_key.strip()

        m = _ATTR_LEVEL_RE.match(key)

        if not m:

            continue

        wiki_attr, level = m.group(1), int(m.group(2))

        if level < 1 or level > max_level:

            continue

        num = _parse_number(raw_val)

        if num is None:

            continue

        per_level.setdefault(level, {})[wiki_attr] = num



    levels = list(range(1, max_level + 1))

    curves: dict[str, Any] = {"levels": levels, "_parsed_levels": len(per_level)}

    for wiki_attr, local_key in WIKI_ATTR_TO_LOCAL.items():

        curves[local_key] = [per_level.get(lv, {}).get(wiki_attr) for lv in levels]

    return curves





def load_local_characters(path: Path) -> dict[str, dict[str, Any]]:

    """按名称索引本地角色记录。"""

    with path.open(encoding="utf-8") as f:

        rows = json.load(f)

    return {row["名称"]: row for row in rows if row.get("名称")}





def compare_operator_to_local(

    *,

    operator_name: str,

    wiki_curves: dict[str, Any],

    local_record: dict[str, Any],

    fields: tuple[str, ...] = ("基础攻击力", "力量", "敏捷", "智识", "意志"),

    tolerance: float = 0.05,

) -> dict[str, Any]:

    """逐级对比 Wiki 与本地数组；返回摘要供报告使用。"""

    local_levels = local_record.get("等级") or []

    mismatches: list[dict[str, Any]] = []

    compared = 0

    for field in fields:

        local_arr = local_record.get(field)

        wiki_arr = wiki_curves.get(field)

        if not isinstance(local_arr, list) or not isinstance(wiki_arr, list):

            continue

        for lv, local_val, wiki_val in zip(local_levels, local_arr, wiki_arr):

            if wiki_val is None or (

                isinstance(wiki_val, float) and math.isnan(wiki_val)

            ):

                continue

            compared += 1

            delta = float(local_val) - float(wiki_val)

            if abs(delta) > tolerance:

                mismatches.append(

                    {

                        "field": field,

                        "level": lv,

                        "local": local_val,

                        "wiki": wiki_val,

                        "delta": round(delta, 3),

                    }

                )

    return {

        "name": operator_name,

        "wiki_levels_parsed": wiki_curves.get("_parsed_levels", 0),

        "compared_points": compared,

        "mismatch_count": len(mismatches),

        "mismatches": mismatches[:30],

    }





def build_operator_stats_diff(

    *,

    output_root: Path,

    characters_json: Path,

) -> dict[str, Any]:

    """读取 raw 缓存中的详细数据页，与本地 characters.json 逐级对比。"""

    raw_dir = output_root / "raw"

    by_name = load_local_characters(characters_json)

    results: list[dict[str, Any]] = []

    missing_detail: list[str] = []

    perfect: list[str] = []



    for name in sorted(by_name.keys()):

        detail_title = operator_detail_title(name)

        bundle_path = raw_dir / re.sub(r'[<>:"/\\|?*]', "_", detail_title) / "wikitext.txt"

        if not bundle_path.is_file():

            missing_detail.append(name)

            continue

        wikitext = bundle_path.read_text(encoding="utf-8")

        if "干员/逐级等级" not in wikitext and "攻击1" not in wikitext:

            missing_detail.append(name)

            continue

        wiki_curves = parse_operator_detail_wikitext(wikitext)

        summary = compare_operator_to_local(

            operator_name=name,

            wiki_curves=wiki_curves,

            local_record=by_name[name],

        )

        results.append(summary)

        if summary["mismatch_count"] == 0 and summary["compared_points"] > 0:

            perfect.append(name)



    return {

        "operators": results,

        "missing_detail_pages": missing_detail,

        "perfect_match": perfect,

    }

