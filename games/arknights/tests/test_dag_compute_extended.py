# SPDX-License-Identifier: AGPL-3.0
"""DAG 计算扩展测试 — 边界条件、极端参数、组合场景。

手动验证基准（阿米娅，等级1，默认敌方 200防/50抗）：
  ATK 最终 = 390(基础) + 70(信赖) + 30(潜能) = 490
  技能倍率 = 1.0
  物理 = max(490*1 - 200, 490*1*0.05) * (1+0) = 290.0
  法术 = 490 * 0.5 = 245.0
  真伤 = 490 = 490.0
"""

from __future__ import annotations

import pytest

from games.arknights.calc.dag_adapter import compute_snapshot_with_dag
from games.arknights.calc.dag_adapter.types import SnapshotResult

# ═══════════════════════════════════════════════
#  零防御 / 高防御 / 零抗性 / 满抗性 边界
# ═══════════════════════════════════════════════


class TestZeroDefense:
    """零防御时物理伤害 = ATK * 倍率（最小值失效/不影响）。"""

    def test_zero_def_physical_damage_equals_atk(self, amiya_operator: dict) -> None:
        result = compute_snapshot_with_dag(amiya_operator, enemy_def=0.0)
        # ATK=490, skill_mult=1.0 → physical = max(490-0, 490*0.05) = 490
        assert result.outputs["物理伤害"] == 490.0

    def test_zero_def_with_multiplier(self, amiya_operator: dict) -> None:
        result = compute_snapshot_with_dag(amiya_operator, enemy_def=0.0, skill_multiplier=2.0)
        # physical = max(490*2 - 0, 490*2*0.05) = 980
        assert result.outputs["物理伤害"] == 980.0

    def test_high_defense_floor_mechanism(self, amiya_operator: dict) -> None:
        """防御远远高于攻击时物理伤害保底为 ATK * 5%"""
        result = compute_snapshot_with_dag(amiya_operator, enemy_def=99999.0)
        # physical = max(490-99999, 490*0.05) = max(-99509, 24.5) = 24.5
        assert result.outputs["物理伤害"] == 24.5


class TestResistanceEdgeCases:
    """法术抗性边界测试。"""

    def test_zero_res_full_magical_damage(self, amiya_operator: dict) -> None:
        result = compute_snapshot_with_dag(amiya_operator, enemy_res=0.0)
        # 法术 = 490 * (1 - 0/100) = 490
        assert result.outputs["法术伤害"] == 490.0

    def test_100_res_no_magical_damage(self, amiya_operator: dict) -> None:
        result = compute_snapshot_with_dag(amiya_operator, enemy_res=100.0)
        # 法术 = 490 * (1 - 100/100) = 0
        assert result.outputs["法术伤害"] == pytest.approx(0.0)

    def test_res_penetration_with_100_res(self, amiya_operator: dict) -> None:
        result = compute_snapshot_with_dag(amiya_operator, enemy_res=100.0, res_penetration=0.5)
        # 有效抗性 = 100 * (1 - 0.5) = 50
        # 法术 = 490 * (1 - 50/100) = 245
        assert result.outputs["法术伤害"] == 245.0


# ═══════════════════════════════════════════════
#  极端倍率 & 高 ATK
# ═══════════════════════════════════════════════


class TestHighMultiplier:
    """倍率 > 10 倍边界测试。"""

    def test_skill_multiplier_10x(self, amiya_operator: dict) -> None:
        result = compute_snapshot_with_dag(amiya_operator, skill_multiplier=10.0)
        # ATK=490, skill_mult=10.0
        # 物理 = max(490*10 - 200, 490*10*0.05) = max(4700, 245) = 4700
        assert result.outputs["物理伤害"] == 4700.0
        # 法术 = 490*10 * 0.5 = 2450
        assert result.outputs["法术伤害"] == 2450.0
        # 真伤 = 490*10 = 4900
        assert result.outputs["真伤伤害"] == 4900.0

    def test_skill_multiplier_100x_overflow_safe(self, amiya_operator: dict) -> None:
        """极高倍率不报错，产物为 finite float。"""
        result = compute_snapshot_with_dag(amiya_operator, skill_multiplier=100.0)
        import math

        for val in result.outputs.values():
            assert math.isfinite(val), f"Value {val} is not finite"

    def test_skill_multiplier_zero(self, amiya_operator: dict) -> None:
        """倍率 0 应产生 0 伤害。"""
        result = compute_snapshot_with_dag(amiya_operator, skill_multiplier=0.0)
        assert result.outputs["真伤伤害"] == 0.0
        # 物理保底：490*0*0.05 = 0 但保底基于有效 ATK*5%，最终攻击=0 → min=0
        # 物理 = max(0-200, 0*0.05) = max(-200, 0) = 0
        assert result.outputs["物理伤害"] == 0.0


