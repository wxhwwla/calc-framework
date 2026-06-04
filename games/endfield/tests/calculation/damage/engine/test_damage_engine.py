#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""单段伤害引擎行为测试。"""

import unittest

from games.endfield.calc.damage.engine import (
    DamageContext,
    DamageEffect,
    DamageResult,
    calculate_single_hit_damage,
)


class TestDamageEngine(unittest.TestCase):
    def test_single_hit_contains_all_zones_with_non_crit_default(self):
        result = calculate_single_hit_damage(
            DamageContext(
                final_attack=1000.0,
                skill_multiplier=2.0,
            )
        )

        self.assertEqual(result.crit_mode, "non_crit")

        self.assertAlmostEqual(result.zone_values["基础伤害区"], 2000.0)

        self.assertAlmostEqual(result.zone_values["暴击区"], 1.0)

        self.assertAlmostEqual(result.zone_values["防御区"], 0.5)

        self.assertAlmostEqual(result.final_damage, 1000.0)

        self.assertEqual(
            tuple(result.zone_values.keys()),
            (
                "基础伤害区",
                "暴击区",
                "伤害加成区",
                "伤害减免区",
                "增幅区",
                "虚弱区",
                "庇护区",
                "脆弱区",
                "易伤区",
                "防御区",
                "失衡易伤区",
                "抗性区",
                "非主控减伤区",
                "连击增伤区",
                "特殊乘区",
            ),
        )

    def test_crit_modes_non_crit_expected_and_always_crit(self):
        base = DamageContext(
            final_attack=1000.0,
            skill_multiplier=1.0,
            enemy_defense=0.0,
            crit_rate=0.5,
            crit_damage=1.0,
        )

        non_crit = calculate_single_hit_damage(base)

        expected = calculate_single_hit_damage(base, crit_mode="expected")

        always = calculate_single_hit_damage(base, crit_mode="always_crit")

        self.assertAlmostEqual(non_crit.final_damage, 1000.0)

        self.assertAlmostEqual(expected.final_damage, 1500.0)

        self.assertAlmostEqual(always.final_damage, 2000.0)

    def test_unknown_effects_are_recorded_without_breaking_calculation(self):
        result = calculate_single_hit_damage(
            DamageContext(
                final_attack=1000.0,
                skill_multiplier=1.0,
                enemy_defense=0.0,
            ),
            effects=[
                DamageEffect(
                    effect_type="神秘增伤",
                    value=0.25,
                    source="测试来源",
                    raw_text="神秘增伤+25%",
                )
            ],
        )

        self.assertAlmostEqual(result.final_damage, 1000.0)

        self.assertEqual(len(result.unknown_effects), 1)

        self.assertEqual(result.unknown_effects[0]["effect_type"], "神秘增伤")

        self.assertTrue(any("神秘增伤" in w for w in result.warnings))

    def test_effect_scope_and_stack_rules_apply_as_expected(self):
        result = calculate_single_hit_damage(
            DamageContext(
                final_attack=1000.0,
                skill_multiplier=1.0,
                enemy_defense=0.0,
                damage_type="法术-寒冷",
            ),
            effects=[
                DamageEffect(effect_type="易伤", value=0.20, damage_types=("法术-寒冷",)),
                DamageEffect(effect_type="易伤", value=0.50, damage_types=("物理",)),
                DamageEffect(effect_type="虚弱", value=0.10),
                DamageEffect(effect_type="虚弱", value=0.20),
                DamageEffect(effect_type="庇护", value=0.30),
                DamageEffect(effect_type="庇护", value=0.90),
            ],
        )
        self.assertAlmostEqual(result.zone_values["易伤区"], 1.2)
        self.assertAlmostEqual(result.zone_values["虚弱区"], 0.72)
        self.assertAlmostEqual(result.zone_values["庇护区"], 0.1)
        self.assertAlmostEqual(result.final_damage, 86.4)

    # ── helpers.py 未覆盖分支 ────────────────────────────────────────────

    def test_clamp_no_upper(self) -> None:
        """_clamp 仅指定 lower 的路径。"""
        from games.endfield.calc.damage.engine.helpers import _clamp

        self.assertEqual(_clamp(5.0, 0.0), 5.0)
        self.assertEqual(_clamp(-1.0, 0.0), 0.0)

    def test_resolve_crit_zone_always_crit(self) -> None:
        """_resolve_crit_zone always_crit 模式。"""
        from games.endfield.calc.damage.engine.helpers import _resolve_crit_zone

        ctx = DamageContext(final_attack=1000.0, crit_damage=0.5)
        result = _resolve_crit_zone(ctx, "always_crit")
        self.assertAlmostEqual(result, 1.5)

    def test_resolve_crit_zone_crit_damage_clamped(self) -> None:
        """_resolve_crit_zone crit_damage clamp 到 0。"""
        from games.endfield.calc.damage.engine.helpers import _resolve_crit_zone

        ctx = DamageContext(final_attack=1000.0, crit_rate=0.5, crit_damage=-0.2)
        result = _resolve_crit_zone(ctx, "expected")
        # crit_damage clamped to 0 => 1 + 0.5 * 0 = 1.0
        self.assertAlmostEqual(result, 1.0)

    def test_match_scope_skill_type_filter(self) -> None:
        """_match_scope skill_types 过滤。"""
        from games.endfield.calc.damage.engine.helpers import _match_scope

        ctx = DamageContext(final_attack=1000.0, skill_type="战技")
        effect_match = DamageEffect(effect_type="易伤", value=0.1, skill_types=("战技",))
        effect_mismatch = DamageEffect(effect_type="易伤", value=0.1, skill_types=("普攻",))
        self.assertTrue(_match_scope(ctx, effect_match))
        self.assertFalse(_match_scope(ctx, effect_mismatch))

    def test_match_scope_require_unbalanced(self) -> None:
        """_match_scope require_unbalanced 过滤。"""
        from games.endfield.calc.damage.engine.helpers import _match_scope

        ctx_unbalanced = DamageContext(final_attack=1000.0, is_unbalanced=True)
        ctx_balanced = DamageContext(final_attack=1000.0, is_unbalanced=False)
        effect_needs_unbalanced = DamageEffect(effect_type="易伤", value=0.1, require_unbalanced=True)
        effect_needs_balanced = DamageEffect(effect_type="易伤", value=0.1, require_unbalanced=False)
        self.assertTrue(_match_scope(ctx_unbalanced, effect_needs_unbalanced))
        self.assertFalse(_match_scope(ctx_unbalanced, effect_needs_balanced))
        self.assertTrue(_match_scope(ctx_balanced, effect_needs_balanced))

    def test_collect_effects_known_but_out_of_scope(self) -> None:
        """已知效果但作用域不匹配时不应加入 known。"""
        from games.endfield.calc.damage.engine.helpers import _collect_effects

        ctx = DamageContext(final_attack=1000.0, skill_type="战技")
        effects = [
            DamageEffect(effect_type="易伤", value=0.1, skill_types=("普攻",)),
        ]
        known, unknown, warnings = _collect_effects(ctx, effects)
        self.assertEqual(len(known), 0)
        self.assertEqual(len(unknown), 0)

    def test_damage_context_defaults(self) -> None:
        """DamageContext 默认值验证。"""
        ctx = DamageContext(final_attack=1000.0)
        self.assertEqual(ctx.skill_multiplier, 1.0)
        self.assertEqual(ctx.damage_type, "物理")
        self.assertEqual(ctx.is_unbalanced, False)
        self.assertEqual(ctx.is_true_damage, False)
        self.assertEqual(ctx.enemy_defense, 100.0)
        self.assertEqual(ctx.crit_rate, 0.05)
        self.assertEqual(ctx.crit_damage, 0.5)
        self.assertEqual(ctx.combo_stacks, 0)
        self.assertEqual(ctx.break_defense_stacks, 0)

    def test_damage_effect_defaults(self) -> None:
        """DamageEffect 默认值验证。"""
        effect = DamageEffect(effect_type="易伤", value=0.1)
        self.assertEqual(effect.stack_rule, "add")
        self.assertEqual(effect.damage_types, ())
        self.assertEqual(effect.skill_types, ())
        self.assertIsNone(effect.require_unbalanced)
        self.assertEqual(effect.source, "")
        self.assertEqual(effect.raw_text, "")

    def test_damage_result_dataclass(self) -> None:
        """DamageResult 数据类构造。"""
        from games.endfield.calc.damage.engine.types import ZONE_ORDER

        result = DamageResult(
            final_damage=1000.0,
            zone_values={z: 1.0 for z in ZONE_ORDER},
            crit_mode="non_crit",
            warnings=(),
            unknown_effects=(),
        )
        self.assertAlmostEqual(result.final_damage, 1000.0)
        self.assertEqual(len(result.zone_values), 15)


if __name__ == "__main__":
    unittest.main()
