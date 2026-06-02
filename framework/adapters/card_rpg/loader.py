#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""卡牌RPG DataContext 加载器 — 实现框架的 DataContextLoader 接口。"""

from __future__ import annotationsfrom typing import Anyfrom calc_framework.data.attr_schema import AttributeSchemafrom calc_framework.data.context import make_contextfrom calc_framework.data.loader import DataContextLoaderclass CardRPGLoader(DataContextLoader):
    """从卡牌RPG原始数据构建 DataContext。

    用法::

        loader = CardRPGLoader()
        ctx = loader.build_context(
            character={"ATK": 100, "DEF": 50, "crit_rate": 0.05, "crit_dmg": 0.5},
            weapon={"ATK_bonus": 15},
            enemy={"DEF": 60},
        )
    """

    def __init__(self, attr_schema: AttributeSchema | None = None):
        self._schema = attr_schema

    def build_context(self, **kwargs: Any) -> dict[str, Any]:
        char: dict[str, Any] = kwargs.get("character", {})
        weapon: dict[str, Any] = kwargs.get("weapon", {})
        enemy: dict[str, Any] = kwargs.get("enemy", {})

        if self._schema:
            raw = {
                "character": char,
                "weapon": weapon,
                "enemy": enemy,
            }
            ctx = self._schema.resolve(raw)
            return ctx

        return make_context(
            character={
                "ATK": float(char.get("ATK", 0)),
                "DEF": float(char.get("DEF", 0)),
                "HP": float(char.get("HP", 100)),
                "crit_rate": float(char.get("crit_rate", 0.05)),
                "crit_dmg": float(char.get("crit_dmg", 0.5)),
            },
            weapon={
                "ATK_bonus": float(weapon.get("ATK_bonus", 0)),
            },
            enemy={
                "DEF": float(enemy.get("DEF", 50)),
            },
        )
