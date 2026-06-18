# SPDX-License-Identifier: AGPL-3.0
"""MOBA 适配器 — 数据上下文加载器。"""

from __future__ import annotations

from calc_framework.data.attr_schema import AttributeSchema
from calc_framework.data.context import DataContext, make_context
from calc_framework.data.loader import DataContextLoader


class MobaLoader(DataContextLoader):
    """MOBA 适配器的 DataContext 构建器。"""

    def __init__(self, attr_schema: AttributeSchema | None = None):
        self._schema = attr_schema

    def build_context(self, **kwargs) -> DataContext:
        if self._schema:
            return self._schema.resolve(kwargs.get("raw_data", {}))

        return make_context(
            character={
                "attack_damage": kwargs.get("attack_damage", 60),
                "ability_power": kwargs.get("ability_power", 0),
                "armor": kwargs.get("armor", 30),
                "magic_resist": kwargs.get("magic_resist", 30),
                "cooldown_reduction": kwargs.get("cooldown_reduction", 0),
                "attack_speed_bonus": kwargs.get("attack_speed_bonus", 0),
                "crit_rate": kwargs.get("crit_rate", 0),
                "crit_dmg": kwargs.get("crit_dmg", 1.75),
                "lethality": kwargs.get("lethality", 0),
                "armor_pen_pct": kwargs.get("armor_pen_pct", 0),
                "magic_pen": kwargs.get("magic_pen", 0),
                "magic_pen_pct": kwargs.get("magic_pen_pct", 0),
            },
            enemy={
                "armor": kwargs.get("enemy_armor", 50),
                "magic_resist": kwargs.get("enemy_magic_resist", 30),
            },
            user_input={
                "skill_base_damage": kwargs.get("skill_base_damage", 100),
                "ad_ratio": kwargs.get("ad_ratio", 0),
                "ap_ratio": kwargs.get("ap_ratio", 0),
                "is_physical": kwargs.get("is_physical", True),
                "is_crit": kwargs.get("is_crit", False),
                "skill_cooldown": kwargs.get("skill_cooldown", 10),
            },
        )
