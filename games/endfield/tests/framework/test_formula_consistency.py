# SPDX-License-Identifier: AGPL-3.0
"""DAG 版 15 乘区函数 vs 本地引擎一致性测试。

验证 framework/adapters/endfield/functions.py 中的 compute_15_zone_damage
与 games/endfield/calc/damage/engine/calculate.calculate_single_hit_damage
在相同输入下输出一致。
"""

from __future__ import annotations

from typing import Any

import pytest
from framework.adapters.endfield.functions import (
    compute_15_zone_damage,
)
from games.endfield.calc.damage.engine.calculate import (
    calculate_single_hit_damage,
)
from games.endfield.calc.damage.engine.types import (
    DamageContext,
    DamageEffect,
)


def _ctx(**overrides: Any) -> DamageContext:
    defaults = {
        "final_attack": 2000.0,
        "skill_multiplier": 3.5,
        "crit_rate": 0.05,
        "crit_damage": 0.5,
        "damage_type": "物理",
        "skill_type": "战技",
        "is_unbalanced": False,
        "is_true_damage": False,
        "enemy_defense": 100.0,
        "enemy_resistance": 0.0,
        "ignore_resistance": 0.0,
        "imbalance_vulnerability_coeff": 1.3,
        "base_damage_bonus": 0.0,
        "damage_type_bonus": 0.0,
        "skill_type_bonus": 0.0,
        "imbalance_damage_bonus": 0.0,
        "other_damage_bonus": 0.0,
        "combo_stacks": 0,
        "break_defense_stacks": 0,
    }
    defaults.update(overrides)
    return DamageContext(**defaults)


def _dag_kwargs(
    ctx: DamageContext,
    crit_mode: str = "non_crit",
    effects: list[DamageEffect] | None = None,
) -> dict:
    """从 DamageContext 构建 compute_15_zone_damage 参数。"""
    kwargs: dict = {
        "final_attack": float(ctx.final_attack),
        "skill_multiplier": float(ctx.skill_multiplier),
        "base_damage_bonus": float(ctx.base_damage_bonus),
        "crit_rate": float(ctx.crit_rate),
        "crit_damage": float(ctx.crit_damage),
        "crit_mode": crit_mode,
        "damage_type_bonus": float(ctx.damage_type_bonus),
        "skill_type_bonus": float(ctx.skill_type_bonus),
        "imbalance_damage_bonus": float(ctx.imbalance_damage_bonus),
        "other_damage_bonus": float(ctx.other_damage_bonus),
        "enemy_defense": float(ctx.enemy_defense),
        "defense_change": 0.0,
        "is_true_damage": bool(ctx.is_true_damage),
        "imbalance_coeff": float(ctx.imbalance_vulnerability_coeff),
        "is_unbalanced": bool(ctx.is_unbalanced),
        "enemy_resistance": float(ctx.enemy_resistance),
        "ignore_resistance": float(ctx.ignore_resistance),
    }
    eff = effects or []
    for e in eff:
        v = float(e.value)
        t = str(e.effect_type)
        if t == "伤害减免":
            cur = kwargs.get("damage_reduction", 0.0)
            kwargs["damage_reduction"] = 1.0 - (1.0 - cur) * (1.0 - v)
        elif t == "增幅":
            kwargs["amplification"] = kwargs.get("amplification", 0.0) + v
        elif t == "虚弱":
            cur = kwargs.get("weakness", 0.0)
            kwargs["weakness"] = 1.0 - (1.0 - cur) * (1.0 - v)
        elif t == "庇护":
            kwargs.setdefault("_shelter_values", []).append(v)
            kwargs["shelter"] = max(kwargs["_shelter_values"])
        elif t == "脆弱":
            kwargs["fragile"] = kwargs.get("fragile", 0.0) + v
        elif t == "易伤":
            kwargs["vulnerability"] = kwargs.get("vulnerability", 0.0) + v
        elif t in ("伤害类型伤害加成", "技能类型伤害加成", "失衡伤害加成", "其他伤害加成"):
            kwargs["damage_type_bonus"] = kwargs.get("damage_type_bonus", 0.0) + v
        elif t == "无视抗性":
            kwargs["ignore_resistance"] = kwargs.get("ignore_resistance", 0.0) + v
        elif t == "抗性":
            kwargs["enemy_resistance"] = kwargs.get("enemy_resistance", 0.0) + v
        elif t == "防御":
            kwargs["defense_change"] = kwargs.get("defense_change", 0.0) + v
        elif t == "失衡易伤系数":
            kwargs["imbalance_coeff"] = v
        elif t == "非主控减伤":
            cur = kwargs.get("non_control_reduction", 0.0)
            kwargs["non_control_reduction"] = 1.0 - (1.0 - cur) * (1.0 - v)
        elif t == "连击增伤":
            kwargs["combo_bonus"] = kwargs.get("combo_bonus", 0.0) + v
        elif t == "特殊乘区":
            kwargs["special"] = kwargs.get("special", 1.0) * v
    return kwargs


