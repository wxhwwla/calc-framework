#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""将 characters.json / weapons.json 中的等级数组压缩为 ``成长参数``。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from calc_framework.inverse.base import FitResult

from games.endfield.calc.core.data_generator import CHARACTER_NORMAL_ATTRS, CHARACTER_SKILL_ATTRS
from games.endfield.calc.damage.inverse.adapter import EndfieldInverseAdapter
from games.endfield.data_loading.curve_materialize import (
    GROWTH_PARAM_KEY,
    materialize_character_entity,
    strip_baked_curve_arrays,
)
from games.endfield.data_loading.loader import CHARACTERS_JSON_PATH, WEAPONS_JSON_PATH

DEFAULT_MAX_ERROR = 0.05
BONUS_LEVELS = 9


def _storage_from_fit(result: FitResult, *, max_error: float) -> dict[str, Any] | None:
    if not result.params or result.max_error > max_error:
        return None
    stored: dict[str, Any] = {
        "base": result.params["base"],
        "growth": result.params["growth"],
        "divisor": result.params["divisor"],
        "offset": result.params.get("offset", 0),
    }
    special = result.params.get("special_values")
    if special:
        stored["special"] = [float(v) for v in special]
    return stored


def _fit_normal_attr(
    adapter: EndfieldInverseAdapter,
    values: list[float | int],
    *,
    max_error: float,
) -> dict[str, Any] | None:
    if len(values) < 2:
        return None
    floats = [float(v) for v in values]
    if len(floats) == 94:
        result = adapter.fit_from_94(floats)
    else:
        result = adapter.fit_attribute_90(floats)
    return _storage_from_fit(result, max_error=max_error)


def _fit_skill_segment(
    adapter: EndfieldInverseAdapter,
    seg: list[float | int],
    *,
    max_error: float,
) -> dict[str, Any] | None:
    if not seg:
        return None
    floats = [float(v) for v in seg]
    if len(floats) >= 12:
        result = adapter.fit_skill_12(floats[:12])
    elif len(floats) >= 9:
        result = adapter.fit_skill_9(floats[:9])
    else:
        return None
    return _storage_from_fit(result, max_error=max_error)


def _fit_skill_segments(
    adapter: EndfieldInverseAdapter,
    segments: list[list[float | int]],
    *,
    max_error: float,
) -> list[dict[str, Any]] | None:
    out: list[dict[str, Any]] = []
    for seg in segments:
        entry = _fit_skill_segment(adapter, seg, max_error=max_error)
        if entry is None:
            return None
        out.append(entry)
    return out


def compact_character(
    char: dict[str, Any],
    adapter: EndfieldInverseAdapter,
    *,
    max_error: float,
) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    name = str(char.get("名称", "?"))
    params: dict[str, Any] = {}

    for attr in CHARACTER_NORMAL_ATTRS:
        values = char.get(attr)
        if not isinstance(values, list) or len(values) < 2:
            continue
        fitted = _fit_normal_attr(adapter, values, max_error=max_error)
        if fitted is None:
            warnings.append(f"{name}.{attr} 拟合误差 > {max_error}，保留数组")
            continue
        params[attr] = fitted

    for skill_attr in CHARACTER_SKILL_ATTRS:
        raw = char.get(skill_attr)
        if raw is None:
            continue
        if isinstance(raw, list) and raw and isinstance(raw[0], list):
            segments = _fit_skill_segments(adapter, raw, max_error=max_error)
            if segments is None:
                warnings.append(f"{name}.{skill_attr} 多段拟合失败，保留数组")
                continue
            params[skill_attr] = segments
        elif isinstance(raw, list):
            fitted = _fit_skill_segment(adapter, raw, max_error=max_error)
            if fitted is None:
                warnings.append(f"{name}.{skill_attr} 拟合失败，保留数组")
                continue
            params[skill_attr] = [fitted]

    if not params:
        return char, warnings

    out = strip_baked_curve_arrays(char, kind="character")
    out[GROWTH_PARAM_KEY] = params
    out["最大等级"] = len(char.get("等级", [])) or 90
    baked = materialize_character_entity(out)
    for key in params:
        if key in char and key in baked:
            old = char[key]
            new = baked[key]
            if isinstance(old, list) and isinstance(new, list) and old != new:
                warnings.append(f"{name}.{key} 烘焙校验与原文不一致（仍写入参数）")
    return out, warnings


