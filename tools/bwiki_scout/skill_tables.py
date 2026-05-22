#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从干员主页 HTML 解析技能等级倍率表（1–9 + 专1–3）。"""

from __future__ import annotations

import io
import re
import sys
from contextlib import redirect_stdout
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_PKG = _REPO_ROOT / "endfield_damage_calculator"
if str(_PKG) not in sys.path:
    sys.path.insert(0, str(_PKG))

from calculation.formula import calculate_skill_curve  # noqa: E402
from calculation.inverse import fit_skill_formula  # noqa: E402

_PERCENT_RE = re.compile(r"([\d.]+)\s*%?")
_SKIP_ROW_KEYWORDS = ("失衡", "技力", "消耗", "冷却", "范围")


class _SkillTableParser(HTMLParser):
    """收集技能区各 tab 内「伤害倍率」等行的 12 格数值。"""

    def __init__(self) -> None:
        super().__init__()
        self._div_classes: list[str] = []
        self._tab_tables: list[list[list[float]]] = []
        self._tab_rows: list[list[float]] = []
        self._current_table: list[list[float]] | None = None
        self._in_tr = False
        self._in_th = False
        self._row_header = ""
        self._row_cells: list[str] = []
        self._capture_row = False

    def _in_skill_block(self) -> bool:
        return any("skill" in (c or "").split() for c in self._div_classes)

    def _in_tab_content(self) -> bool:
        return self._in_skill_block() and any(
            "tab-content" in (c or "").split() for c in self._div_classes
        )

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
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
        if tag == "th":
            self._in_th = False
        if tag == "tr" and self._in_tr:
            self._in_tr = False
            if self._capture_row and self._row_cells and self._current_table is not None:
                values = [_parse_percent_cell(c) for c in self._row_cells]
                if len(values) == 12:
                    self._current_table.append(values)
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
    m = _PERCENT_RE.search(text.replace(",", ""))
    if not m:
        return 0.0
    return float(m.group(1))


def _is_damage_multiplier_row(header: str) -> bool:
    if "倍率" not in header or "伤害" not in header:
        return False
    return not any(k in header for k in _SKIP_ROW_KEYWORDS)


def parse_skill_damage_rows_from_html(html: str) -> list[list[list[float]]]:
    """
    解析技能区每个 tab 的伤害倍率行。

    返回 ``[tab_index][row_index][12]``；仅含出现「伤害倍率」行的 tab，按顺序对应 sk1/sk2/sk3。
    """
    parser = _SkillTableParser()
    parser.feed(html)
    return parser._tab_tables


def skill_tabs_to_seed_skills(
    tab_tables: list[list[list[float]]],
) -> dict[str, list[dict[str, Any]]]:
    """
    将 HTML tab 转为 seed 的 sk1/sk2/sk3。

    每个 tab 取所有「伤害倍率」行（无该行的普攻 tab 不会出现在 ``tab_tables``）。
    """
    tabs = tab_tables
    out: dict[str, list[dict[str, Any]]] = {}
    keys = ("sk1", "sk2", "sk3")
    for idx, table in enumerate(tabs[:3]):
        key = keys[idx]
        curves: list[dict[str, Any]] = []
        for row in table:
            if len(row) != 12:
                continue
            curves.append(fit_skill_params_from_curve(row))
        out[key] = curves
    for key in keys:
        out.setdefault(key, [])
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
