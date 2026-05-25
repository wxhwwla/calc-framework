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


def _first_line_of_slot3_content(p: dict[str, str]) -> str:
    """词条3内容首行：Wiki 表格第三列的无条件部分。"""
    raw = (p.get("词条3内容") or "").strip()
    if not raw:
        return ""
    return raw.split("\n")[0].strip()


def _slot3_unconditional_attr_key(p: dict[str, str]) -> str:
    """第三附加技能键名（仅 ``词条3内容`` 首行无条件段，不用副1 文案）。"""
    first = _first_line_of_slot3_content(p).replace("％", "%").strip()
    # 首行须为「简短属性+数值」前缀；长句/模板标记归入特殊能力副词条。
    match = re.match(r"^([^+。]+?\+[\d.]+%?)(?:[。]|$)", first)
    if not match:
        return ""
    attr_part = match.group(1).split("+", 1)[0]
    if len(attr_part) > 12 or any(ch in attr_part for ch in "，'''{{"):
        return ""
    return _attr_key_from_content(match.group(1))


def _slot3_conditional_attr_key(p: dict[str, str], sub: str) -> str:
    """词条3 副 N 有条件描述 → JSON「特殊能力」名称。"""
    raw = (p.get(f"词条3副{sub}内容") or "").strip()
    if not raw:
        return ""
    return raw if raw.endswith("+") else raw + "+"


def _parse_max_stack_from_text(text: str, *, name: str = "") -> int:
    """从 Wiki 条件描述解析最大叠加层数。"""
    from character_weapon_equipment.weapon_data.special_fields import (
        infer_max_stack_from_special,
    )

    return infer_max_stack_from_special(name, text)


def _fit_conditional_special(rank_curves: dict[str, list[float]], p: dict[str, str], sub: str) -> dict[str, Any] | None:
    gkey = f"3_{sub}"
    if gkey not in rank_curves:
        return None
    name = _slot3_conditional_attr_key(p, sub)
    if not name:
        return None
    fitted = fit_bonus_params_from_rank_curve(rank_curves[gkey])
    raw_text = (p.get(f"词条3副{sub}内容") or "").strip()
    slot3_context = "\n".join(
        (p.get(key) or "").strip()
        for key in ("词条3内容", "满级词条3内容")
        if (p.get(key) or "").strip()
    )
    max_stack = _parse_max_stack_from_text(
        f"{raw_text}\n{slot3_context}", name=name
    )
    if "curve" in fitted:
        return {"enabled": True, "name": name, "curve": fitted["curve"], "max_stack": max_stack}
    return {"enabled": True, "name": name, "max_stack": max_stack, **fitted}


def split_slot3_weapon_effects(
    p: dict[str, str],
    rank_curves: dict[str, list[float]],
) -> tuple[tuple[str, dict[str, Any]] | None, list[dict[str, Any]]]:
    """
    拆分词条3：第三技能（无条件 / 副1）与最多两条有条件特殊能力（副1–4）。

    若 ``词条3内容`` 首行可解析为 ``属性+数值``，则副1 曲线归入第三技能，有条件从副2 起；
    否则副1 起归入特殊能力1/2（如 O.B.J.尖峰）。
    """
    third: tuple[str, dict[str, Any]] | None = None
    third_key = _slot3_unconditional_attr_key(p)
    if third_key and "3_1" in rank_curves:
        third = (third_key, fit_bonus_params_from_rank_curve(rank_curves["3_1"]))

    conditionals: list[dict[str, Any]] = []
    for sub in ("1", "2", "3", "4"):
        if sub == "1" and third is not None:
            continue
        spec = _fit_conditional_special(rank_curves, p, sub)
        if spec:
            conditionals.append(spec)
    return third, conditionals


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
    try:
        with redirect_stdout(io.StringIO()):
            base, growth, divisor, offset, special = fit_skill_formula_no_special(curve9)
        return {
            "base": base,
            "growth": growth,
            "divisor": divisor,
            "offset": offset,
            "special": list(special),
        }
    except (ValueError, AssertionError):
        # 部分有条件词条（如 O.B.J.尖峰 攻击力 副2）无法反推公式，直接烘焙 Wiki 九档
        return {"curve": [float(v) for v in curve9]}


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
        "special_1": {"enabled": False},
        "special_2": {"enabled": False},
    }

    rank_curves = parse_weapon_rank_curves(wikitext)
    key1 = _attr_key_from_content(p.get("词条1内容") or "")
    key2 = _attr_key_from_content(p.get("词条2内容") or "")
    if key1 and "1" in rank_curves:
        spec["bonus_attrs"][key1] = fit_bonus_params_from_rank_curve(rank_curves["1"])
    if key2 and "2" in rank_curves:
        spec["bonus_attrs"][key2] = fit_bonus_params_from_rank_curve(rank_curves["2"])

    third, conditionals = split_slot3_weapon_effects(p, rank_curves)
    if third:
        spec["bonus_attrs"][third[0]] = third[1]
    if conditionals:
        spec["special_1"] = conditionals[0]
    if len(conditionals) > 1:
        spec["special_2"] = conditionals[1]
    return spec


def _bonus_curves_from_seed_spec(spec: dict[str, Any]) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {}
    for attr, params in (spec.get("bonus_attrs") or {}).items():
        key = attr if attr.endswith("+") else attr + "+"
        p = dict(params)
        special = p.pop("special", None)
        out[key] = calculate_bonus_attribute(special=special, **p)
    for sa_key in ("special_1", "special_2"):
        sa = spec.get(sa_key) or {}
        if not sa.get("enabled"):
            continue
        name = sa.get("name", "")
        if not name:
            continue
        key = name if name.endswith("+") else name + "+"
        if isinstance(sa.get("curve"), list):
            out[key] = [float(v) for v in sa["curve"]]
        else:
            p = {k: sa[k] for k in ("base", "growth", "divisor", "offset") if k in sa}
            special = sa.get("special")
            out[key] = calculate_bonus_attribute(special=special, **p)
    return out


