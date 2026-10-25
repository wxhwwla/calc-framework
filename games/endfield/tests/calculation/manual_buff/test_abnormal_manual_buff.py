#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""异常计算接入手动 buff 测试。"""

import unittest

from games.endfield.calc.damage.engine import DamageContext
from games.endfield.calc.manual_buff.physical import evaluate_physical_abnormal_total
from games.endfield.calc.manual_buff.spell import evaluate_spell_abnormal_total


class TestAbnormalManualBuff(unittest.TestCase):
    def test_physical_abnormal_per_occurrence_buffs(self):
        base_ctx = DamageContext(
            final_attack=1000.0,
            skill_multiplier=1.0,
            enemy_defense=0.0,
            crit_rate=0.0,
            crit_damage=0.0,
        )

        total_no_buffs, _bk = evaluate_physical_abnormal_total(
            context=base_ctx,
            crit_mode="non_crit",
            effects=[],
            counts={"猛击:0": 2, "倒地:0": 3},
            char_level=1,
        )

        total_with_buffs, bk2 = evaluate_physical_abnormal_total(
            context=base_ctx,
            crit_mode="non_crit",
            effects=[],
            counts={"猛击:0": 2, "倒地:0": 3},
            char_level=1,
            manual_buffs={
                "猛击:0:1": [{"effect_type": "易伤", "value": 0.50}],
                "倒地:0:2": [{"effect_type": "增幅", "value": 0.30}],
            },
        )

        self.assertGreater(total_with_buffs, total_no_buffs)

        self.assertAlmostEqual(bk2["猛击:0"] * 2 + bk2["倒地:0"] * 3, total_with_buffs)

    def test_spell_abnormal_per_occurrence_buffs(self):
        base_ctx = DamageContext(
            final_attack=1000.0,
            skill_multiplier=1.0,
            damage_type="法术-灼热",
            skill_type="异常",
            enemy_defense=0.0,
            crit_rate=0.0,
            crit_damage=0.0,
        )

        total_no_buffs, _bk = evaluate_spell_abnormal_total(
            context=base_ctx,
            crit_mode="non_crit",
            effects=[],
            counts={"灼热异常:0": 2, "灼热爆发:1": 1},
            char_level=1,
        )

        total_with_buffs, bk2 = evaluate_spell_abnormal_total(
            context=base_ctx,
            crit_mode="non_crit",
            effects=[],
            counts={"灼热异常:0": 2, "灼热爆发:1": 1},
            char_level=1,
            manual_buffs={
                "灼热异常:0:1": [{"effect_type": "易伤", "value": 0.30}],
                "灼热爆发:1:1": [{"effect_type": "增幅", "value": 0.20}],
            },
        )

        self.assertGreater(total_with_buffs, total_no_buffs)

        self.assertAlmostEqual(bk2["灼热异常:0"] * 2 + bk2["灼热爆发:1"] * 1, total_with_buffs)


if __name__ == "__main__":
    unittest.main()
