# SPDX-License-Identifier: AGPL-3.0
"""FPS 适配器 — 数据上下文加载器。"""

from __future__ import annotations

from calc_framework.data.context import DataContext, make_context
from calc_framework.data.loader import DataContextLoader
from calc_framework.data.attr_schema import AttributeSchema


class FpsLoader(DataContextLoader):
    """FPS 适配器的 DataContext 构建器。"""

    def __init__(self, attr_schema: AttributeSchema | None = None):
        self._schema = attr_schema

    def build_context(self, **kwargs) -> DataContext:
        if self._schema:
            return self._schema.resolve(kwargs.get("raw_data", {}))
        return make_context(
            weapon={
                "base_damage": kwargs.get("base_damage", 30),
                "fire_rate": kwargs.get("fire_rate", 600),
                "mag_size": kwargs.get("mag_size", 30),
                "reload_time": kwargs.get("reload_time", 2.5),
                "decay_start": kwargs.get("decay_start", 15),
                "decay_end": kwargs.get("decay_end", 50),
                "min_damage_ratio": kwargs.get("min_damage_ratio", 0.5),
                "penetration": kwargs.get("penetration", 0),
            },
            enemy={
                "distance": kwargs.get("distance", 20),
                "armor": kwargs.get("armor", 50),
                "head_mult": kwargs.get("head_mult", 2.0),
                "body_mult": kwargs.get("body_mult", 1.0),
            },
            user_input={
                "is_head": kwargs.get("is_head", False),
                "is_limb": kwargs.get("is_limb", False),
                "wall_pen_count": kwargs.get("wall_pen_count", 0),
            },
        )
