#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""全量搜索用的多技能加权评分配置（与快速预览共用倍率/次数语义）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from calc_engine.endfield.calc.multi_skill.optimizer import SkillScenario
from calc_engine.endfield.calc.skills.segments import (
    build_segment_scenarios_from_levels,
    format_segment_count_label,
    scenario_counts_for_eval,
    segment_key,
)


def skill_multiplier_from_curve(
    char_data: dict[str, Any],
    field_name: str,
    level: int,
) -> float:
    """从技能曲线读取第一段倍率（小数）。"""
    from calc_engine.endfield.calc.skills.segments import segment_multiplier_at_level

    value = segment_multiplier_at_level(
        char_data,
        field_name,
        skill_level=level,
        segment_index=1,
    )
    return value if value is not None else 0.0


def build_skill_scenarios_from_levels(
    char_data: dict[str, Any],
    *,
    skill_1_level: int,
    skill_2_level: int,
    skill_3_level: int,
) -> list[SkillScenario]:
    """按左侧技能等级构建全部有效段场景。"""
    return build_segment_scenarios_from_levels(
        char_data,
        skill_1_level=skill_1_level,
        skill_2_level=skill_2_level,
        skill_3_level=skill_3_level,
    )


def format_multi_skill_count_label(skill_counts: dict[str, int]) -> str:
    """生成弹窗/作业用的次数说明。"""
    return format_segment_count_label(skill_counts)


@dataclass(frozen=True)
class MultiSkillSearchEval:
    """全量遍历按加权总伤排序时的场景与次数。"""

    scenarios: tuple[SkillScenario, ...]
    skill_counts: dict[str, int]

    @property
    def priority_skill_types(self) -> tuple[str, ...]:
        active_keys = {key for key, c in self.skill_counts.items() if c > 0}
        return tuple(dict.fromkeys(s.resolved_skill_type for s in self.scenarios if s.scenario_key in active_keys))

    def signature_token(self) -> str:
        """写入 run_signature，避免与单技能或不同次数混库。"""
        count_part = "|".join(
            f"{key}:{max(0, int(self.skill_counts.get(key, 0)))}" for key in sorted(self.skill_counts.keys())
        )
        mult_part = "|".join(f"{s.scenario_key}:{s.skill_multiplier:.6f}" for s in self.scenarios)
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
) -> tuple[MultiSkillSearchEval | None, str | None]:
    """
    从角色技能等级与手动次数组装全量搜索评分配置。

    返回 (eval, None) 或 (None, 错误文案)。
    """
    scenarios = build_skill_scenarios_from_levels(
        char_data,
        skill_1_level=skill_1_level,
        skill_2_level=skill_2_level,
        skill_3_level=skill_3_level,
    )
    if not scenarios:
        scenarios = [
            SkillScenario(
                skill_name=segment_key("战技", 1),
                skill_multiplier=1.0,
                skill_type="战技",
                segment_index=1,
            )
        ]
    try:
        counts = scenario_counts_for_eval(
            manual_counts,
            scenarios,
            use_manual=True,
        )
    except ValueError as exc:
        return None, str(exc)
    active = {k: v for k, v in counts.items() if v > 0}
    if not active:
        return None, "手动次数不能全为 0，请至少设置一项 > 0。"
    return (
        MultiSkillSearchEval(scenarios=tuple(scenarios), skill_counts=active),
        None,
    )
