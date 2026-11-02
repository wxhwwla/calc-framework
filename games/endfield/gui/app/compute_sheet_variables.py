# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""终末地 ComputeSheet 用户输入变量定义与上下文映射（无 PySide6 依赖）。

从 endfield_actions.py 拆分而来，可被 Web/CLI/测试复用。
"""

from __future__ import annotations

from typing import Any

from games.endfield.calc.damage.break_defense import vulnerability_bonus_from_break_defense
from games.endfield.calc.damage.combo_bonus import combo_zone_multiplier

# 用户输入变量定义（user_input 源）
# 键格式：user_input.<中文变量名>
ENDFIELD_USER_INPUT_VARIABLES: dict[str, dict[str, Any]] = {
    "user_input.敌人防御": {
        "source": "user_input",
        "type": "float",
        "default": 100.0,
        "min": 0,
        "max": 99999,
        "step": 10.0,
    },
    "user_input.敌人等阶": {"source": "user_input", "type": "str", "default": "普通"},
    "user_input.敌人抗性": {
        "source": "user_input",
        "type": "float",
        "default": 0.0,
        "min": -100,
        "max": 100,
        "step": 1.0,
    },
    "user_input.无视抗性": {
        "source": "user_input",
        "type": "float",
        "default": 0.0,
        "min": -100,
        "max": 100,
        "step": 1.0,
    },
    "user_input.失衡易伤系数": {
        "source": "user_input",
        "type": "float",
        "default": 1.3,
        "min": 0.1,
        "max": 10.0,
        "step": 0.05,
    },
    "user_input.是否失衡": {"source": "user_input", "type": "bool", "default": False},
    "user_input.是否真实伤害": {"source": "user_input", "type": "bool", "default": False},
    "user_input.连击层数": {"source": "user_input", "type": "int", "default": 0, "min": 0, "max": 4, "step": 1},
    "user_input.额外暴击率": {
        "source": "user_input",
        "type": "float",
        "default": 0.0,
        "min": 0,
        "max": 1.0,
        "step": 0.01,
    },
    "user_input.额外暴击伤害": {
        "source": "user_input",
        "type": "float",
        "default": 0.0,
        "min": 0,
        "max": 5.0,
        "step": 0.01,
    },
    "user_input.额外伤害加成": {
        "source": "user_input",
        "type": "float",
        "default": 0.0,
        "min": 0,
        "max": 5.0,
        "step": 0.01,
    },
    "user_input.附带效果倍率": {
        "source": "user_input",
        "type": "float",
        "default": 1.0,
        "min": 0.1,
        "max": 3.0,
        "step": 0.05,
    },
    "user_input.破防层数": {"source": "user_input", "type": "int", "default": 0, "min": 0, "max": 4, "step": 1},
    "user_input.失衡效率加成": {
        "source": "user_input",
        "type": "float",
        "default": 0.0,
        "min": 0,
        "max": 1.0,
        "step": 0.05,
    },
    "user_input.腐蚀计时(秒)": {
        "source": "user_input",
        "type": "float",
        "default": 15.0,
        "min": 0.0,
        "max": 15.0,
        "step": 0.5,
    },
}

# 用户输入 → DAG context 的直接映射。
# 敌人抗性/失衡/真实伤害/连击/破防等需要换算为乘区值，统一由
# ``apply_endfield_sheet_context`` 处理；这里只保留无需换算的直写项。
ENDFIELD_USER_CONTEXT_OVERRIDES: dict[str, tuple[str, list[str]]] = {}


def _as_float(values: dict[str, Any], key: str, default: float) -> float:
    """读取数值，缺失或非法时返回默认值（0 是合法值）。"""
    raw = values.get(key, default)
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


def _as_int(values: dict[str, Any], key: str, default: int) -> int:
    """读取整数，缺失或非法时返回默认值。"""
    raw = values.get(key, default)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def apply_endfield_sheet_context(
    context: dict[str, Any],
    user_values: dict[str, Any],
    *,
    skill_type: str = "",
    use_expected_crit: bool = True,
) -> dict[str, Any]:
    """把 ComputeSheet 的原始敌人输入换算为 DAG 需要的乘区值。

    ComputeSheet 的 ``user_context_overrides`` 只能覆盖/累加，无法表达
    “百分比抗性 → 抗性区乘数”这类派生关系。本函数作为 ``context_transform``
    在 context 合并完成后执行。

    Args:
        context: 已合并 base_context 与用户输入的 DAG context。
        user_values: ``ComputeSheet.read_user_inputs()`` 的返回值。
        skill_type: 当前选中技能类型（战技/连携技/终结技），用于连击层数表。
        use_expected_crit: 是否按期望暴击计算；否则暴击区固定为 1。

    Returns:
        处理后的 context（原地修改并返回）。
    """
    computed = context.setdefault("computed", {})
    character = context.setdefault("character", {})
    enemy = context.setdefault("enemy", {})

    extra_crit_rate = _as_float(user_values, "user_input.额外暴击率", 0.0)
    extra_crit_damage = _as_float(user_values, "user_input.额外暴击伤害", 0.0)
    crit_rate = _as_float(character, "暴击率", 0.05) + extra_crit_rate
    character["暴击伤害"] = _as_float(character, "暴击伤害", 0.5) + extra_crit_damage
    character["暴击率"] = crit_rate if use_expected_crit else 0.0

    enemy_resistance = _as_float(user_values, "user_input.敌人抗性", 0.0)
    ignore_resistance = _as_float(user_values, "user_input.无视抗性", 0.0)
    computed["抗性"] = 1.0 - enemy_resistance / 100.0 + ignore_resistance / 100.0

    is_unbalanced = bool(user_values.get("user_input.是否失衡", False))
    imbalance_coeff = _as_float(user_values, "user_input.失衡易伤系数", 1.3)
    computed["失衡易伤"] = imbalance_coeff if is_unbalanced else 1.0

    is_true_damage = bool(user_values.get("user_input.是否真实伤害", False))
    enemy["防御"] = 0.0 if is_true_damage else _as_float(user_values, "user_input.敌人防御", 100.0)

    combo_stacks = _as_int(user_values, "user_input.连击层数", 0)
    computed["连击增伤"] = combo_zone_multiplier(skill_type, combo_stacks)

    break_stacks = _as_int(user_values, "user_input.破防层数", 0)
    computed["易伤"] = _as_float(computed, "易伤", 1.0) + vulnerability_bonus_from_break_defense(break_stacks)

    computed["伤害加成"] = _as_float(computed, "伤害加成", 1.0) + _as_float(user_values, "user_input.额外伤害加成", 0.0)
    return context
