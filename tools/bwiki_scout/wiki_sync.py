#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 BWIKI 缓存同步干员/武器数据到 JSON 与 seed 脚本。

规则：与 Wiki 不一致时以 Wiki 为准；曲线经反推公式后录入。
干员技能倍率来自主页 HTML；武器成长来自主页 wikitext（基础攻击 + 词条 rank）。
"""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

from bwiki_scout.pkg_bootstrap import ensure_package_path
from bwiki_scout.seed_persist import (
    load_seed_character_specs,
    load_seed_weapon_specs,
    replace_seed_specs,
    write_seed_character_specs,
    write_seed_weapon_specs,
)

ensure_package_path()

from bwiki_scout.detail_levels import (  # noqa: E402
    operator_detail_title,
    parse_operator_detail_wikitext,
)
from bwiki_scout.parse_draft import extract_template_params, _parse_int  # noqa: E402
from bwiki_scout.storage import load_page_bundle  # noqa: E402
from bwiki_scout.skill_tables import (  # noqa: E402
    parse_skill_damage_rows_from_html,
    skill_tabs_to_seed_skills,
    verify_skill_params,
)
from bwiki_scout.import_targets import (  # noqa: E402
    load_manifest_titles,
    resolve_operator_sync_names,
    resolve_weapon_sync_names,
)
from bwiki_scout.weapon_wiki import (  # noqa: E402
    build_weapon_seed_spec_from_wiki,
    has_weapon_growth_block,
    needs_weapon_sync_with_wiki,
)
from calculation.damage.formula import calculate_growth_curve  # noqa: E402
from calculation.damage.inverse import fit_attribute_formula  # noqa: E402

# seed 字段名 -> 详细页解析后的曲线键
_ATTR_FIELDS: tuple[tuple[str, str], ...] = (
    ("strength", "力量"),
    ("agility", "敏捷"),
    ("intellect", "智识"),
    ("will", "意志"),
    ("base_atk", "基础攻击力"),
)

_META_LOCAL_TO_SPEC: tuple[tuple[str, str], ...] = (
    ("类型", "char_type"),
    ("星级", "star"),
    ("武器", "weapon"),
    ("主能力", "primary"),
    ("副能力", "secondary"),
)


def fit_growth_params_from_curve(
    curve: list[float | None],
    *,
    max_level: int = 90,
) -> dict[str, int | float]:
    """对 90 级曲线反推成长参数（add_character / seed 用）。"""
    values = []
    for lv in range(1, max_level + 1):
        if lv - 1 >= len(curve):
            raise ValueError(f"曲线长度不足 90（缺 L{lv}）")
        v = curve[lv - 1]
        if v is None:
            raise ValueError(f"曲线缺 L{lv} 数值，无法反推")
        values.append(float(v))
    with redirect_stdout(io.StringIO()):
        base, growth, divisor, offset = fit_attribute_formula(values)
    return {
        "base": base,
        "growth": growth,
        "divisor": divisor,
        "offset": offset,
    }


def parse_operator_meta_from_main_wikitext(wikitext: str) -> dict[str, Any]:
    """从干员主页模板读取元数据。"""
    p = extract_template_params(wikitext)
    star = _parse_int(p.get("稀有度") or p.get("星级"))
    return {
        "char_type": (p.get("职业") or p.get("类型") or "").strip(),
        "star": star if star is not None else 0,
        "weapon": (p.get("武器") or "").strip(),
        "primary": (p.get("主属性") or "").strip(),
        "secondary": (p.get("副属性") or "").strip(),
    }


def build_seed_spec_from_wiki(
    *,
    name: str,
    main_wikitext: str,
    detail_wikitext: str,
    main_html: str | None = None,
    preserve_skills: dict[str, list] | None = None,
) -> dict[str, Any]:
    """由 Wiki 主页 + 详细数据 wikitext（+ 可选 HTML 技能表）生成 seed 条目。"""
    meta = parse_operator_meta_from_main_wikitext(main_wikitext)
    curves = parse_operator_detail_wikitext(detail_wikitext)
    spec: dict[str, Any] = {
        "name": name,
        "char_type": meta["char_type"],
        "star": meta["star"],
        "weapon": meta["weapon"],
        "primary": meta["primary"],
        "secondary": meta["secondary"],
        "sk1": [],
        "sk2": [],
        "sk3": [],
    }
    if main_html:
        tabs = parse_skill_damage_rows_from_html(main_html)
        spec.update(skill_tabs_to_seed_skills(tabs))
    elif preserve_skills:
        for key in ("sk1", "sk2", "sk3"):
            if key in preserve_skills:
                spec[key] = preserve_skills[key]

    for seed_key, curve_key in _ATTR_FIELDS:
        spec[seed_key] = fit_growth_params_from_curve(curves[curve_key])
    return spec


def _curves_from_seed_spec(spec: dict[str, Any]) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {}
    for seed_key, _ in _ATTR_FIELDS:
        params = spec[seed_key]
        out[seed_key] = calculate_growth_curve(**params)
    return out


def needs_sync_with_wiki(
    spec: dict[str, Any],
    local_record: dict[str, Any],
    *,
    tolerance: float = 0.05,
) -> bool:
    """本地与 Wiki 推导结果是否不一致（含元数据）。"""
    mapping = {
        "char_type": "类型",
        "star": "星级",
        "weapon": "武器",
        "primary": "主能力",
        "secondary": "副能力",
    }
    for spec_key, local_key in mapping.items():
        if spec.get(spec_key) != local_record.get(local_key):
            return True

    skill_map = (
        ("sk1", "战技倍率"),
        ("sk2", "连携技倍率"),
        ("sk3", "终结技倍率"),
    )
    for sk_key, local_key in skill_map:
        wiki_skills = spec.get(sk_key) or []
        local_skills = local_record.get(local_key) or []
        if len(wiki_skills) != len(local_skills):
            return True
        for wiki_params, local_curve in zip(wiki_skills, local_skills):
            if not isinstance(local_curve, list):
                return True
            rebuilt = verify_skill_params(wiki_params)
            for a, b in zip(rebuilt, local_curve):
                if abs(float(a) - float(b)) > tolerance:
                    return True

    wiki_curves = _curves_from_seed_spec(spec)
    local_keys = {
        "strength": "力量",
        "agility": "敏捷",
        "intellect": "智识",
        "will": "意志",
        "base_atk": "基础攻击力",
    }
    levels = local_record.get("等级") or list(range(1, 91))
    for seed_key, local_key in local_keys.items():
        local_arr = local_record.get(local_key)
        wiki_arr = wiki_curves.get(seed_key)
        if not isinstance(local_arr, list) or not wiki_arr:
            return True
        for lv, la, wa in zip(levels, local_arr, wiki_arr):
            if abs(float(la) - float(wa)) > tolerance:
                return True
    return False


def load_preserve_skills_for_name(
    seed_path: Path,
    name: str,
) -> dict[str, list] | None:
    """读取已有 seed 中的技能反推参数以便保留。"""
    try:
        for spec in load_seed_character_specs(seed_path):
            if spec.get("name") == name:
                return {
                    "sk1": spec.get("sk1") or [],
                    "sk2": spec.get("sk2") or [],
                    "sk3": spec.get("sk3") or [],
                }
    except (ValueError, SyntaxError):
        return None
    return None


def sync_operators_from_cache(
    *,
    output_root: Path,
    characters_json: Path,
    seed_path: Path,
    names: list[str] | None = None,
    include_new: bool = False,
    dry_run: bool = True,
) -> dict[str, Any]:
    """
    从 output/raw 同步干员；返回摘要。

    dry_run=True 时不写文件，只报告将更新谁。
    include_new=True 时，将 manifest 中缓存齐全、本地尚无的干员一并写入。
    """
    from character_weapon_equipment.character_data.add_character import add_character

    raw_dir = output_root / "raw"
    with characters_json.open(encoding="utf-8") as f:
        local_rows = json.load(f)
    local_by_name = {r["名称"]: r for r in local_rows if r.get("名称")}

    manifest_ops = load_manifest_titles(output_root, "operator")
    target_names = resolve_operator_sync_names(
        local_names=set(local_by_name.keys()),
        manifest_titles=manifest_ops,
        raw_dir=raw_dir,
        only=names,
        include_new=include_new,
    )
    updates: dict[str, dict[str, Any]] = {}
    skipped: list[str] = []
    planned: list[str] = []
    added: list[str] = []
    updated: list[str] = []

    for name in target_names:
        local = local_by_name.get(name)
        is_new = local is None
        if is_new and not include_new:
            skipped.append(f"{name}(本地无，需 --new)")
            continue
        main_bundle = load_page_bundle(raw_dir, name)
        detail_bundle = load_page_bundle(raw_dir, operator_detail_title(name))
        if not main_bundle or not detail_bundle:
            skipped.append(name)
            continue
        main_html = main_bundle.get("html") or ""
        preserve = None if main_html.strip() else load_preserve_skills_for_name(seed_path, name)
        try:
            spec = build_seed_spec_from_wiki(
                name=name,
                main_wikitext=main_bundle["wikitext"],
                detail_wikitext=detail_bundle["wikitext"],
                main_html=main_html or None,
                preserve_skills=preserve,
            )
        except (ValueError, AssertionError) as exc:
            skipped.append(f"{name}({exc})")
            continue
        if not is_new and not needs_sync_with_wiki(spec, local):
            continue
        planned.append(name)
        if is_new:
            added.append(name)
        else:
            updated.append(name)
        updates[name] = spec
        if not dry_run:
            add_character(**spec, json_path=characters_json)

    if not dry_run and updates:
        specs = load_seed_character_specs(seed_path)
        merged = replace_seed_specs(specs, updates, admin_first=True)
        write_seed_character_specs(seed_path, merged)

    return {
        "planned": planned,
        "added": added,
        "updated": updated,
        "skipped": skipped,
        "updated_count": len(updates) if not dry_run else 0,
        "dry_run": dry_run,
        "include_new": include_new,
    }


def sync_weapons_from_cache(
    *,
    output_root: Path,
    weapons_json: Path,
    seed_path: Path,
    names: list[str] | None = None,
    include_new: bool = False,
    dry_run: bool = True,
) -> dict[str, Any]:
    """
    从 output/raw 同步武器；仅处理 Wiki 含完整成长块的条目。

    include_new=True 时，将 manifest 中可反推、本地尚无的武器写入 JSON/seed。
    """
    from character_weapon_equipment.weapon_data.add_weapon import add_weapon

    raw_dir = output_root / "raw"
    with weapons_json.open(encoding="utf-8") as f:
        local_rows = json.load(f)
    local_by_name = {r["名称"]: r for r in local_rows if r.get("名称")}

    manifest_weps = load_manifest_titles(output_root, "weapon")
    target_names = resolve_weapon_sync_names(
        local_names=set(local_by_name.keys()),
        manifest_titles=manifest_weps,
        raw_dir=raw_dir,
        only=names,
        include_new=include_new,
    )
    updates: dict[str, dict[str, Any]] = {}
    skipped: list[str] = []
    planned: list[str] = []
    added: list[str] = []
    updated: list[str] = []

    for name in target_names:
        local = local_by_name.get(name)
        is_new = local is None
        if is_new and not include_new:
            skipped.append(f"{name}(本地无，需 --new)")
            continue
        bundle = load_page_bundle(raw_dir, name)
        if not bundle:
            skipped.append(name)
            continue
        wikitext = bundle.get("wikitext") or ""
        if not has_weapon_growth_block(wikitext):
            skipped.append(f"{name}(无成长块)")
            continue
        try:
            spec = build_weapon_seed_spec_from_wiki(
                name=name,
                wikitext=wikitext,
                reference_weapon=local,
            )
        except (ValueError, AssertionError) as exc:
            skipped.append(f"{name}({exc})")
            continue
        if not is_new and not needs_weapon_sync_with_wiki(spec, local):
            continue
        planned.append(name)
        if is_new:
            added.append(name)
        else:
            updated.append(name)
        updates[name] = spec
        if not dry_run:
            add_weapon(**spec, json_path=weapons_json)

    if not dry_run and updates:
        specs = load_seed_weapon_specs(seed_path)
        merged = replace_seed_specs(specs, updates)
        write_seed_weapon_specs(seed_path, merged)

    return {
        "planned": planned,
        "added": added,
        "updated": updated,
        "skipped": skipped,
        "updated_count": len(updates) if not dry_run else 0,
        "dry_run": dry_run,
        "include_new": include_new,
    }