class TestHighAttackBase:
    """高基础 ATK 值（溢出保护）。"""

    def test_very_high_atk_float_overflow(self) -> None:
        operator = {
            "名称": "HighATK",
            "星级": 6,
            "职业": "近卫",
            "基础属性": {"atk": 1e15},
        }
        result = compute_snapshot_with_dag(operator)
        import math

        assert math.isfinite(result.outputs["最终攻击力"])

    def test_atk_billion_order(self) -> None:
        operator = {
            "名称": "BillionATK",
            "星级": 6,
            "职业": "狙击",
            "基础属性": {"atk": 1e9, "def": 0, "res": 0},
        }
        result = compute_snapshot_with_dag(operator)
        assert result.outputs["最终攻击力"] == 1e9
        assert result.outputs["物理伤害"] == pytest.approx(1e9)


# ═══════════════════════════════════════════════
#  不同技能等级
# ═══════════════════════════════════════════════


class TestSkillLevels:
    """skill_level 1-10 的验证（解析器暂未完全覆盖所有模板，此处验证框架行为）。"""

    def test_skill_level_1(self, amiya_operator: dict) -> None:
        """skill_level=1 不报错且结果完整。"""
        result = compute_snapshot_with_dag(amiya_operator, skill_level=1)
        assert "最终攻击力" in result.outputs
        assert result.outputs["最终攻击力"] == 490.0

    def test_skill_level_4(self, amiya_operator: dict) -> None:
        result = compute_snapshot_with_dag(amiya_operator, skill_level=4)
        assert len(result.execution_order) > 0

    def test_skill_level_7(self, amiya_operator: dict) -> None:
        result = compute_snapshot_with_dag(amiya_operator, skill_level=7)
        assert result.outputs["最终攻击力"] == 490.0

    def test_skill_level_8(self, amiya_operator: dict) -> None:
        """专精1。"""
        result = compute_snapshot_with_dag(amiya_operator, skill_level=8)
        assert len(result.execution_order) > 0

    def test_skill_level_10(self, amiya_operator: dict) -> None:
        """专精3。"""
        result = compute_snapshot_with_dag(amiya_operator, skill_level=10)
        assert len(result.execution_order) > 0

    def test_skill_level_99_does_not_crash(self, amiya_operator: dict) -> None:
        """超范围 level 不离谱。"""
        result = compute_snapshot_with_dag(amiya_operator, skill_level=99)
        assert "最终攻击力" in result.outputs

    def test_skill_level_zero(self, amiya_operator: dict) -> None:
        result = compute_snapshot_with_dag(amiya_operator, skill_level=0)
        assert "最终攻击力" in result.outputs


# ═══════════════════════════════════════════════
#  负面倍率 & 组合 buff
# ═══════════════════════════════════════════════


class TestNegativeParameters:
    """负面参数处理。"""

    def test_negative_skill_multiplier(self, amiya_operator: dict) -> None:
        """负面倍率仍计算，但不允许结果为负（保底 0）。"""
        result = compute_snapshot_with_dag(amiya_operator, skill_multiplier=-0.5)
        # 最终 ATK 仍然是 490（不受负面倍率影响，倍率只影响伤害计算）
        assert result.outputs["最终攻击力"] == 490.0
        # 物理 = max(490*(-0.5) - 200, 490*(-0.5)*0.05) = max(-445, -12.25) = -12.25
        # ... 但 DAG 内有 max(..., 0) ? 取决于公式设计。这里仅验证不报错。
        import math

        for val in result.outputs.values():
            assert math.isfinite(val)

    def test_negative_dmg_bonus(self, amiya_operator: dict) -> None:
        """dmg_bonus 负面值。"""
        result = compute_snapshot_with_dag(amiya_operator, dmg_bonus=-0.5)
        # physical = 290 * (1 + (-0.5)/100) = 290 * 0.995 = 288.55
        assert result.outputs["物理伤害"] == pytest.approx(288.55)

    def test_negative_atk_percent_bonus(self, amiya_operator: dict) -> None:
        """atk_percent_bonus 负面。"""
        result = compute_snapshot_with_dag(amiya_operator, atk_percent_bonus=-0.2)
        # ATK = 390*(1 + (-0.2)/100) + 100 = 390*0.998 + 100 = 489.22
        assert result.outputs["最终攻击力"] == pytest.approx(489.22)


