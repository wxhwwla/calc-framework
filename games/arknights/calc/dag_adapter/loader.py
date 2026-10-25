# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""明日方舟 DataContext 加载器 — 实现框架的 DataContextLoader 接口。"""

from __future__ import annotations

from typing import Any

from calc_framework.data.context import make_context
from calc_framework.data.loader import DataContextLoader

from games.arknights.calc.inverse.stats import resolve_stats_from_segments


class ArknightsContextLoader(DataContextLoader):
    """从明日方舟干员原始数据构建 DataContext。

    用法::

        loader = ArknightsContextLoader()
        ctx = loader.build_context(
            operator=operator_dict,
            skill_level=7,
            enemy_def=200.0,
            enemy_res=50.0,
            atk_percent_bonus=0.0,
            dmg_bonus=0.0,
            def_penetration=0.0,
            res_penetration=0.0,
        )
    """

    def build_context(self, **kwargs: Any) -> dict[str, Any]:
        """从干员数据构建 DAG 计算上下文。

        参数:
            **kwargs: 包含 operator, skill_level, enemy_def,
                      enemy_res, atk_percent_bonus 等键。

        返回:
            符合框架 DataContext 格式的字典。
        """
        operator: dict[str, Any] = kwargs["operator"]
        kwargs.get("skill_level", 7)
        enemy_def: float = kwargs.get("enemy_def", 200.0)
        enemy_res: float = kwargs.get("enemy_res", 50.0)
        atk_pct: float = kwargs.get("atk_percent_bonus", 0.0)
        dmg_bonus: float = kwargs.get("dmg_bonus", 0.0)
        def_pen: float = kwargs.get("def_penetration", 0.0)
        res_pen: float = kwargs.get("res_penetration", 0.0)
        skill_mult: float = kwargs.get("skill_multiplier", 1.0)

        base_stats = operator.get("基础属性", {})
        trust_bonus = operator.get("信赖加成", {})
        potentials = operator.get("潜能", [])

        elite = int(kwargs.get("elite", 2))
        operator_level = kwargs.get("operator_level")
        seg_stats = resolve_stats_from_segments(
            operator,
            elite=elite,
            level=int(operator_level) if operator_level is not None else None,
        )

        base_atk = float(seg_stats["atk"]) if "atk" in seg_stats else _get_num(base_stats, "atk")
        base_def = float(seg_stats["def"]) if "def" in seg_stats else _get_num(base_stats, "def")
        base_res = float(seg_stats["res"]) if "res" in seg_stats else _get_num(base_stats, "res", 0.0)

        trust_override = kwargs.get("trust_atk_override")
        if trust_override is not None:
            trust_atk = float(trust_override)
        else:
            trust_atk = _get_num(trust_bonus, "攻击", 0.0)

        pot_override = kwargs.get("pot_atk_override")
        if pot_override is not None:
            pot_atk = float(pot_override)
        else:
            pot_atk = _parse_potential_atk(potentials)

        return make_context(
            character={
                "攻击力": base_atk,
                "防御": base_def,
                "法术抗性": base_res,
                "信赖攻击": trust_atk,
                "潜能攻击": pot_atk,
            },
            enemy={
                "防御": enemy_def,
                "法术抗性": enemy_res,
            },
            computed={
                "技能倍率": skill_mult,
                "攻击力百分比加成": atk_pct,
                "伤害加成": dmg_bonus,
                "物理穿透": def_pen,
                "法术穿透": res_pen,
            },
        )


def _get_num(d: dict[str, Any], key: str, default: float = 0.0) -> float:
    """从 dict 中提取数值。"""
    try:
        return float(d.get(key, default))
    except (TypeError, ValueError):
        return float(default)


def _parse_potential_atk(potentials: list[str]) -> float:
    """从潜能描述中提取攻击力加成。

    例如 "攻击力+12" → 12.0, "部署费用-1" → 0.0
    """
    total = 0.0
    for p in potentials:
        p = p.strip()
        if p.startswith("攻击力+"):
            try:
                total += float(p.replace("攻击力+", "").strip())
            except ValueError:
                continue
    return total
