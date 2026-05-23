#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全量搜索预估文案（无 CustomTkinter，供单测与 search_controls 共用）。"""

from __future__ import annotations

from typing import Optional


def compose_search_estimate_message(
    *,
    has_char: bool,
    has_weapon: bool,
    catalog_err: Optional[str],
    weapons_empty: bool,
    job_error: Optional[str],
    estimate_text: Optional[str],
) -> str:
    """根据前置检查结果生成「预计组合数」标签文案（无 GUI 副作用）。"""
    if not has_char or not has_weapon:
        return "预计组合数：请先选择角色和武器"
    if catalog_err:
        return f"预计组合数：{catalog_err.split('。')[0]}"
    if weapons_empty:
        return "预计组合数：当前武器候选为空"
    if job_error:
        return f"预计组合数：{job_error}"
    if estimate_text:
        return estimate_text
    return "预计组合数：无法预估"
