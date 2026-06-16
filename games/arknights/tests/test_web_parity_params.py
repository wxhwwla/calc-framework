# SPDX-License-Identifier: AGPL-3.0
"""桌面/Web 参数语义对齐测试（DAG 百分点制）。"""

from __future__ import annotations

import pytest

from games.arknights.calc.dag_adapter import compute_snapshot_with_dag


def test_atk_percent_15_points(amiya_operator: dict) -> None:
    """15 百分点 ATK 加成：390×(1+15/100)+70+30 = 548.5。"""
    result = compute_snapshot_with_dag(amiya_operator, atk_percent_bonus=15.0)
    assert result.outputs["最终攻击力"] == pytest.approx(548.5)


def test_dmg_bonus_10_points(amiya_operator: dict) -> None:
    """10 百分点伤害加成：物理 290×1.1 = 319。"""
    result = compute_snapshot_with_dag(amiya_operator, dmg_bonus=10.0)
    assert result.outputs["物理伤害"] == pytest.approx(319.0)