def compact_weapon(
    weapon: dict[str, Any],
    adapter: EndfieldInverseAdapter,
    *,
    max_error: float,
) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    name = str(weapon.get("名称", "?"))
    params: dict[str, Any] = {}

    base_atk = weapon.get("基础攻击力")
    if isinstance(base_atk, list) and len(base_atk) >= 2:
        fitted = _fit_normal_attr(adapter, base_atk, max_error=max_error)
        if fitted is not None:
            params["基础攻击力"] = fitted
        else:
            warnings.append(f"{name}.基础攻击力 拟合失败，保留数组")

    for key, values in weapon.items():
        if not isinstance(key, str) or not key.endswith("+") or key == "攻击力+":
            continue
        if not isinstance(values, list) or len(values) < 2:
            continue
        fitted = _fit_normal_attr(adapter, values[:BONUS_LEVELS], max_error=max_error)
        if fitted is None:
            warnings.append(f"{name}.{key} 拟合失败，保留数组")
            continue
        if len(values) >= 9 and values[8] != fitted.get("base"):
            fitted["special"] = [float(values[8])]
        params[key] = fitted

    if not params:
        return weapon, warnings

    out = strip_baked_curve_arrays(weapon, kind="weapon")
    out[GROWTH_PARAM_KEY] = params
    out["最大等级"] = len(weapon.get("等级", [])) or 90
    return out, warnings


def _run(*, apply: bool, max_error: float) -> int:
    adapter = EndfieldInverseAdapter()
    char_path = Path(CHARACTERS_JSON_PATH)
    weapon_path = Path(WEAPONS_JSON_PATH)
    characters = json.loads(char_path.read_text(encoding="utf-8"))
    weapons = json.loads(weapon_path.read_text(encoding="utf-8"))
    all_warnings: list[str] = []

    new_chars = []
    for char in characters:
        compacted, warns = compact_character(char, adapter, max_error=max_error)
        new_chars.append(compacted)
        all_warnings.extend(warns)

    new_weapons = []
    for weapon in weapons:
        compacted, warns = compact_weapon(weapon, adapter, max_error=max_error)
        new_weapons.append(compacted)
        all_warnings.extend(warns)

    old_size = char_path.stat().st_size + weapon_path.stat().st_size
    if apply:
        char_path.write_text(json.dumps(new_chars, ensure_ascii=False, indent=2), encoding="utf-8")
        weapon_path.write_text(json.dumps(new_weapons, ensure_ascii=False, indent=2), encoding="utf-8")
        new_size = char_path.stat().st_size + weapon_path.stat().st_size
        print(f"[完成] 已写入 JSON；体积 {old_size} → {new_size} 字节")
    else:
        print(f"[dry-run] 角色 {len(new_chars)}、武器 {len(new_weapons)}；当前体积合计 {old_size} 字节")

    for w in all_warnings[:50]:
        print(f"  [警告] {w}")
    if len(all_warnings) > 50:
        print(f"  ... 另有 {len(all_warnings) - 50} 条警告")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="压缩游戏 JSON 等级曲线为成长参数")
    parser.add_argument("--apply", action="store_true", help="写回 JSON（默认仅 dry-run）")
    parser.add_argument("--max-error", type=float, default=DEFAULT_MAX_ERROR, help="拟合允许最大误差")
    args = parser.parse_args()
    raise SystemExit(_run(apply=args.apply, max_error=args.max_error))


if __name__ == "__main__":
    main()
