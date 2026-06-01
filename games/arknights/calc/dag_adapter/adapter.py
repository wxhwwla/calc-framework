# SPDX-License-Identifier: AGPL-3.0
"""DAG 适配器：将 DAG 引擎接入明日方舟伤害计算。"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from calc_framework.config.adapter import AdapterPackage

from .loader import ArknightsContextLoader
from .types import SnapshotResult

_FRAMEWORK_DIR = Path(__file__).resolve().parents[4] / "framework"
_SRC_DIR = _FRAMEWORK_DIR / "src"
_ADAPTER_DIR = _FRAMEWORK_DIR / "adapters" / "arknights"

if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

_dag_pkg: AdapterPackage | None = None


def _ensure_dag() -> AdapterPackage:
    global _dag_pkg
    if _dag_pkg is None:
        _dag_pkg = AdapterPackage(_ADAPTER_DIR)
    return _dag_pkg


def compute_snapshot_with_dag(
    operator: dict[str, Any],
    *,
    skill_level: int = 7,
    skill_multiplier: float | None = None,
    enemy_def: float = 200.0,
    enemy_res: float = 50.0,
    atk_percent_bonus: float = 0.0,
    dmg_bonus: float = 0.0,
    def_penetration: float = 0.0,
    res_penetration: float = 0.0,
) -> SnapshotResult:
    """用 DAG 引擎计算干员伤害快照。

    参数:
        operator: parse_operator 输出的干员数据字典
        skill_level: 技能等级（1-7=技能等级, 8=专精1, 9=专精2, 10=专精3）
        skill_multiplier: 技能倍率。为 None 时直接从技能数据取倍率（解析器暂未提取，默认 1.0）
        enemy_def: 敌方防御力
        enemy_res: 敌方法术抗性
        atk_percent_bonus: 攻击力百分比加成（小数）
        dmg_bonus: 伤害加成百分比（小数）
        def_penetration: 固定减防值
        res_penetration: 百分比减抗（小数）

    返回:
        SnapshotResult 包含输出变量和执行顺序
    """
    pkg = _ensure_dag()
    loader = ArknightsContextLoader()

    skill_mult = _resolve_skill_mult(operator, skill_level) if skill_multiplier is None else skill_multiplier

    ctx = loader.build_context(
        operator=operator,
        skill_level=skill_level,
        skill_multiplier=skill_mult,
        enemy_def=enemy_def,
        enemy_res=enemy_res,
        atk_percent_bonus=atk_percent_bonus,
        dmg_bonus=dmg_bonus,
        def_penetration=def_penetration,
        res_penetration=res_penetration,
    )

    result = pkg.dag_service.evaluate(ctx)

    return SnapshotResult(
        outputs=result.outputs,
        execution_order=result.execution_order,
    )


def _resolve_skill_mult(operator: dict[str, Any], level: int) -> float:
    """从技能数据中提取指定等级的倍率。

    当前简化实现：仅返回 1.0（普攻倍率）。
    技能倍率暂未从 wikitext 中提取——倍率信息嵌在描述文本中，
    需要后续实现 NLP 解析（如"攻击力+30%"→ 1.3）。
    """
    return 1.0
