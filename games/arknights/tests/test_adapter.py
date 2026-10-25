# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""测试 adapter.py — get_parsed_skill_info 与 compute_snapshot_with_dag 组合。"""

from __future__ import annotations

from typing import Any

from games.arknights.calc.dag_adapter.adapter import (
    _resolve_skill_mult,
    compute_snapshot_with_dag,
    get_parsed_skill_info,
)
from games.arknights.calc.dag_adapter.types import SnapshotResult


def _make_operator(skills: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    data: dict[str, Any] = {
        "name": "测试干员",
        "职业": "狙击",
    }
    if skills is not None:
        data["技能"] = skills
    return data


class TestGetParsedSkillInfo:
    def test_skill_index_negative_returns_auto_attack(self) -> None:
        """skill_index < 0 → 返回普攻（倍率 1.0，物理，1 段）"""
        op = _make_operator()
        info = get_parsed_skill_info(op, skill_index=-1)
        assert info.effective_multiplier == 1.0
        assert info.damage_type == "physical"
        assert info.hit_count == 1
        assert not info.is_healing

    def test_skill_index_out_of_range_returns_auto_attack(self) -> None:
        """skill_index >= len(skills) → 返回普攻"""
        op = _make_operator(skills=[])
        info = get_parsed_skill_info(op, skill_index=0)
        assert info.effective_multiplier == 1.0
        assert info.damage_type == "physical"

    def test_skill_index_valid_returns_parsed_skill(self) -> None:
        """skill_index 在范围内 → 正常解析技能"""
        skill = {
            "name": "战术咏唱",
            "sp_type": "自动回复",
            "trigger": "手动触发",
            "levels": [
                {
                    "description": "攻击力+50%",
                    "sp_cost": 10,
                    "init_sp": 5,
                    "duration": "20",
                }
            ],
        }
        op = _make_operator(skills=[skill])
        info = get_parsed_skill_info(op, level=7, skill_index=0)
        assert info.effective_multiplier == 1.0
        assert info.atk_buff_hint == 0.5
        assert info.sp_cost == 10
        assert info.duration == 20


# ═══════════════════════════════════════════════
#  compute_snapshot_with_dag 不同干员
# ═══════════════════════════════════════════════


class TestComputeSnapshotDifferentOperators:
    def test_with_direct_atk_set_skill(self) -> None:
        """技能含"攻击力提升至XX%"。"""
        skill = {
            "name": "强力击",
            "sp_type": "自动回复",
            "trigger": "手动触发",
            "levels": [
                {
                    "description": "攻击力提升至200%",
                    "sp_cost": 20,
                    "init_sp": 0,
                    "duration": "0",
                }
            ],
        }
        op = {
            "名称": "TestGuard",
            "星级": 3,
            "职业": "近卫",
            "基础属性": {"atk": 500, "def": 100},
            "技能": [skill],
        }
        # _resolve_skill_mult 返回 effective_multiplier=2.0
        # 最终 ATK = 500
        # 物理 = max(500*2 - 200, 500*2*0.05) = max(800, 50) = 800
        result = compute_snapshot_with_dag(op)
        assert result.outputs["物理伤害"] == 800.0

    def test_with_equiv_damage_skill(self) -> None:
        """技能含"相当于攻击力XX% 的伤害"。"""
        skill = {
            "name": "战术咏唱β",
            "sp_type": "自动回复",
            "trigger": "手动触发",
            "levels": [
                {
                    "description": "相当于攻击力200%的法术伤害",
                    "sp_cost": 15,
                    "init_sp": 5,
                    "duration": "10",
                }
            ],
        }
        op = {
            "名称": "TestCaster",
            "星级": 4,
            "职业": "术师",
            "基础属性": {"atk": 600, "def": 40, "res": 15},
            "技能": [skill],
        }
        result = compute_snapshot_with_dag(op)
        # _resolve_skill_mult 应返回 2.0
        # 最终 ATK = 600
        # 物理 = max(600*2 - 200, 600*2*0.05) = max(1000, 60) = 1000
        assert result.outputs["物理伤害"] == 1000.0

    def test_with_atk_buff_only_skill(self) -> None:
        """技能只有"攻击力+XX%"（无倍率，只有 ATK buff hint）。"""
        skill = {
            "name": "攻击力强化·α",
            "sp_type": "自动回复",
            "trigger": "手动触发",
            "levels": [
                {
                    "description": "攻击力+30%",
                    "sp_cost": 10,
                    "init_sp": 0,
                    "duration": "20",
                }
            ],
        }
        op = {
            "名称": "TestBuffer",
            "星级": 3,
            "职业": "先锋",
            "基础属性": {"atk": 300, "def": 50},
            "技能": [skill],
        }
        # effective_multiplier = 1.0 (只有 ATK buff)
        # _resolve_skill_mult 返回 1.0
        result = compute_snapshot_with_dag(op)
        # 最终 ATK = 300, skill_mult=1.0
        assert result.outputs["最终攻击力"] == 300.0
        # 物理 = max(300-200, 300*0.05) = max(100, 15) = 100
        assert result.outputs["物理伤害"] == 100.0


class TestResolveSkillMult:
    """_resolve_skill_mult 间接测试。"""

    def test_no_skills_returns_1(self) -> None:
        op = _make_operator(skills=[])
        mult = _resolve_skill_mult(op, 7)
        assert mult == 1.0

    def test_no_skills_key_returns_1(self) -> None:
        op = _make_operator()
        mult = _resolve_skill_mult(op, 7)
        assert mult == 1.0

    def test_with_atk_buff_skill_returns_1(self) -> None:
        """攻击力+XX% 技能：effective_multiplier = 1.0。"""
        skill = {
            "name": "α",
            "sp_type": "自动回复",
            "trigger": "手动触发",
            "levels": [{"description": "攻击力+50%", "sp_cost": 10, "init_sp": 5, "duration": "20"}],
        }
        op = _make_operator(skills=[skill])
        mult = _resolve_skill_mult(op, 7)
        assert mult == 1.0

    def test_with_direct_atk_skill_returns_multiplier(self) -> None:
        """攻击力提升至XX% 技能返回倍率。"""
        skill = {
            "name": "强力击",
            "sp_type": "自动回复",
            "trigger": "手动触发",
            "levels": [{"description": "攻击力提升至300%", "sp_cost": 10, "init_sp": 5, "duration": "0"}],
        }
        op = _make_operator(skills=[skill])
        mult = _resolve_skill_mult(op, 7)
        assert mult == 3.0


class TestSnapshotResultTypeValidation:
    """SnapshotResult 类型验证。"""

    def test_has_outputs_and_execution_order(self) -> None:
        result = compute_snapshot_with_dag(
            {"名称": "T", "星级": 1, "职业": "先锋", "基础属性": {"atk": 100}},
        )
        assert isinstance(result, SnapshotResult)
        assert isinstance(result.outputs, dict)
        assert isinstance(result.execution_order, list)
        # 所有输出键为 str，值为 float
        for key, val in result.outputs.items():
            assert isinstance(key, str)
            assert isinstance(val, float)

    def test_outputs_has_all_four_keys(self) -> None:
        result = compute_snapshot_with_dag(
            {"名称": "T", "星级": 1, "职业": "先锋", "基础属性": {"atk": 100}},
        )
        assert "最终攻击力" in result.outputs
        assert "物理伤害" in result.outputs
        assert "法术伤害" in result.outputs
        assert "真伤伤害" in result.outputs


class TestAdapterWithNoneParams:
    """None 类可选参数行为。"""

    def test_skill_multiplier_none_uses_resolved(self) -> None:
        """skill_multiplier=None 时应回退到技能解析。"""
        result = compute_snapshot_with_dag(
            {"名称": "T", "星级": 1, "职业": "先锋", "基础属性": {"atk": 200}},
            skill_multiplier=None,
        )
        # 无技能时 _resolve_skill_mult 返回 1.0
        # 物理 = max(200-200, 200*0.05) = max(0, 10) = 10
        assert result.outputs["物理伤害"] == 10.0

    def test_all_defaults_work(self) -> None:
        """所有参数都用默认值时不出错。"""
        result = compute_snapshot_with_dag(
            {"名称": "T", "星级": 1, "职业": "先锋", "基础属性": {"atk": 100}},
        )
        assert result.outputs["最终攻击力"] == 100.0