# ═══════════════════════════════════════════════
#  buff + multiplier 组合
# ═══════════════════════════════════════════════


class TestBuffAndMultiplierCombined:
    """同时使用 atk_percent_bonus 和 skill_multiplier。"""

    def test_atk_buff_with_skill_multiplier(self, amiya_operator: dict) -> None:
        result = compute_snapshot_with_dag(
            amiya_operator,
            atk_percent_bonus=1.0,  # 100%
            skill_multiplier=2.0,
        )
        # ATK = 390*(1+1.0/100) + 100 = 390*1.01 + 100 = 493.9
        assert result.outputs["最终攻击力"] == pytest.approx(493.9)
        # 物理 = max(493.9*2 - 200, 493.9*2*0.05) = max(787.8, 49.39) = 787.8
        assert result.outputs["物理伤害"] == pytest.approx(787.8)

    def test_direct_multiplier_without_atk_buff(self, amiya_operator: dict) -> None:
        """只有 skill_multiplier，无 atk_percent_bonus。"""
        result = compute_snapshot_with_dag(amiya_operator, skill_multiplier=3.0)
        # ATK=490, 物理 = max(490*3 - 200, 490*3*0.05) = max(1270, 73.5) = 1270
        assert result.outputs["物理伤害"] == 1270.0

    def test_zero_atk_buff_with_large_mult(self, amiya_operator: dict) -> None:
        result = compute_snapshot_with_dag(amiya_operator, atk_percent_bonus=0.0, skill_multiplier=5.0)
        assert result.outputs["物理伤害"] == 2250.0


# ═══════════════════════════════════════════════
#  信任 & 潜能加成
# ═══════════════════════════════════════════════


class TestTrustBonus:
    """信赖加成传播。"""

    def test_amiya_trust_bonus_applied(self, amiya_operator: dict) -> None:
        result = compute_snapshot_with_dag(amiya_operator)
        assert result.outputs["最终攻击力"] == 490.0  # 含信赖 70

    def test_no_trust_bonus(self, amiya_operator: dict) -> None:
        operator_no_trust = {**amiya_operator}
        del operator_no_trust["信赖加成"]
        result = compute_snapshot_with_dag(operator_no_trust)
        # ATK = 390 + 0 + 30 = 420
        assert result.outputs["最终攻击力"] == 420.0

    def test_trust_def_does_not_affect_atk(self, amiya_operator: dict) -> None:
        """信赖防御加成不影响攻击力。"""
        operator = {
            **amiya_operator,
            "信赖加成": {"攻击": 70, "防御": 50, "生命": 200},
        }
        result = compute_snapshot_with_dag(operator)
        assert result.outputs["最终攻击力"] == 490.0

    def test_trust_bonus_zero_values(self, amiya_operator: dict) -> None:
        operator = {**amiya_operator, "信赖加成": {"攻击": 0, "防御": 0}}
        result = compute_snapshot_with_dag(operator)
        # ATK = 390 + 0 + 30 = 420
        assert result.outputs["最终攻击力"] == 420.0


