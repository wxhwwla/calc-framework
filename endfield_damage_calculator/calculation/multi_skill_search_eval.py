#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全量搜索用的多技能加权评分配置（与快速预览共用倍率/次数语义）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from calculation.multi_skill_optimizer import SkillScenario


def skill_multiplier_from_curve(
    char_data: dict[str, Any],
    field_name: str,
    level: int,
) -> float:
    """从技能曲线读取第一段倍率（小数）。"""
    if level <= 0:
        return 0.0
    segments = char_data.get(field_name)
    if not isinstance(segments, list) or not segments:
        return 0.0
    first_segment = segments[0]
    if not isinstance(first_segment, list) or not first_segment:
        return 0.0
    idx = level - 1
    if not (0 <= idx < len(first_segment)):
        return 0.0
    value = first_segment[idx]
    if value is None:
        return 0.0
    return float(value) / 100.0


def build_skill_scenarios_from_levels(
    char_data: dict[str, Any],
    *,
    skill_1_level: int,
    skill_2_level: int,
    skill_3_level: int,
) -> list[SkillScenario]:
    """按左侧技能等级构建战技/连携/终结场景。"""
    multipliers = {
        "战技": skill_multiplier_from_curve(char_data, "战技倍率", skill_1_level),
        "连携技": skill_multiplier_from_curve(char_data, "连携技倍率", skill_2_level),
        "终结技": skill_multiplier_from_curve(char_data, "终结技倍率", skill_3_level),
    }
    return [
        SkillScenario(skill_name=name, skill_multiplier=val, skill_type=name)
        for name, val in multipliers.items()
        if val > 0
    ]


def format_multi_skill_count_label(skill_counts: dict[str, int]) -> str:
    """生成弹窗/作业用的次数说明。"""
    parts = [
        f"{name}×{max(0, int(skill_counts.get(name, 0)))}"
        for name in ("战技", "连携技", "终结技")
        if int(skill_counts.get(name, 0)) > 0
    ]
    return " + ".join(parts) if parts else "（无有效次数）"


@dataclass(frozen=True)
class MultiSkillSearchEval:
    """全量遍历按加权总伤排序时的场景与次数。"""

    scenarios: tuple[SkillScenario, ...]
    skill_counts: dict[str, int]

    @property
    def priority_skill_types(self) -> tuple[str, ...]:
        active = {s.skill_name for s in self.scenarios if self.skill_counts.get(s.skill_name, 0) > 0}
        return tuple(
            dict.fromkeys(
                (s.skill_type or s.skill_name for s in self.scenarios if s.skill_name in active)
            )
        )

    def signature_token(self) -> str:
        """写入 run_signature，避免与单技能或不同次数混库。"""
        count_part = "|".join(
            f"{name}:{max(0, int(self.skill_counts.get(name, 0)))}"
            for name in ("战技", "连携技", "终结技")
        )
        mult_part = "|".join(
            f"{s.skill_name}:{s.skill_multiplier:.6f}" for s in self.scenarios
        )
        return f"multi({count_part};{mult_part})"

    @property
    def display_label(self) -> str:
        return f"加权总伤（{format_multi_skill_count_label(self.skill_counts)}）"


def build_multi_skill_search_eval(
    char_data: dict[str, Any],
    *,
    skill_1_level: int,
    skill_2_level: int,
    skill_3_level: int,
    manual_counts: dict[str, int],
) -> tuple[Optional[MultiSkillSearchEval], Optional[str]]:
    """
    从角色技能等级与手动次数组装全量搜索评分配置。

    返回 (eval, None) 或 (None, 错误文案)。
    """
    counts = {
        "战技": max(0, int(manual_counts.get("战技", 0))),
        "连携技": max(0, int(manual_counts.get("连携技", 0))),
        "终结技": max(0, int(manual_counts.get("终结技", 0))),
    }
    if all(v == 0 for v in counts.values()):
        return None, "手动次数不能全为 0，请至少设置一项 > 0。"

    scenarios = build_skill_scenarios_from_levels(
        char_data,
        skill_1_level=skill_1_level,
        skill_2_level=skill_2_level,
        skill_3_level=skill_3_level,
    )
    if not scenarios:
        scenarios = [SkillScenario(skill_name="战技", skill_multiplier=1.0, skill_type="战技")]
    return (
        MultiSkillSearchEval(scenarios=tuple(scenarios), skill_counts=counts),
        None,
    )
