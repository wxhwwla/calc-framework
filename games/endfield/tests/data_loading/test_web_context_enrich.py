#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""Web context enrichment 测试。"""

from __future__ import annotations

import unittest

from games.endfield.data_loading.web_context_enrich import (
    enrich_adapter_context,
    iter_manual_buff_entries,
    resolve_equipment_modifiers,
)


class TestWebContextEnrich(unittest.TestCase):
    _CATALOG = {
        "chest": [
            {
                "名称": "测试护甲",
                "装备种类": "护甲",
                "部位": "护甲",
                "套装": "",
                "属性词条": ["力量50", "攻击力30"],
                "效果": [],
                "三件套效果": [],
            }
        ],
        "gloves": [],
        "accessories": [],
    }

    def test_resolve_equipment_flat_stats(self) -> None:
        effects, flats, atk_pct = resolve_equipment_modifiers(
            fixed_equipment_names={"chest": "测试护甲", "gloves": None, "accessory_a": None, "accessory_b": None},
            equipment_catalog=self._CATALOG,
        )
        self.assertAlmostEqual(flats.get("力量", 0.0), 50.0)
        self.assertAlmostEqual(flats.get("攻击力", 0.0), 30.0)
        self.assertEqual(atk_pct, 0.0)
        self.assertEqual(len(effects), 0)

    def test_manual_buff_flattens(self) -> None:
        store = {
            "战技:1:1": [{"effect_type": "其他伤害加成", "value": 0.1}],
            "连携技:1:1": [{"effect_type": "暴击率", "value": 0.05}],
        }
        entries = iter_manual_buff_entries(store)
        self.assertEqual(len(entries), 2)

    def test_enrich_applies_manual_buff_and_skill_multiplier(self) -> None:
        class _Loadout:
            skill_multiplier = 1.5
            extra_crit_rate = 0.02
            extra_crit_damage = 0.1
            manual_buffs = {"战技:1:1": [{"effect_type": "其他伤害加成", "value": 0.08}]}

        ctx = {
            "character": {"暴击率": 0.05, "暴击伤害": 0.5},
            "computed": {"伤害加成": 1.0, "技能倍率": 1.0},
            "equipment": {},
            "user_input": {},
        }
        enrich_adapter_context(ctx, _Loadout(), flat_stats={"攻击力": 10.0})
        self.assertAlmostEqual(ctx["computed"]["技能倍率"], 1.5)
        self.assertAlmostEqual(ctx["character"]["暴击率"], 0.07)
        self.assertAlmostEqual(ctx["computed"]["伤害加成"], 1.08)
        self.assertAlmostEqual(ctx["equipment"]["攻击力平值"], 10.0)


if __name__ == "__main__":
    unittest.main()
