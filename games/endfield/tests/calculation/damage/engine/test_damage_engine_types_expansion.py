# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""伤害引擎类型的覆盖扩展测试（P2-07 从 test_coverage_expansion.py 拆分）。"""

from __future__ import annotations


class TestDamageEngineTypes:
    """Damage engine types creation and properties."""

    def test_damage_context_creation(self):
        from games.endfield.calc.damage.engine.types import DamageContext

        ctx = DamageContext(
            final_attack=1000.0,
            skill_multiplier=1.5,
            damage_type="物理",
            skill_type="普通攻击",
            is_unbalanced=False,
        )
        assert ctx.final_attack == 1000.0
        assert ctx.skill_multiplier == 1.5
        assert ctx.damage_type == "物理"
        assert ctx.skill_type == "普通攻击"
        assert ctx.is_unbalanced is False

    def test_damage_effect_creation_basic(self):
        from games.endfield.calc.damage.engine.types import DamageEffect

        effect = DamageEffect(
            effect_type="伤害类型伤害加成",
            value=0.20,
            source="test",
            raw_text="物理伤害20%",
        )
        assert effect.effect_type == "伤害类型伤害加成"
        assert effect.value == 0.20
        assert effect.source == "test"
        assert effect.raw_text == "物理伤害20%"

    def test_damage_effect_with_skill_types(self):
        from games.endfield.calc.damage.engine.types import DamageEffect

        effect = DamageEffect(
            effect_type="技能类型伤害加成",
            value=0.15,
            source="test",
            raw_text="战技伤害15%",
            skill_types=("战技",),
        )
        assert effect.skill_types == ("战技",)

    def test_damage_effect_with_damage_types(self):
        from games.endfield.calc.damage.engine.types import DamageEffect

        effect = DamageEffect(
            effect_type="伤害类型伤害加成",
            value=0.10,
            source="test",
            raw_text="物理伤害10%",
            damage_types=("物理",),
        )
        assert effect.damage_types == ("物理",)

    def test_damage_result_creation(self):
        from games.endfield.calc.damage.engine.types import DamageResult

        result = DamageResult(
            final_damage=1500.0,
            zone_values={"基础伤害区": 1000.0, "暴击区": 1.0},
            crit_mode="non_crit",
            warnings=(),
            unknown_effects=(),
        )
        assert result.final_damage == 1500.0
        assert isinstance(result.zone_values, dict)

    def test_damage_context_default_is_unbalanced(self):
        from games.endfield.calc.damage.engine.types import DamageContext

        ctx = DamageContext(
            final_attack=500.0,
            skill_multiplier=1.0,
            damage_type="物理",
            skill_type="普通攻击",
        )
        assert ctx.is_unbalanced is False

    def test_known_effect_types(self):
        from games.endfield.calc.damage.engine.types import KNOWN_EFFECT_TYPES

        assert isinstance(KNOWN_EFFECT_TYPES, tuple | list | set | frozenset)
        assert len(KNOWN_EFFECT_TYPES) > 0

    def test_zone_order(self):
        from games.endfield.calc.damage.engine.types import ZONE_ORDER

        assert isinstance(ZONE_ORDER, tuple | list)
        assert len(ZONE_ORDER) > 0

    def test_crit_mode_literal_values(self):
        from typing import get_args

        from games.endfield.calc.damage.engine.types import CritMode

        values = set(get_args(CritMode))
        assert "non_crit" in values
        assert "expected" in values
        assert "always_crit" in values

    def test_damage_effect_repr(self):
        from games.endfield.calc.damage.engine.types import DamageEffect

        effect = DamageEffect(
            effect_type="易伤",
            value=0.20,
            source="test",
        )
        r = repr(effect)
        assert "易伤" in r or "DamageEffect" in r
