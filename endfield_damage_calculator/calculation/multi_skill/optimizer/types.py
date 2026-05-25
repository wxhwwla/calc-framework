#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多技能加权总伤优化模块。

核心功能：支持多技能场景下的配装搜索，按加权总伤害评分。

评分公式：
    总伤 = Σ(单技能单次伤害 × 该技能释放次数)

设计目标：
- 快速预览与全量遍历共用统一的评分语义
- 支持段级（segment-level）技能定义和次数配置
- 支持外部效果注入（如队伍buff、环境效果等）

关键数据结构：
- SkillScenario: 单个技能段场景定义（技能名称、倍率、类型、段索引、外部效果）
- MultiSkillConfig: 多技能配置（Top-N、选中技能、技能次数映射、暴击模式）
- MultiSkillScore: 单条配装的多技能评分（含各段伤害明细）
- MultiSkillResult: 搜索结果汇总

场景键格式："技能类型:段索引"（如 "战技:1"、"普攻:2"）
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from calculation.damage.engine import CritMode, DamageContext, DamageEffect, calculate_single_hit_damage
from calculation.equipment.affix import aggregate_loadout_modifiers
from calculation.loadout.optimizer import (
    LoadoutScore,
    OptimizerConfig,
    OptimizerTask,
    WeaponCandidate,
    enumerate_optimizer_tasks,
)
from calculation.multiplicative_zones.final_attack_zone import calculate_final_attack_with_details
from calculation.search.evaluate.context import SearchEvalContext
from calculation.equipment.prune import character_ability_attrs
from calculation.equipment.system import build_four_slot_loadout, collect_loadout_effects


@dataclass(frozen=True)
class SkillScenario:
    """单个技能段场景定义。

    表示技能的一个分段（segment），包含倍率、类型和可选的外部效果。

    Attributes:
        skill_name: 技能名称，支持 "技能类型:段索引" 格式（如 "战技:2"）
        skill_multiplier: 技能倍率
        skill_type: 技能类型（普攻/战技/终结技等），若 skill_name 包含 ":" 则从其中解析
        segment_index: 段索引，用于区分同一技能的不同段（如战技第一段、第二段）
        external_effects: 外部效果（如队伍buff、环境效果），在计算时追加到装备效果后
    """

    skill_name: str
    skill_multiplier: float
    skill_type: str = ""
    segment_index: int = 1
    damage_type: str = ""
    damage_type_explicit: bool = False
    external_effects: tuple[DamageEffect, ...] = ()

    @property
    def scenario_key(self) -> str:
        """段级键，用于次数映射和伤害明细的键。

        Returns:
            格式为 "技能类型:段索引" 的字符串
        """
        if ":" in self.skill_name:
            return self.skill_name
        skill = self.skill_type or self.skill_name
        return f"{skill}:{self.segment_index}"

    @property
    def resolved_skill_type(self) -> str:
        """解析后的技能类型，用于装备加成匹配和伤害上下文。

        Returns:
            技能类型字符串（优先从 skill_name 解析，其次使用 skill_type）
        """
        if ":" in self.skill_name:
            return self.skill_name.split(":", 1)[0]
        return self.skill_type or self.skill_name

    @property
    def resolved_segment_index(self) -> int:
        """解析后的段索引。

        Returns:
            段索引（优先从 skill_name 解析，其次使用 segment_index）
        """
        if ":" in self.skill_name:
            try:
                return max(1, int(self.skill_name.split(":", 1)[1]))
            except ValueError:
                return 1
        return max(1, self.segment_index)


def resolve_scenario_damage_type(scenario: SkillScenario, base_context: DamageContext) -> str:
    if scenario.damage_type:
        return scenario.damage_type
    return base_context.damage_type


@dataclass(frozen=True)
class MultiSkillConfig:
    """多技能次数加权配置。

    控制多技能搜索的行为和参数。

    Attributes:
        top_n: 返回前 N 个最优结果
        selected_skill: 选中的技能类型（用于默认次数分配）
        skill_counts: 技能次数映射，键为场景键（如 "战技:1"），值为释放次数
        crit_mode: 暴击模式（non_crit/expected/always_crit）
    """

    top_n: int = 10
    selected_skill: str = "战技"
    skill_counts: Optional[dict[str, int]] = None
    crit_mode: str = "non_crit"


@dataclass(frozen=True)
class MultiSkillScore:
    """单条配装的多技能评分结果。

    包含该配装在所有技能场景下的伤害明细和加权总伤害。

    Attributes:
        weapon_name: 武器名称
        loadout_names: 四格配装的名称字典
        skill_breakdown: 各技能段的单次伤害明细
        weighted_total_damage: 加权总伤害（Σ 单次伤害 × 次数）
    """

    weapon_name: str
    loadout_names: dict[str, str]
    skill_breakdown: dict[str, float]
    weighted_total_damage: float


@dataclass(frozen=True)
class MultiSkillResult:
    """多技能搜索结果汇总。

    Attributes:
        top_results: Top-N 最优配装列表
        skill_count_map: 技能次数映射（场景键 → 次数）
        total_combinations: 总组合数
    """

    top_results: tuple[MultiSkillScore, ...]
    skill_count_map: dict[str, int]
    total_combinations: int

    @property
    def weight_map(self) -> dict[str, float]:
        """兼容旧测试和调用方，将次数转换为 float 类型。

        Returns:
            技能次数映射（值为 float 类型）
        """
        return {name: float(count) for name, count in self.skill_count_map.items()}