def parse_special_max_stacks_from_wikitext(wikitext: str) -> list[tuple[str, int]]:
    """仅解析特殊能力名称与 max_stack（不要求 rank 曲线或成长块）。"""
    p = extract_template_params(wikitext)
    slot3_context = "\n".join(
        (p.get(key) or "").strip()
        for key in ("词条3内容", "满级词条3内容")
        if (p.get(key) or "").strip()
    )
    third_key = _slot3_unconditional_attr_key(p)
    results: list[tuple[str, int]] = []
    for sub in ("1", "2", "3", "4"):
        if sub == "1" and third_key:
            continue
        name = _slot3_conditional_attr_key(p, sub)
        if not name:
            continue
        raw_text = (p.get(f"词条3副{sub}内容") or "").strip()
        max_stack = _parse_max_stack_from_text(
            f"{raw_text}\n{slot3_context}", name=name
        )
        results.append((name, max_stack))
        if len(results) >= 2:
            break
    return results


def backfill_weapon_max_stack_from_cache(
    *,
    output_root: Path,
    weapons_json: Path,
    seed_path: Path,
    names: list[str] | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """
    从 Wiki 缓存（或离线名称推断）回填 weapons.json / seed 的 max_stack，不改曲线。
    """
    import json

    from bwiki_scout.seed_persist import load_seed_weapon_specs, write_seed_weapon_specs
    from bwiki_scout.storage import load_page_bundle
    from character_weapon_equipment.weapon_data.special_fields import (
        infer_max_stack_from_special,
        read_weapon_special_slots,
        write_weapon_special_slots,
    )

    raw_dir = output_root / "raw"
    with weapons_json.open(encoding="utf-8") as f:
        weapons = json.load(f)

    seed_specs = load_seed_weapon_specs(seed_path)
    seed_by_name = {s["name"]: s for s in seed_specs if s.get("name")}

    planned: list[str] = []
    skipped: list[str] = []
    changes: list[dict[str, Any]] = []

    for record in weapons:
        name = record.get("名称") or ""
        if not name:
            continue
        if names and name not in names:
            continue

        slots = list(read_weapon_special_slots(record))
        if not any(s[0] for s in slots):
            continue

        bundle = load_page_bundle(raw_dir, name)
        wiki_stacks: list[tuple[str, int]] = []
        if bundle and (bundle.get("wikitext") or "").strip():
            wiki_stacks = parse_special_max_stacks_from_wikitext(bundle["wikitext"])

        new_slots = list(slots)
        weapon_changed = False
        slot_changes: list[dict[str, Any]] = []

        for idx in range(2):
            enabled, sa_name, curve, old_stack = slots[idx]
            if not enabled:
                continue
            new_stack = old_stack
            source = "local"
            if idx < len(wiki_stacks) and wiki_stacks[idx][0] == sa_name:
                new_stack = wiki_stacks[idx][1]
                source = "wiki"
            elif wiki_stacks:
                for wname, wstack in wiki_stacks:
                    if wname == sa_name:
                        new_stack = wstack
                        source = "wiki"
                        break
            else:
                inferred = infer_max_stack_from_special(sa_name)
                if inferred != old_stack:
                    new_stack = inferred
                    source = "offline"

            if new_stack != old_stack:
                new_slots[idx] = (enabled, sa_name, curve, new_stack)
                weapon_changed = True
                slot_changes.append(
                    {
                        "slot": idx + 1,
                        "name": sa_name,
                        "old": old_stack,
                        "new": new_stack,
                        "source": source,
                    }
                )

        if not weapon_changed:
            continue

        planned.append(name)
        changes.append({"name": name, "slots": slot_changes})

        if dry_run:
            continue

        write_weapon_special_slots(record, new_slots)

        seed = seed_by_name.get(name)
        if seed:
            for ch in slot_changes:
                for sa_key in ("special_1", "special_2", "special_ability"):
                    sa = seed.get(sa_key) or {}
                    if sa.get("enabled") and sa.get("name") == ch["name"]:
                        sa["max_stack"] = ch["new"]
                        break

    if not dry_run and planned:
        with weapons_json.open("w", encoding="utf-8") as f:
            json.dump(weapons, f, ensure_ascii=False, indent=2)
        write_seed_weapon_specs(seed_path, seed_specs)

    return {
        "planned": planned,
        "changes": changes,
        "skipped": skipped,
        "updated_count": len(planned) if not dry_run else 0,
        "dry_run": dry_run,
    }


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

    from character_weapon_equipment.weapon_data.special_fields import (
        read_weapon_special_slots,
    )

    local_slots = read_weapon_special_slots(local_record)
    for idx, sa_key in enumerate(("special_1", "special_2")):
        wiki_sa = spec.get(sa_key) or {}
        local_enabled, local_name, local_curve, local_max_stack = local_slots[idx]
        wiki_enabled = bool(wiki_sa.get("enabled"))
        if wiki_enabled != local_enabled:
            return True
        if wiki_enabled:
            if wiki_sa.get("name") != local_name:
                return True
            wiki_max_stack = max(1, int(wiki_sa.get("max_stack", 1)))
            if wiki_max_stack != local_max_stack:
                return True
            wiki_cond = _bonus_curves_from_seed_spec({sa_key: wiki_sa})
            for _key, wiki_arr in wiki_cond.items():
                if not isinstance(local_curve, list):
                    return True
                for la, wa in zip(local_curve, wiki_arr):
                    if abs(float(la) - float(wa)) > tolerance:
                        return True
    return False
