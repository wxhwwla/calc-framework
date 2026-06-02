# SPDX-License-Identifier: AGPL-3.0
"""{Game} DataContext 加载器 — 继承 calc_framework.data.loader.DataContextLoader。

TODO: 根据实际游戏数据结构，在 build_context() 中提取属性并组装上下文。
"""

from __future__ import annotations

from typing import Any

from calc_framework.data.context import make_context
from calc_framework.data.loader import DataContextLoader


class TEMPLATEContextLoader(DataContextLoader):
    """从 {Game} 原始数据构建 DataContext。

    用法::

        loader = TEMPLATEContextLoader()
        ctx = loader.build_context(
            character=character_dict,
            weapon=weapon_dict,
            skill_level=7,
            enemy_def=200.0,
            enemy_res=50.0,
        )
    """

    def build_context(self, **kwargs: Any) -> dict[str, Any]:
        # ── 提取输入参数 ────────────────────────────────────
        character: dict[str, Any] = kwargs.get("character", {})
        # weapon: dict[str, Any] = kwargs.get("weapon", {})   # TODO: 按需启用

        skill_level: int = kwargs.get("skill_level", 7)
        enemy_def: float = kwargs.get("enemy_def", 200.0)
        enemy_res: float = kwargs.get("enemy_res", 50.0)

        # ── 从原始数据提取属性 ───────────────────────────────
        # TODO: 替换为实际游戏的数据字段名
        base_atk = float(character.get("atk", 0))
        base_def = float(character.get("def", 0))
        base_hp = float(character.get("hp", 100))

        # 示例：信赖/潜能加成
        trust_atk = float(character.get("trust_atk", 0))
        pot_atk = float(character.get("potential_atk", 0))

        # 示例：攻击力/伤害百分比加成（用户输入）
        atk_pct: float = kwargs.get("atk_percent_bonus", 0.0)
        dmg_bonus: float = kwargs.get("dmg_bonus", 0.0)

        return make_context(
            character={
                "攻击力": base_atk,
                "防御": base_def,
                "生命上限": base_hp,
                "信赖攻击": trust_atk,
                "潜能攻击": pot_atk,
                # TODO: 添加更多角色属性
            },
            enemy={
                "防御": enemy_def,
                "法术抗性": enemy_res,
                # TODO: 添加更多敌方属性
            },
            computed={
                "技能等级": skill_level,
                "攻击力百分比加成": atk_pct,
                "伤害加成": dmg_bonus,
                # TODO: 添加游戏专属计算参数
            },
        )
