# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""DAG 计算端到端单元测试 — 使用真实 arknights DAG。

手动验证数据（阿米娅，等级1，无攻%加成，默认敌方 200防/50抗）：

  ATK 最终 = 390(基础) + 70(信赖) + 30(潜能) = 490
  技能倍率 = 1.0（普攻）

  物理伤害 = max(490×1.0 - 200, 490×1.0×0.05) × (1 + 0)
           = max(290, 24.5) = 290.0
  法术伤害 = 490×1.0 × (1 - 50/100) × (1 + 0)
           = 490 × 0.5 = 245.0
  真伤伤害 = 490×1.0 × (1 + 0) = 490.0
"""

from __future__ import annotations

import pytest

from games.arknights.calc.dag_adapter import compute_snapshot_with_dag


class TestComputeWithAmiya:
    def test_outputs_have_expected_keys(self, amiya_operator: dict) -> None:
        result = compute_snapshot_with_dag(amiya_operator)
        assert "最终攻击力" in result.outputs
        assert "物理伤害" in result.outputs
        assert "法术伤害" in result.outputs
        assert "真伤伤害" in result.outputs

    def test_final_atk_490(self, amiya_operator: dict) -> None:
        result = compute_snapshot_with_dag(amiya_operator)
        assert result.outputs["最终攻击力"] == 490.0

    def test_physical_damage_290(self, amiya_operator: dict) -> None:
        result = compute_snapshot_with_dag(amiya_operator)
        assert result.outputs["物理伤害"] == 290.0

    def test_magical_damage_245(self, amiya_operator: dict) -> None:
        result = compute_snapshot_with_dag(amiya_operator)
        assert result.outputs["法术伤害"] == 245.0

    def test_true_damage_490(self, amiya_operator: dict) -> None:
        result = compute_snapshot_with_dag(amiya_operator)
        assert result.outputs["真伤伤害"] == 490.0

    def test_execution_order_is_populated(self, amiya_operator: dict) -> None:
        result = compute_snapshot_with_dag(amiya_operator)
        assert len(result.execution_order) > 0

    def test_outputs_are_floats(self, amiya_operator: dict) -> None:
        result = compute_snapshot_with_dag(amiya_operator)
        for val in result.outputs.values():
            assert isinstance(val, float), f"Expected float, got {type(val)}: {val}"


class TestComputeCustomParams:
    def test_with_skill_multiplier(self, amiya_operator: dict) -> None:
        result = compute_snapshot_with_dag(amiya_operator, skill_multiplier=2.0)
        # ATK 最终 = 490, 技能倍率 = 2.0
        # 物理 = max(490*2 - 200, 490*2*0.05) = max(780, 49) = 780
        assert result.outputs["最终攻击力"] == 490.0
        assert result.outputs["物理伤害"] == 780.0
        # 法术 = 490*2 * (1 - 50/100) = 980*0.5 = 490
        assert result.outputs["法术伤害"] == 490.0
        # 真伤 = 490*2 = 980
        assert result.outputs["真伤伤害"] == 980.0

    def test_with_atk_percent_bonus(self, amiya_operator: dict) -> None:
        result = compute_snapshot_with_dag(amiya_operator, atk_percent_bonus=0.5)
        # 最终 ATK = 390*(1+0.5/100) + 70 + 30 = 390*1.005 + 100 = 491.95... wait
        # atk_percent_bonus is in decimal form (e.g., 0.5 = 50%)
        # In the DAG: base_atk * (1 + atk_percent/100) + trust + pot
        # atk_percent is divided by 100 in the DAG
        # So: 390 * (1 + 0.5/100) + 100 = 390 * 1.005 + 100 = 391.95 + 100 = 491.95
        assert result.outputs["最终攻击力"] == pytest.approx(491.95)
        # 物理 = max(491.95 - 200, 491.95*0.05) = max(291.95, 24.5975) = 291.95
        assert result.outputs["物理伤害"] == pytest.approx(291.95)
        # 法术 = 491.95 * 0.5 = 245.975
        assert result.outputs["法术伤害"] == pytest.approx(245.975)

    def test_with_damage_bonus(self, amiya_operator: dict) -> None:
        result = compute_snapshot_with_dag(amiya_operator, dmg_bonus=0.5)
        # 物理 = 290 * (1 + 0.5/100) = 290 * 1.005 = 291.45
        assert result.outputs["物理伤害"] == pytest.approx(291.45)
        # 法术 = 245 * 1.005 = 246.225
        assert result.outputs["法术伤害"] == pytest.approx(246.225)
        # 真伤 = 490 * 1.005 = 492.45
        assert result.outputs["真伤伤害"] == pytest.approx(492.45)

    def test_with_def_penetration(self, amiya_operator: dict) -> None:
        result = compute_snapshot_with_dag(amiya_operator, def_penetration=100.0)
        # 有效防御 = max(200-100, 0) = 100
        # 物理 = max(490 - 100, 490*0.05) = max(390, 24.5) = 390
        assert result.outputs["物理伤害"] == 390.0

    def test_with_res_penetration(self, amiya_operator: dict) -> None:
        result = compute_snapshot_with_dag(amiya_operator, res_penetration=0.5)
        # 有效抗性 = 50 * (1 - 0.5) = 25
        # 法术 = 490 * (1 - 25/100) = 490 * 0.75 = 367.5
        assert result.outputs["法术伤害"] == 367.5

    def test_with_all_params(self, amiya_operator: dict) -> None:
        result = compute_snapshot_with_dag(
            amiya_operator,
            skill_multiplier=3.0,
            enemy_def=500.0,
            enemy_res=30.0,
            atk_percent_bonus=0.2,
            dmg_bonus=0.15,
        )
        # 最终 ATK = 390*(1+0.2/100) + 100 = 390*1.002+100 = 490.78
        assert result.outputs["最终攻击力"] == pytest.approx(490.78)


class TestComputeEdgeCases:
    def test_minimal_operator(self, minimal_operator: dict) -> None:
        result = compute_snapshot_with_dag(minimal_operator)
        # ATK=100, no trust, no pot
        # 物理 = max(100-200, 100*0.05) = max(-100, 5) = 5
        assert result.outputs["最终攻击力"] == 100.0
        assert result.outputs["物理伤害"] == 5.0
        # 法术 = 100 * (1 - 50/100) = 50
        assert result.outputs["法术伤害"] == 50.0
        # 真伤 = 100
        assert result.outputs["真伤伤害"] == 100.0

    def test_high_defense_no_damage(self) -> None:
        operator = {
            "名称": "Tank",
            "星级": 1,
            "职业": "重装",
            "基础属性": {"atk": 100, "def": 50},
        }
        # 物理 = max(100-5000, 100*0.05) = max(-4900, 5) = 5
        result = compute_snapshot_with_dag(operator, enemy_def=5000.0)
        assert result.outputs["物理伤害"] >= 5.0  # 5% 保底
        assert result.outputs["物理伤害"] == 5.0

    def test_result_is_snapshot_result_type(self, amiya_operator: dict) -> None:
        from games.arknights.calc.dag_adapter.types import SnapshotResult

        result = compute_snapshot_with_dag(amiya_operator)
        assert isinstance(result, SnapshotResult)