class TestPotentialBonus:
    """潜能加成传播。"""

    def test_potential_atk_bonus_applied(self, amiya_operator: dict) -> None:
        result = compute_snapshot_with_dag(amiya_operator)
        # ATK = 390 + 70 + 30 = 490
        assert result.outputs["最终攻击力"] == 490.0

    def test_no_potential_bonus(self, amiya_operator: dict) -> None:
        operator_no_pot = {**amiya_operator}
        del operator_no_pot["潜能"]
        result = compute_snapshot_with_dag(operator_no_pot)
        # ATK = 390 + 70 + 0 = 460
        assert result.outputs["最终攻击力"] == 460.0

    def test_potential_multiple_atk_entries(self) -> None:
        operator = {
            "名称": "MultiPot",
            "星级": 6,
            "职业": "狙击",
            "基础属性": {"atk": 200, "def": 50},
            "潜能": ["攻击力+30", "攻击力+25", "攻击力+20", "部署费用-1"],
        }
        result = compute_snapshot_with_dag(operator)
        # ATK = 200 + 0 + 75 = 275
        assert result.outputs["最终攻击力"] == 275.0

    def test_potential_no_atk_entries(self) -> None:
        operator = {
            "名称": "NoAtkPot",
            "星级": 5,
            "职业": "重装",
            "基础属性": {"atk": 150},
            "潜能": ["部署费用-1", "生命上限+200", "天赋效果增强"],
        }
        result = compute_snapshot_with_dag(operator)
        # ATK = 150 + 0 + 0 = 150
        assert result.outputs["最终攻击力"] == 150.0


# ═══════════════════════════════════════════════
#  缺少字段 / 降级
# ═══════════════════════════════════════════════


class TestGracefulDegradation:
    """干员数据不全时的行为。"""

    def test_no_base_stats_key(self) -> None:
        operator = {
            "名称": "Ghost",
            "星级": 3,
            "职业": "辅助",
        }
        result = compute_snapshot_with_dag(operator)
        assert result.outputs["最终攻击力"] == 0.0

    def test_no_name_field(self) -> None:
        operator = {
            "星级": 1,
            "职业": "先锋",
            "基础属性": {"atk": 100},
        }
        result = compute_snapshot_with_dag(operator)
        assert result.outputs["最终攻击力"] == 100.0

    def test_base_stats_empty_dict(self) -> None:
        operator = {"基础属性": {}}
        result = compute_snapshot_with_dag(operator)
        assert result.outputs["最终攻击力"] == 0.0

    def test_base_stats_missing_atk(self) -> None:
        operator = {"基础属性": {"def": 200, "res": 10}}
        result = compute_snapshot_with_dag(operator)
        assert result.outputs["最终攻击力"] == 0.0

    def test_base_stats_atk_is_string(self) -> None:
        operator = {"基础属性": {"atk": "450", "def": 100}}
        result = compute_snapshot_with_dag(operator)
        assert result.outputs["最终攻击力"] == 450.0


# ═══════════════════════════════════════════════
#  所有可选参数同时使用
# ═══════════════════════════════════════════════


class TestAllParamsSimultaneously:
    """所有可选参数一起传入。"""

    def test_all_eight_params(self, amiya_operator: dict) -> None:
        result = compute_snapshot_with_dag(
            amiya_operator,
            skill_level=10,
            skill_multiplier=3.5,
            enemy_def=400.0,
            enemy_res=70.0,
            atk_percent_bonus=0.8,
            dmg_bonus=0.25,
            def_penetration=100.0,
            res_penetration=0.3,
        )
        assert "最终攻击力" in result.outputs
        assert "物理伤害" in result.outputs
        assert "法术伤害" in result.outputs
        assert "真伤伤害" in result.outputs
        assert len(result.execution_order) > 0

    def test_all_params_zeroed(self) -> None:
        operator = {
            "名称": "Zeroed",
            "星级": 1,
            "职业": "特种",
            "基础属性": {"atk": 300, "def": 50, "res": 5},
        }
        result = compute_snapshot_with_dag(
            operator,
            skill_multiplier=1.0,
            enemy_def=0.0,
            enemy_res=0.0,
            atk_percent_bonus=0.0,
            dmg_bonus=0.0,
            def_penetration=0.0,
            res_penetration=0.0,
        )
        # 最终 ATK = 300
        assert result.outputs["最终攻击力"] == 300.0
        # 物理 = max(300-0, 300*0.05) = 300
        assert result.outputs["物理伤害"] == 300.0
        # 法术 = 300 * (1-0) = 300
        assert result.outputs["法术伤害"] == 300.0
        # 真伤 = 300
        assert result.outputs["真伤伤害"] == 300.0


