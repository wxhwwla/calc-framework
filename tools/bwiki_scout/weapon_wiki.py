#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从武器主页 wikitext 解析成长数据并反推 seed 参数。"""

from __future__ import annotations

import io
import re
import sys
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_PKG = _REPO_ROOT / "endfield_damage_calculator"
if str(_PKG) not in sys.path:
    sys.path.insert(0, str(_PKG))

from bwiki_scout.parse_draft import extract_template_params, _parse_int  # noqa: E402
from calculation.formula import calculate_bonus_attribute, calculate_growth_curve  # noqa: E402
from calculation.inverse import fit_attribute_formula, fit_skill_formula_no_special  # noqa: E402

# Wiki 稀有度 → 本地星级
_RARITY_STAR: dict[str, int] = {
    "白色": 2,
    "绿色": 3,
    "蓝色": 4,
    "紫色": 4,
    "金色": 5,
    "橙色": 6,
}

_ATTR_KEY_RE = re.compile(r"^(.+?)\+")
_RANK_RE = re.compile(r"^词条(\d)(?:副(\d))?rank(\d)$")
_FLOAT_RE = re.compile(r"[\d.]+")


def _parse_float(text: str | None) -> float | None:
    if not text:
        return None
    m = _FLOAT_RE.search(text.replace(",", ""))
    return float(m.group(0)) if m else None


def _attr_key_from_content(content: str) -> str:
    """「智识+16」「攻击力+5.0%」→「智识+」「攻击力+」。"""
    text = (content or "").strip().replace("％", "%")
    m = _ATTR_KEY_RE.match(text)
    if not m:
        return ""
    return m.group(1) + "+"


def _parse_rank_value(raw: str) -> float:
    text = (raw or "").strip().replace("％", "%")
    if text.endswith("%"):
        return _parse_float(text[:-1]) or 0.0
    return float(_parse_int(text) or _parse_float(text) or 0)


def parse_weapon_meta_from_wikitext(wikitext: str) -> dict[str, Any]:
    """武器类型、星级等元数据。"""
    p = extract_template_params(wikitext)
    rarity = (p.get("稀有度") or "").strip()
    star = _RARITY_STAR.get(rarity)
    if star is None:
        star = _parse_int(rarity) or 0
    return {
        "weapon_type": (p.get("武器种类") or "").strip(),
        "star": star,
    }


def parse_weapon_rank_curves(wikitext: str) -> dict[str, list[float]]:
    """解析 ``词条Nrank1–9`` / ``词条N副Mrank1–9`` 曲线（9 点）。"""
    p = extract_template_params(wikitext)
    grouped: dict[str, list[float | None]] = {}
    for key, raw in p.items():
        m = _RANK_RE.match(key)
        if not m:
            continue
        slot = m.group(1)
        sub = m.group(2) or ""
        rank = int(m.group(3))
        gkey = f"{slot}_{sub}" if sub else slot
        grouped.setdefault(gkey, [None] * 9)
        if 1 <= rank <= 9:
            grouped[gkey][rank - 1] = _parse_rank_value(raw)

    out: dict[str, list[float]] = {}
    for gkey, vals in grouped.items():
        if any(v is None for v in vals):
            continue
        out[gkey] = [float(v) for v in vals]  # type: ignore[arg-type]
    return out


def has_weapon_growth_block(wikitext: str) -> bool:
    """是否包含可用于反推的基础攻击与词条 rank 数据。"""
    p = extract_template_params(wikitext)
    return "基础攻击力" in p and "满级基础攻击力" in p and "词条1rank1" in p


def fit_bonus_params_from_rank_curve(curve9: list[float]) -> dict[str, Any]:
    """9 档潜能曲线 → add_weapon / seed 用参数字典。"""
    if len(curve9) != 9:
        raise ValueError(f"武器词条曲线长度应为 9，实际 {len(curve9)}")
    with redirect_stdout(io.StringIO()):
        base, growth, divisor, offset, special = fit_skill_formula_no_special(curve9)
    return {
        "base": base,
        "growth": growth,
        "divisor": divisor,
        "offset": offset,
        "special": list(special),
    }


