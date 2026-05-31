#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""BWIKI 装备 wikitext 解析（与 Wiki 模板字段对齐）。"""

from __future__ import annotations

import re
from typing import Any

# Wiki「装备种类」三槽（与 BWIKI 展示一致）
EQUIPMENT_KIND_ARMOR = "护甲"
EQUIPMENT_KIND_GLOVES = "护手"
EQUIPMENT_KIND_ACCESSORY = "配件"

_WIKI_KIND_ALIASES = {
    "护甲": EQUIPMENT_KIND_ARMOR,
    "胸甲": EQUIPMENT_KIND_ARMOR,
    "防具": EQUIPMENT_KIND_ARMOR,
    "护手": EQUIPMENT_KIND_GLOVES,
    "配件": EQUIPMENT_KIND_ACCESSORY,
}

_DIGIT_RE = re.compile(r"\d+")


def normalize_equipment_kind(raw: str | None) -> str:
    """将 Wiki/旧本地字段归一为装备种类：护甲 | 护手 | 配件。"""
    text = (raw or "").strip()
    if not text:
        return ""
    if text in _WIKI_KIND_ALIASES:
        return _WIKI_KIND_ALIASES[text]
    return ""


def _parse_int(text: str | None) -> int:
    if not text:
        return 0
    m = _DIGIT_RE.search(str(text))
    return int(m.group(0)) if m else 0


def _collect_numbered_texts(params: dict[str, Any], prefix: str) -> list[str]:
    texts: list[str] = []
    for idx in range(1, 10):
        raw = str(params.get(f"{prefix}{idx}") or "").strip()
        if raw:
            texts.append(raw)
    return texts


def collect_attribute_affixes(params: dict[str, Any]) -> list[str]:
    """收集主词条与属性词条（面板向，非伤害乘区效果）。"""
    affixes: list[str] = []
    main = str(params.get("主词条") or "").strip()
    main_val = str(params.get("主词条数值") or "").strip()
    if main:
        affixes.append(f"{main}{main_val}" if main_val else main)
    for idx in range(1, 10):
        key = str(params.get(f"属性词条{idx}") or "").strip()
        if not key:
            continue
        val = str(params.get(f"属性词条{idx}数值") or "").strip()
        affixes.append(f"{key}{val}" if val else key)
    return affixes


def collect_set_bonus_texts(params: dict[str, Any]) -> list[str]:
    """三件套描述：优先 Wiki「装备套组效果」。"""
    set_text = str(params.get("装备套组效果") or "").strip()
    if set_text:
        return [set_text]
    return _collect_numbered_texts(params, "三件套效果")


def equipment_record_from_wiki_params(
    *,
    name: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """由模板参数生成本地 equipments.json 单条记录。"""
    kind = normalize_equipment_kind(
        str(params.get("装备种类") or params.get("部位") or params.get("类型") or "")
    )
    set_name = str(params.get("所属套组") or params.get("套装") or "").strip()
    rarity_raw = str(params.get("稀有度") or params.get("星级") or "").strip()
    return {
        "名称": name.strip(),
        "装备种类": kind,
        "部位": kind,
        "稀有度": rarity_raw,
        "星级": _parse_int(rarity_raw),
        "所属套组": set_name,
        "套装": set_name,
        "属性词条": collect_attribute_affixes(params),
        "效果": _collect_numbered_texts(params, "效果"),
        "三件套效果": collect_set_bonus_texts(params),
        "_source": "bwiki",
    }


def equipment_record_from_draft(draft: dict[str, Any]) -> dict[str, Any]:
    """将 parse_draft 草案转为本地装备记录；种类缺失时由调用方回退推断。"""
    params = draft.get("_wiki_params") or {}
    name = str(draft.get("名称") or params.get("装备名称") or "").strip()
    row = equipment_record_from_wiki_params(name=name, params=params)
    if not row["装备种类"]:
        from bwiki_scout.pkg_bootstrap import ensure_package_path

        ensure_package_path()
        from games.endfield.calc.equipment.system import infer_equipment_slot

        inferred = infer_equipment_slot({"名称": name, "部位": "", "装备种类": ""})
        row["装备种类"] = inferred
        row["部位"] = inferred
    return row