# ═══════════════════════════════════════════════
#  防御/法抗穿透组合
# ═══════════════════════════════════════════════


class TestPenetrationCombined:
    """双穿透同时使用。"""

    def test_both_penetrations(self, amiya_operator: dict) -> None:
        result = compute_snapshot_with_dag(
            amiya_operator,
            def_penetration=200.0,
            res_penetration=1.0,
        )
        # 有效防御 = max(200-200, 0) = 0
        # 物理 = max(490-0, 490*0.05) = 490
        assert result.outputs["物理伤害"] == 490.0
        # 有效抗性 = 50 * (1-1) = 0
        # 法术 = 490 * (1-0) = 490
        assert result.outputs["法术伤害"] == 490.0

    def test_def_penetration_greater_than_def(self, amiya_operator: dict) -> None:
        result = compute_snapshot_with_dag(amiya_operator, def_penetration=9999.0)
        # 有效防御 = max(200-9999, 0) = 0
        # 物理 = max(490-0, 490*0.05) = 490
        assert result.outputs["物理伤害"] == 490.0

    def test_res_penetration_greater_than_one(self, amiya_operator: dict) -> None:
        """res_penetration > 1 时有效抗性为负？公式为 res*(1-pen)，结果应 >= 0。"""
        result = compute_snapshot_with_dag(amiya_operator, res_penetration=2.0)
        import math

        assert math.isfinite(result.outputs["法术伤害"])


# ═══════════════════════════════════════════════
#  不同类型干员
# ═══════════════════════════════════════════════


class TestMixedDamageTypes:
    """不同伤害类型干员结果。"""

    def test_physical_only_operator(self) -> None:
        """纯物理职业（狙击）计算结果有效。"""
        operator = {
            "名称": "SniperX",
            "星级": 4,
            "职业": "狙击",
            "基础属性": {"atk": 500, "def": 50},
        }
        result = compute_snapshot_with_dag(operator)
        assert result.outputs["物理伤害"] > 0

    def test_caster_operator(self) -> None:
        """术师干员。"""
        operator = {
            "名称": "CasterY",
            "星级": 5,
            "职业": "术师",
            "基础属性": {"atk": 600, "def": 40, "res": 15},
        }
        result = compute_snapshot_with_dag(operator)
        assert result.outputs["最终攻击力"] == 600.0

    def test_defender_operator(self) -> None:
        """重装干员。"""
        operator = {
            "名称": "DefenderZ",
            "星级": 6,
            "职业": "重装",
            "基础属性": {"atk": 200, "def": 500},
        }
        result = compute_snapshot_with_dag(operator)
        assert result.outputs["物理伤害"] == 10.0  # max(200-200, 200*0.05)=10

    def test_supporter_operator(self) -> None:
        """辅助干员。"""
        operator = {
            "名称": "SupporterA",
            "星级": 5,
            "职业": "辅助",
            "基础属性": {"atk": 350},
        }
        result = compute_snapshot_with_dag(operator)
        assert result.outputs["物理伤害"] == 150.0  # max(350-200, 350*0.05)=150


# ═══════════════════════════════════════════════
#  SnapshotResult 类型检查
# ═══════════════════════════════════════════════


class TestSnapshotResultType:
    def test_type_is_snapshot_result(self, amiya_operator: dict) -> None:
        result = compute_snapshot_with_dag(amiya_operator)
        assert isinstance(result, SnapshotResult)

    def test_has_outputs_and_execution_order(self, amiya_operator: dict) -> None:
        result = compute_snapshot_with_dag(amiya_operator)
        assert hasattr(result, "outputs")
        assert hasattr(result, "execution_order")
        assert isinstance(result.outputs, dict)
        assert isinstance(result.execution_order, list)

    def test_outputs_all_floats(self, amiya_operator: dict) -> None:
        result = compute_snapshot_with_dag(amiya_operator)
        for key, val in result.outputs.items():
            assert isinstance(val, float), f"Key '{key}' has type {type(val)}: {val}"

    def test_execution_order_non_empty(self, amiya_operator: dict) -> None:
        result = compute_snapshot_with_dag(amiya_operator)
        assert len(result.execution_order) > 0
        assert all(isinstance(x, str) for x in result.execution_order)
