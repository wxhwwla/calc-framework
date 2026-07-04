# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""明日方舟 ComputeSheet 配置数据（无 PySide6 依赖）。

从 arknights_compute_sheet.py 拆分而来，可被 Web/CLI/测试复用。
"""

from __future__ import annotations

from typing import Any

# DamageApp 右栏 ComputeSheet：额外加成(ATK%/伤害%) + 敌人 + 信赖/潜能
DAMAGE_APP_SHEET_SECTION_IDS: frozenset[str] = frozenset({"enemy", "extra_bonuses"})
DAMAGE_APP_BONUS_VARS: tuple[str, ...] = (
    "user_input.攻击力百分比加成",
    "user_input.伤害加成",
)

# layout.json 中 user_input 变量定义（与终末地 compute_sheet_variables 模式一致）
ARKNIGHTS_USER_VARS: dict[str, dict[str, Any]] = {
    "user_input.技能倍率": {
        "source": "user_input",
        "type": "float",
        "default": 1.0,
        "min": 0.0,
        "max": 10.0,
        "step": 0.01,
    },
    "user_input.技能等级": {
        "source": "user_input",
        "type": "int",
        "default": 7,
        "min": 1,
        "max": 10,
        "step": 1,
    },
    "user_input.敌人防御": {
        "source": "user_input",
        "type": "float",
        "default": 200.0,
        "min": 0,
        "max": 10000,
        "step": 10,
    },
    "user_input.敌人法术抗性": {
        "source": "user_input",
        "type": "float",
        "default": 50.0,
        "min": 0,
        "max": 100,
        "step": 1,
    },
    "user_input.攻击力百分比加成": {
        "source": "user_input",
        "type": "float",
        "default": 0.0,
        "min": -100,
        "max": 200,
        "step": 1,
        "ui_control": {"widget": "spinbox", "step": 1},
    },
    "user_input.伤害加成": {
        "source": "user_input",
        "type": "float",
        "default": 0.0,
        "min": -100,
        "max": 200,
        "step": 1,
        "ui_control": {"widget": "spinbox", "step": 1},
    },
    "user_input.物理穿透": {
        "source": "user_input",
        "type": "float",
        "default": 0.0,
        "min": 0,
        "max": 3000,
        "step": 10,
    },
    "user_input.法术穿透": {
        "source": "user_input",
        "type": "float",
        "default": 0.0,
        "min": 0,
        "max": 1.0,
        "step": 0.01,
    },
    "user_input.信赖攻击": {
        "source": "user_input",
        "type": "float",
        "default": 0,
        "min": 0,
        "max": 500,
        "step": 1,
        "ui_control": {"widget": "spinbox", "step": 1},
    },
    "user_input.潜能攻击": {
        "source": "user_input",
        "type": "float",
        "default": 0,
        "min": 0,
        "max": 500,
        "step": 1,
        "ui_control": {"widget": "spinbox", "step": 1},
    },
}

ARKNIGHTS_USER_CONTEXT_OVERRIDES: dict[str, tuple[str, list[str]]] = {
    "user_input.技能倍率": ("computed.技能倍率", ["override"]),
    "user_input.技能等级": ("computed.技能等级", ["override"]),
    "user_input.敌人防御": ("enemy.防御", ["override"]),
    "user_input.敌人法术抗性": ("enemy.法术抗性", ["override"]),
    "user_input.攻击力百分比加成": ("computed.攻击力百分比加成", ["override"]),
    "user_input.伤害加成": ("computed.伤害加成", ["override"]),
    "user_input.物理穿透": ("computed.物理穿透", ["override"]),
    "user_input.法术穿透": ("computed.法术穿透", ["override"]),
    "user_input.信赖攻击": ("character.信赖攻击", ["override"]),
    "user_input.潜能攻击": ("character.潜能攻击", ["override"]),
}


def combo_index_to_skill_index(combo_index: int) -> int:
    """技能下拉索引 → ``get_parsed_skill_info`` 的 skill_index（0=普攻时为 -1）。"""
    return combo_index - 1 if combo_index > 0 else -1


def merge_atk_percent_bonus(user_pct: float, atk_buff_hint: float) -> float:
    """合并用户 ATK% 与技能解析 buff，与 Web ``handleCompute`` 一致（百分点制）。"""
    return user_pct + atk_buff_hint * 100.0
