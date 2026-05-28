#!/usr/bin/env python3
"""
乘区计算模块

此模块包含所有乘区的定义和计算逻辑。

乘区是游戏伤害计算公式中的乘法因子区域，包括：
- 攻击倍率区
- 伤害加成区
- 防御减伤区
- 抗性减伤区
- 能力值加成区
- 最终攻击力区
- 等等

接缝说明：
- **右侧乘区 GUI**：``zone_snapshot.compute_multiplicative_zone_snapshot`` + 各 ``calculate_*_with_details``；
- **单段伤害 / 全量搜索评分**：``calculation.damage.engine``（15 乘区连乘）；
- **最终攻击力共用 seam**：``calculation.loadout.attack_eval.final_attack_details_for_loadout``（搜索重算与预设对比）；
- **武器技能选用**：``calculation.skills.weapon_selection.WeaponSkillSelection``；
- ``ZoneManager`` 为历史演示路径，生产 GUI/搜索不经过该类。
"""

from .ability_bonus_calc import calculate_ability_bonus
from .ability_bonus_details import calculate_ability_bonus_with_details
from .ability_bonus_calc import AbilityBonusZone
from .attribute_zone import (
    AttributeMultiplierZone,
    AttributeZoneManager,
    calculate_attribute_zones,
    calculate_attribute_zones_with_details,
)
from .base_zone import BaseZone, DefenseReductionZone
from .final_attack_zone import FinalAttackZone, calculate_final_attack, calculate_final_attack_with_details
from .zone_manager import ZoneManager
from .zone_snapshot import (
    MultiplicativeZoneSelection,
    WeaponBonusSelection,
    ZoneDisplayLine,
    compute_multiplicative_zone_snapshot,
)

__all__ = [
    "AbilityBonusZone",
    "AttributeMultiplierZone",
    "AttributeZoneManager",
    "BaseZone",
    "DefenseReductionZone",
    "FinalAttackZone",
    "MultiplicativeZoneSelection",
    "WeaponBonusSelection",
    "ZoneDisplayLine",
    "ZoneManager",
    "calculate_ability_bonus",
    "calculate_ability_bonus_with_details",
    "calculate_attribute_zones",
    "calculate_attribute_zones_with_details",
    "calculate_final_attack",
    "calculate_final_attack_with_details",
    "compute_multiplicative_zone_snapshot",
]