class TestFormulaConsistency:
    """验证 DAG 函数与本地引擎输出一致。"""

    @pytest.mark.parametrize("crit_mode", ["non_crit", "expected", "always_crit"])
    def test_basic_non_crit(self, crit_mode: str) -> None:
        """基础伤害: 无效果，改变暴击模式。"""
        ctx = _ctx()
        local = calculate_single_hit_damage(ctx, crit_mode=crit_mode)  # type: ignore[arg-type]
        dag_val = compute_15_zone_damage(**_dag_kwargs(ctx, crit_mode=crit_mode))
        assert abs(local.final_damage - dag_val) < 0.001, (
            f"crit_mode={crit_mode}: local={local.final_damage:.4f} dag={dag_val:.4f}"
        )

    def test_true_damage(self) -> None:
        """真实伤害: 跳过防御区。"""
        ctx = _ctx(is_true_damage=True)
        local = calculate_single_hit_damage(ctx)
        dag_val = compute_15_zone_damage(**_dag_kwargs(ctx))
        assert abs(local.final_damage - dag_val) < 0.001

    def test_unbalanced(self) -> None:
        """失衡状态: 应用失衡易伤系数。"""
        ctx = _ctx(is_unbalanced=True)
        local = calculate_single_hit_damage(ctx)
        dag_val = compute_15_zone_damage(**_dag_kwargs(ctx))
        assert abs(local.final_damage - dag_val) < 0.001

    def test_zero_defense(self) -> None:
        """零防御: 防御区 = 1.0。"""
        ctx = _ctx(enemy_defense=0.0)
        local = calculate_single_hit_damage(ctx)
        dag_val = compute_15_zone_damage(**_dag_kwargs(ctx))
        assert abs(local.final_damage - dag_val) < 0.001

    def test_high_defense(self) -> None:
        """高防御: 验证防御区计算。"""
        ctx = _ctx(enemy_defense=500.0)
        local = calculate_single_hit_damage(ctx)
        dag_val = compute_15_zone_damage(**_dag_kwargs(ctx))
        assert abs(local.final_damage - dag_val) < 0.001

    def test_base_damage_bonus(self) -> None:
        """基础伤害提升。"""
        ctx = _ctx(base_damage_bonus=500.0)
        local = calculate_single_hit_damage(ctx)
        dag_val = compute_15_zone_damage(**_dag_kwargs(ctx))
        assert abs(local.final_damage - dag_val) < 0.001

    def test_damage_type_bonus(self) -> None:
        """伤害类型加成。"""
        ctx = _ctx(damage_type_bonus=0.3)
        local = calculate_single_hit_damage(ctx)
        dag_val = compute_15_zone_damage(**_dag_kwargs(ctx))
        assert abs(local.final_damage - dag_val) < 0.001

    def test_resistance_and_ignore(self) -> None:
        """敌人抗性 + 无视抗性。"""
        ctx = _ctx(enemy_resistance=30.0, ignore_resistance=10.0)
        local = calculate_single_hit_damage(ctx)
        dag_val = compute_15_zone_damage(**_dag_kwargs(ctx))
        assert abs(local.final_damage - dag_val) < 0.001

    def test_all_zones_at_once(self) -> None:
        """所有乘区同时设非默认值。"""
        ctx = _ctx(
            final_attack=3000.0,
            skill_multiplier=4.2,
            base_damage_bonus=200.0,
            crit_rate=0.3,
            crit_damage=1.8,
            enemy_defense=200.0,
            enemy_resistance=40.0,
            ignore_resistance=15.0,
            imbalance_vulnerability_coeff=1.5,
            is_unbalanced=True,
            damage_type_bonus=0.25,
            skill_type_bonus=0.15,
            imbalance_damage_bonus=0.1,
            other_damage_bonus=0.05,
        )
        local = calculate_single_hit_damage(ctx, crit_mode="expected")
        dag_val = compute_15_zone_damage(**_dag_kwargs(ctx, crit_mode="expected"))
        assert abs(local.final_damage - dag_val) < 0.001

    def test_with_effects_no_unknown(self) -> None:
        """效果列表: 所有已知效果累加到对应乘区。"""
        ctx = _ctx()
        effects = [
            DamageEffect(effect_type="增幅", value=0.2, source="src1", raw_text="增幅+20%"),
            DamageEffect(effect_type="伤害减免", value=0.15, source="src2", raw_text="减伤15%"),
            DamageEffect(effect_type="脆弱", value=0.3, source="src3", raw_text="脆弱+30%"),
            DamageEffect(effect_type="易伤", value=0.1, source="src4", raw_text="易伤+10%"),
            DamageEffect(effect_type="无视抗性", value=0.05, source="src5", raw_text="无视5%抗性"),
            DamageEffect(effect_type="防御", value=-50.0, source="src6", raw_text="减防50"),
            DamageEffect(effect_type="特殊乘区", value=0.8, source="src7", raw_text="特殊0.8"),
        ]
        local = calculate_single_hit_damage(ctx, effects=effects)
        dag_val = compute_15_zone_damage(**_dag_kwargs(ctx, effects=effects))
        assert abs(local.final_damage - dag_val) < 0.001, (
            f"local={local.final_damage:.4f} dag={dag_val:.4f}"
        )

    def test_multi_amplification_effects(self) -> None:
        """多个增幅效果累加。"""
        ctx = _ctx()
        effects = [
            DamageEffect(effect_type="增幅", value=0.1, source="src1", raw_text="增幅+10%"),
            DamageEffect(effect_type="增幅", value=0.15, source="src2", raw_text="增幅+15%"),
            DamageEffect(effect_type="增幅", value=0.05, source="src3", raw_text="增幅+5%"),
        ]
        local = calculate_single_hit_damage(ctx, effects=effects)
        dag_val = compute_15_zone_damage(**_dag_kwargs(ctx, effects=effects))
        assert abs(local.final_damage - dag_val) < 0.001

    def test_atypical_effect_types_pass_through(self) -> None:
        """效果类型未被识别时应返回 unknown_effects。"""
        ctx = _ctx()
        effects = [
            DamageEffect(effect_type="未知效果A", value=999.0, source="test", raw_text="未知A"),
            DamageEffect(effect_type="未知效果B", value=999.0, source="test", raw_text="未知B"),
        ]
        local = calculate_single_hit_damage(ctx, effects=effects)
        assert len(local.unknown_effects) == 2
        local_damage = local.final_damage

        dag_val = compute_15_zone_damage(**_dag_kwargs(ctx, effects=[]))
        assert abs(local_damage - dag_val) < 0.001, (
            "未知效果不应影响伤害结果"
        )
