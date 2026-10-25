# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""DAG 适配器 — 调用框架 DAG 引擎执行计算并返回 SnapshotResult。

TODO: 根据实际游戏适配器目录路径调整 _ADAPTER_DIR。
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from calc_framework.config.adapter import AdapterPackage

from .loader import TEMPLATEContextLoader

_REPO_ROOT = Path(__file__).resolve().parents[4] / ".." / ".."
_FRAMEWORK_SRC = _REPO_ROOT / "framework" / "src"
_ADAPTER_DIR = _REPO_ROOT / "framework" / "adapters" / "_template"

if str(_FRAMEWORK_SRC) not in sys.path:
    sys.path.insert(0, str(_FRAMEWORK_SRC))

_dag_pkg: AdapterPackage | None = None


def _ensure_dag() -> AdapterPackage:
    """惰性加载 DAG 适配包（单例）。"""
    global _dag_pkg
    if _dag_pkg is None:
        _dag_pkg = AdapterPackage(_ADAPTER_DIR)
    return _dag_pkg


# TODO: 定义与游戏匹配的 SnapshotResult 数据结构
def compute_snapshot_with_dag(
    character: dict[str, Any],
    *,
    skill_level: int = 7,
    skill_multiplier: float = 1.0,
    enemy_def: float = 200.0,
    enemy_res: float = 50.0,
    atk_percent_bonus: float = 0.0,
    dmg_bonus: float = 0.0,
) -> dict[str, float]:
    """用 DAG 引擎计算角色伤害快照。

    参数:
        character: 角色数据字典（结构由游戏定义）
        skill_level: 技能等级
        skill_multiplier: 技能倍率
        enemy_def: 敌方防御力
        enemy_res: 敌方法术抗性
        atk_percent_bonus: 攻击力百分比加成（小数）
        dmg_bonus: 伤害加成百分比（小数）

    返回:
        输出变量名 → 值的字典，如 {"最终攻击力": 490.0, "物理伤害": 290.0}
    """
    pkg = _ensure_dag()
    loader = TEMPLATEContextLoader()

    ctx = loader.build_context(
        character=character,
        skill_level=skill_level,
        skill_multiplier=skill_multiplier,
        enemy_def=enemy_def,
        enemy_res=enemy_res,
        atk_percent_bonus=atk_percent_bonus,
        dmg_bonus=dmg_bonus,
    )

    result = pkg.dag_service.evaluate(ctx)

    # TODO: 返回类型可根据游戏需要调整为具名元组或 dataclass
    return dict(result.outputs)