def fit_weapon_base_atk_from_endpoints(
    level1: int,
    level90: int,
    *,
    reference_curve: list[float] | None = None,
) -> dict[str, int | float]:
    """
    由 1 级 / 90 级基础攻击反推 90 级成长参数。

    若提供 ``reference_curve``（通常来自本地 JSON），按端点比例缩放形状后反推；
    否则对整数线性插值曲线反推。
    """
    if reference_curve and len(reference_curve) >= 90:
        ref = [float(reference_curve[i]) for i in range(90)]
        denom = ref[-1] - ref[0]
        if abs(denom) < 1e-9:
            raise ValueError("参考基础攻击曲线端点相同，无法缩放")
        scaled = [
            level1 + (ref[i] - ref[0]) * (level90 - level1) / denom for i in range(90)
        ]
        sample = [int(round(v)) for v in scaled]
    else:
        sample = [
            int(round(level1 + (level90 - level1) * (lv - 1) / 89)) for lv in range(1, 91)
        ]
    with redirect_stdout(io.StringIO()):
        base, growth, divisor, offset = fit_attribute_formula(sample)
    return {"base": base, "growth": growth, "divisor": divisor, "offset": offset}


def build_weapon_seed_spec_from_wiki(
    *,
    name: str,
    wikitext: str,
    reference_weapon: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """由武器 wikitext 生成 seed_weapons 条目。"""
    if not has_weapon_growth_block(wikitext):
        raise ValueError(f"武器「{name}」Wiki 缺少成长数据块")

    meta = parse_weapon_meta_from_wikitext(wikitext)
    p = extract_template_params(wikitext)
    l1 = _parse_int(p.get("基础攻击力"))
    l90 = _parse_int(p.get("满级基础攻击力"))
    if l1 is None or l90 is None:
        raise ValueError(f"武器「{name}」基础攻击力端点不完整")

    ref_atk = None
    if reference_weapon:
        ref_atk = reference_weapon.get("基础攻击力")

    spec: dict[str, Any] = {
        "name": name,
        "weapon_type": meta["weapon_type"],
        "star": meta["star"],
        "base_atk": fit_weapon_base_atk_from_endpoints(
            l1, l90, reference_curve=ref_atk
        ),
        "bonus_attrs": {},
        "special_ability": {"enabled": False},
    }

    rank_curves = parse_weapon_rank_curves(wikitext)
    key1 = _attr_key_from_content(p.get("词条1内容") or "")
    key2 = _attr_key_from_content(p.get("词条2内容") or "")
    if key1 and "1" in rank_curves:
        spec["bonus_attrs"][key1] = fit_bonus_params_from_rank_curve(rank_curves["1"])
    if key2 and "2" in rank_curves:
        spec["bonus_attrs"][key2] = fit_bonus_params_from_rank_curve(rank_curves["2"])

    sub1_key = (p.get("词条3副1内容") or "").strip()
    if sub1_key and "3_1" in rank_curves:
        sa_name = sub1_key if sub1_key.endswith("+") else sub1_key + "+"
        sa_params = fit_bonus_params_from_rank_curve(rank_curves["3_1"])
        spec["special_ability"] = {"enabled": True, "name": sa_name, **sa_params}
    return spec


def _bonus_curves_from_seed_spec(spec: dict[str, Any]) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {}
    for attr, params in (spec.get("bonus_attrs") or {}).items():
        key = attr if attr.endswith("+") else attr + "+"
        p = dict(params)
        special = p.pop("special", None)
        out[key] = calculate_bonus_attribute(special=special, **p)
    sa = spec.get("special_ability") or {}
    if sa.get("enabled"):
        name = sa.get("name", "")
        key = name if name.endswith("+") else name + "+"
        p = {k: sa[k] for k in ("base", "growth", "divisor", "offset") if k in sa}
        special = sa.get("special")
        out[key] = calculate_bonus_attribute(special=special, **p)
    return out


def needs_weapon_sync_with_wiki(
    spec: dict[str, Any],
    local_record: dict[str, Any],
    *,
    tolerance: float = 0.05,
) -> bool:
    """本地武器与 Wiki 推导是否不一致。"""
    if spec.get("weapon_type") != local_record.get("类型"):
        return True
    if spec.get("star") != local_record.get("星级"):
        return True

    wiki_atk = calculate_growth_curve(**spec["base_atk"])
    local_atk = local_record.get("基础攻击力")
    levels = local_record.get("等级") or list(range(1, 91))
    if not isinstance(local_atk, list):
        return True
    for lv, la, wa in zip(levels, local_atk, wiki_atk):
        if abs(float(la) - float(wa)) > tolerance:
            return True

    wiki_bonus = _bonus_curves_from_seed_spec(spec)
    for key, wiki_arr in wiki_bonus.items():
        local_arr = local_record.get(key)
        if not isinstance(local_arr, list):
            return True
        for la, wa in zip(local_arr, wiki_arr):
            if abs(float(la) - float(wa)) > tolerance:
                return True

    local_sa = local_record.get("特殊能力") or [False]
    wiki_sa = spec.get("special_ability") or {}
    wiki_enabled = bool(wiki_sa.get("enabled"))
    if wiki_enabled != bool(local_sa[0] if local_sa else False):
        return True
    return False
