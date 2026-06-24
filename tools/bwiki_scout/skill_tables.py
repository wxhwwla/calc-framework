#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0

# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""从干员主页 HTML 解析技能等级倍率表（1–9 + 专1–3）及段伤害类型。"""

from __future__ import annotations


import io

import re

import sys

from contextlib import redirect_stdout

from dataclasses import dataclass

from html.parser import HTMLParser

from pathlib import Path

from typing import Any


_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

_PKG = _REPO_ROOT / "games" / "endfield"

if str(_PKG) not in sys.path:
    sys.path.insert(0, str(_PKG))


from games.endfield.calc.damage.types import infer_segment_damage_type

from games.endfield.calc.damage.formula import calculate_skill_curve

from games.endfield.calc.damage.inverse import fit_skill_formula


_PERCENT_RE = re.compile(r"([\d.]+)\s*%?")

_SKIP_ROW_KEYWORDS = ("失衡", "技力", "消耗", "冷却", "范围")


@dataclass(frozen=True)
class ParsedSkillDamageRow:
    """单行伤害倍率 + 推断的段伤害类型。"""

    curve: list[float]

    damage_type: str

    raw_header: str


class _SkillTableParser(HTMLParser):
    """收集技能区各 tab 内「伤害倍率」等行的 12 格数值与行标题。"""

    def __init__(self) -> None:
        super().__init__()

        self._div_classes: list[str] = []

        self._tab_tables: list[list[ParsedSkillDamageRow]] = []

        self._tab_rows: list[ParsedSkillDamageRow] = []

        self._current_table: list[ParsedSkillDamageRow] | None = None

        self._in_tr = False

        self._in_th = False

        self._row_header = ""

        self._row_cells: list[str] = []

        self._capture_row = False

    def _in_skill_block(self) -> bool:
        """_in_skill_block 实现。"""
        return any("skill" in (c or "").split() for c in self._div_classes)

    def _in_tab_content(self) -> bool:
        """_in_tab_content 实现。"""
        return self._in_skill_block() and any("tab-content" in (c or "").split() for c in self._div_classes)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """handle_starttag 实现。

        Args:
            tag: 参数描述。
            attrs: 参数描述。

        Returns:
            返回值描述。
        """
        attrs_dict = dict(attrs)

        cls = attrs_dict.get("class") or ""

        if tag == "div":
            self._div_classes.append(cls)

            if "tab-content" in cls.split() and self._in_skill_block():
                self._tab_rows = []

        if self._in_tab_content() and tag == "table" and "wikitable" in cls.split():
            self._current_table = []

        if self._in_tab_content() and tag == "tr":
            self._in_tr = True

            self._row_header = ""

            self._row_cells = []

            self._capture_row = False

        if self._in_tr and tag == "th":
            self._in_th = True

    def handle_endtag(self, tag: str) -> None:
        """handle_endtag 实现。

        Args:
            tag: 参数描述。

        Returns:
            返回值描述。
        """
        if tag == "th":
            self._in_th = False

        if tag == "tr" and self._in_tr:
            self._in_tr = False

            if self._capture_row and self._row_cells and self._current_table is not None:
                parsed = _finalize_damage_row(self._row_header, self._row_cells)

                if parsed is not None:
                    self._current_table.append(parsed)

            self._capture_row = False

        if tag == "table" and self._current_table is not None and self._in_tab_content():
            if self._current_table:
                self._tab_rows.extend(self._current_table)

            self._current_table = None

        if tag == "div" and self._div_classes:
            closing = self._div_classes.pop()

            if "tab-content" in closing.split() and self._tab_rows:
                self._tab_tables.append(self._tab_rows)

                self._tab_rows = []

    def handle_data(self, data: str) -> None:
        """handle_data 实现。

        Args:
            data: 参数描述。

        Returns:
            返回值描述。
        """
        text = data.strip()

        if not text or not self._in_tr:
            return

        if self._in_th:
            self._row_header += text

            if _is_damage_multiplier_row(self._row_header):
                self._capture_row = True

        elif self._capture_row:
            self._row_cells.append(text)


def _parse_percent_cell(text: str) -> float:
    """_parse_percent_cell 实现。"""
    m = _PERCENT_RE.search(text.replace(",", ""))

    if not m:
        return 0.0

    return float(m.group(1))


def _cell_looks_numeric(text: str) -> bool:
    """_cell_looks_numeric 实现。"""
    return bool(_PERCENT_RE.search(text.replace(",", "")))


def _finalize_damage_row(header: str, cells: list[str]) -> ParsedSkillDamageRow | None:
    """_finalize_damage_row 实现。"""
    numeric: list[float] = []

    extra_text: list[str] = []

    for cell in cells:
        if _cell_looks_numeric(cell):
            numeric.append(_parse_percent_cell(cell))

        elif cell.strip():
            extra_text.append(cell.strip())

    if len(numeric) != 12:
        return None

    damage_type = infer_segment_damage_type(header, *extra_text)

    return ParsedSkillDamageRow(curve=numeric, damage_type=damage_type, raw_header=header.strip())


def _is_damage_multiplier_row(header: str) -> bool:
    """_is_damage_multiplier_row 实现。"""
    if "倍率" not in header or "伤害" not in header:
        return False

    return not any(k in header for k in _SKIP_ROW_KEYWORDS)


def parse_skill_damage_rows_from_html(html: str) -> list[list[ParsedSkillDamageRow]]:
    """

    解析技能区每个 tab 的伤害倍率行。



    返回 ``[tab_index][row_index]``；仅含出现「伤害倍率」行的 tab，按顺序对应 sk1/sk2/sk3。

    """

    parser = _SkillTableParser()

    parser.feed(html)

    return parser._tab_tables


def skill_tabs_to_seed_skills(
    tab_tables: list[list[ParsedSkillDamageRow]],
) -> dict[str, list[Any]]:
    """将 HTML tab 转为 seed 的 sk1/sk2/sk3 与平行 sk*_dt 段伤害类型列表。"""

    out: dict[str, list[Any]] = {}

    keys = ("sk1", "sk2", "sk3")

    dt_keys = ("sk1_dt", "sk2_dt", "sk3_dt")

    for idx, table in enumerate(tab_tables[:3]):
        sk_key = keys[idx]

        dt_key = dt_keys[idx]

        curves: list[dict[str, Any]] = []

        damage_types: list[str] = []

        for row in table:
            if len(row.curve) != 12:
                continue

            curves.append(fit_skill_params_from_curve(row.curve))

            damage_types.append(row.damage_type)

        out[sk_key] = curves

        out[dt_key] = damage_types

    for key in keys:
        out.setdefault(key, [])

    for dt_key in dt_keys:
        out.setdefault(dt_key, [])

    return out


def fit_skill_params_from_curve(curve12: list[float]) -> dict[str, Any]:
    """12 级技能倍率反推为 seed 参数（含 special 专1–3）。"""

    if len(curve12) != 12:
        raise ValueError(f"技能曲线长度应为 12，实际 {len(curve12)}")

    with redirect_stdout(io.StringIO()):
        base, growth, divisor, offset, special = fit_skill_formula(curve12)

    return {
        "base": base,
        "growth": growth,
        "divisor": divisor,
        "offset": offset,
        "special": list(special),
    }


def verify_skill_params(params: dict[str, Any]) -> list[float]:
    """反推参数生成 12 级曲线，供测试与对比。"""

    return calculate_skill_curve(
        **{k: params[k] for k in ("base", "growth", "divisor", "offset")},
        special_values=params.get("special"),
    )
