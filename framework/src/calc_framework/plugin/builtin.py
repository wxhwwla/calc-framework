# SPDX-License-Identifier: AGPL-3.0
"""内置游戏机制插件。"""

from __future__ import annotations

from typing import Any

from calc_framework.plugin.base import BasePlugin, PluginMeta
from calc_framework.plugin.registry import get_registry


class CritPlugin(BasePlugin):
    """暴击机制插件 — 提供暴击率/暴击伤害的 DAG 子图模板。"""

    @property
    def meta(self) -> PluginMeta:
        return PluginMeta(
            name="crit_handler",
            version="1.0.0",
            description="暴击率/暴击伤害计算：crit_rate × (1 + crit_dmg)",
            author="framework",
        )

    def on_load(self) -> dict[str, Any]:
        return {
            "variables": {
                "character.crit_rate": {
                    "type": "float", "source": "character",
                    "default": 0.05, "description": "暴击率",
                },
                "character.crit_dmg": {
                    "type": "float", "source": "character",
                    "default": 0.5, "description": "暴击伤害",
                },
            },
            "templates": {
                "crit_basic": {
                    "parameters": ["crit_rate", "crit_dmg", "is_crit"],
                    "nodes": {
                        "crit_rate_val": {"type": "var", "path": "$crit_rate"},
                        "crit_dmg_val": {"type": "var", "path": "$crit_dmg"},
                        "is_crit_val": {"type": "var", "path": "$is_crit"},
                        "const_1": {"type": "const", "value": 1.0},
                        "base_mult": {"type": "binary", "op": "+", "lhs": "const_1", "rhs": "crit_dmg_val"},
                        "result": {
                            "type": "condition",
                            "cond": "is_crit_val",
                            "true_val": "base_mult",
                            "false_val": "const_1",
                        },
                    },
                    "output_node": "result",
                    "description": "暴击倍率: 暴击时=1+crit_dmg, 否则=1",
                },
            },
        }


class DodgePlugin(BasePlugin):
    """闪避机制插件。"""

    @property
    def meta(self) -> PluginMeta:
        return PluginMeta(
            name="dodge_handler",
            version="1.0.0",
            description="闪避/命中率计算",
            author="framework",
        )

    def on_load(self) -> dict[str, Any]:
        return {
            "variables": {
                "character.accuracy": {
                    "type": "float", "source": "character",
                    "default": 1.0, "description": "命中率",
                },
                "enemy.dodge_rate": {
                    "type": "float", "source": "enemy",
                    "default": 0.0, "description": "敌方闪避率",
                },
            },
            "templates": {
                "dodge_check": {
                    "parameters": ["accuracy", "dodge_rate"],
                    "nodes": {
                        "acc_val": {"type": "var", "path": "$accuracy"},
                        "dodge_val": {"type": "var", "path": "$dodge_rate"},
                        "result": {
                            "type": "expr",
                            "expr": "max(0, acc - dodge_val)",
                            "inputs": {"acc": "acc_val", "dodge_val": "dodge_val"},
                        },
                    },
                    "output_node": "result",
                    "description": "最终命中率 = max(0, accuracy - dodge_rate)",
                },
            },
        }


class DistanceDecayPlugin(BasePlugin):
    """距离衰减插件 — 远程攻击的距离衰减。"""

    @property
    def meta(self) -> PluginMeta:
        return PluginMeta(
            name="distance_decay",
            version="1.0.0",
            description="远程攻击距离衰减：start_at 内 100%, end_at 外 0%, 之间线性",
            author="framework",
        )

    def on_load(self) -> dict[str, Any]:
        return {
            "variables": {
                "attack.distance": {
                    "type": "float", "source": "computed",
                    "default": 0, "description": "攻击距离",
                },
                "attack.decay_start": {
                    "type": "float", "source": "computed",
                    "default": 10, "description": "衰减起始距离",
                },
                "attack.decay_end": {
                    "type": "float", "source": "computed",
                    "default": 30, "description": "衰减结束距离",
                },
            },
            "templates": {
                "linear_distance_decay": {
                    "parameters": ["distance", "start_at", "end_at"],
                    "nodes": {
                        "dist_val": {"type": "var", "path": "$distance"},
                        "start_val": {"type": "var", "path": "$start_at"},
                        "end_val": {"type": "var", "path": "$end_at"},
                        "const_1": {"type": "const", "value": 1.0},
                        "const_0": {"type": "const", "value": 0.0},
                        "in_range": {
                            "type": "condition",
                            "cond": "le_start",
                            "true_val": "const_1",
                            "false_val": "out_of_range",
                        },
                        "le_start": {
                            "type": "binary", "op": "<=",
                            "lhs": "dist_val", "rhs": "start_val",
                        },
                        "out_of_range": {
                            "type": "condition",
                            "cond": "ge_end",
                            "true_val": "const_0",
                            "false_val": "linear",
                        },
                        "ge_end": {
                            "type": "binary", "op": ">=",
                            "lhs": "dist_val", "rhs": "end_val",
                        },
                        "linear": {
                            "type": "expr",
                            "expr": "1 - (d - s) / (e - s)",
                            "inputs": {"d": "dist_val", "s": "start_val", "e": "end_val"},
                        },
                    },
                    "output_node": "in_range",
                    "description": "线性距离衰减: [0,start]=1, [start,end]线性, [end,∞)=0",
                },
            },
        }


def register_builtin_plugins() -> None:
    """注册所有内置插件。"""
    reg = get_registry()
    for plugin in [CritPlugin(), DodgePlugin(), DistanceDecayPlugin()]:
        reg.register(plugin)
