# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""从 AI 文本响应中提取完整配方 JSON，不提升嵌套对象。"""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from typing import Any

_RECIPE_KEYS = frozenset({"variables", "formula_steps", "outputs"})
_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)


def _as_recipe(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict) and any(key in value for key in _RECIPE_KEYS):
        return value
    return None


def _decode_object(text: str) -> dict[str, Any] | None:
    try:
        return _as_recipe(json.loads(text.strip()))
    except (json.JSONDecodeError, TypeError):
        return None


def _outer_object_spans(text: str) -> Iterator[str]:
    """返回文本中最外层对象的片段；数组和损坏外层中的内层对象不返回。"""
    depth = 0
    start: int | None = None
    in_string = False
    escaped = False
    for index, char in enumerate(text):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
            continue
        if char in "[{":
            if char == "{" and depth == 0:
                start = index
            depth += 1
            continue
        if char not in "]}" or depth == 0:
            continue
        depth -= 1
        if depth == 0 and start is not None:
            if char == "}":
                yield text[start : index + 1]
            start = None


def extract_ai_json(content: str) -> dict[str, Any] | None:
    """提取含配方字段的顶层对象；无法确定边界时返回 None。"""
    direct = _decode_object(content)
    if direct is not None:
        return direct
    stripped = content.strip()
    if stripped.startswith(("{", "[")):
        return None

    for match in _FENCE_RE.finditer(content):
        fenced = _decode_object(match.group(1))
        if fenced is not None:
            return fenced

    best: dict[str, Any] | None = None
    best_score = 0
    for span in _outer_object_spans(content):
        candidate = _decode_object(span)
        if candidate is None:
            continue
        score = sum(key in candidate for key in _RECIPE_KEYS)
        if score >= best_score:
            best = candidate
            best_score = score
    return best
