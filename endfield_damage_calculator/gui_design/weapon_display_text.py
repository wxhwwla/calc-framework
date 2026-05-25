#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""武器技能/词条展示文案（无 CustomTkinter）。"""

from __future__ import annotations

import re

_EFFECT_NAME_RE = re.compile(r'([^\s，。；:：,\.()（）"“”\[\]【】]+?\+)')
_SIMPLE_EFFECT_NAME_RE = re.compile(r'^[^\s，。；:：,\.()（）"“”\[\]【】]+?\+$')


def format_weapon_skill_title(prefix: str, attr_name: str = "") -> str:
    """武器技能行标题，例如「第一技能：智识+」；无属性时为「第三技能：无」。"""
    name = (attr_name or "").strip()
    if name:
        return f"{prefix}：{name}"
    return f"{prefix}：无"


def format_weapon_skill_slider_value(*, active: bool, level: int = 0) -> str:
    """武器技能滑块右侧数值；无该条技能时与特殊技能一致显示 0。"""
    if not active:
        return "0"
    return str(level)


def extract_effect_display_name(raw_name: str) -> str:
    """从条件描述中提取词条展示名（仅效果，不含触发条件），供 UI 展示。"""
    name = (raw_name or "").strip()
    if not name:
        return ""

    received = re.search(r"受到的\s*([^，。；]+?\+)\s*$", name)
    if received:
        return received.group(1).strip()

    for prefix in (
        "目标受到的",
        "目标获得",
        "使目标受到的",
        "使目标获得",
        "装备者获得的",
        "装备者",
    ):
        if name.startswith(prefix) and name.endswith("+"):
            trimmed = name[len(prefix) :].strip()
            if trimmed.endswith("+") and len(trimmed) <= 24:
                return trimmed

    if _SIMPLE_EFFECT_NAME_RE.fullmatch(name) and len(name) <= 16:
        return name

    matches = _EFFECT_NAME_RE.findall(name)
    if matches:
        candidate = matches[-1]
        for marker in ("时获得", "获得", "时", "使", "造成", "提高", "提升", "降低", "增加"):
            if marker in candidate:
                tail = candidate.split(marker)[-1].strip()
                if tail.endswith("+"):
                    candidate = tail
        return candidate
    return name


def split_special_skill_display(raw_name: str) -> tuple[str, str]:
    """
    拆分特殊技能展示文案：返回 (条件行, 效果行)。

    - 条件行用于第一行展示（可为空）
    - 效果行始终尽量返回 ``xxx+``（由 ``extract_effect_display_name`` 提取）
    """
    name = (raw_name or "").strip()
    if not name:
        return "", ""
    effect = extract_effect_display_name(name)
    if not effect:
        return "", name
    if name == effect:
        return "", effect
    if effect not in name:
        return "", effect
    condition = name[: name.rfind(effect)].strip("，。；:：, ")
    for marker in ("时获得", "获得", "提高", "提升", "增加", "降低", "使得", "使"):
        if condition.endswith(marker):
            condition = condition[: -len(marker)].strip("，。；:：, ")
            break
    if condition in {
        "目标受到的",
        "目标获得",
        "使目标受到的",
        "使目标获得",
        "装备者",
        "装备者获得的",
    }:
        condition = ""
    return condition, effect
