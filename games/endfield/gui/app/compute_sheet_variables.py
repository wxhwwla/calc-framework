# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""终末地 ComputeSheet 用户输入变量定义与上下文映射（无 PySide6 依赖）。

从 endfield_actions.py 拆分而来，可被 Web/CLI/测试复用。
"""

from __future__ import annotations

from typing import Any

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

# 用户输入 → DAG context 映射
# 键：user_input 变量路径
# 值：(目标 DAG context 路径, 合并方式列表)
# 合并方式："override" = 覆盖, "add" = 累加
ENDFIELD_USER_CONTEXT_OVERRIDES: dict[str, tuple[str, list[str]]] = {
    "user_input.敌人防御": ("enemy.防御", ["override"]),
    "user_input.敌人抗性": ("computed.抗性", ["add"]),
    "user_input.无视抗性": ("computed.无视抗性", ["override"]),
    "user_input.失衡易伤系数": ("computed.失衡易伤", ["override"]),
    "user_input.是否失衡": ("computed.失衡状态", ["override"]),
    "user_input.是否真实伤害": ("computed.真实伤害", ["override"]),
    "user_input.连击层数": ("computed.连击层数", ["override"]),
    "user_input.额外暴击率": ("character.暴击率", ["add"]),
    "user_input.额外暴击伤害": ("character.暴击伤害", ["add"]),
    "user_input.额外伤害加成": ("computed.伤害加成", ["add"]),
}
