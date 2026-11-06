# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""全批量最终攻击力预计算：按装备属性签名记忆化，结果与逐个重算一致。"""

from __future__ import annotations

import unittest
from unittest import mock

from games.endfield.calc.loadout import attack_eval
from games.endfield.calc.loadout.attack_eval import final_attack_details_for_loadout
from games.endfield.calc.loadout.optimizer import WeaponCandidate
from games.endfield.calc.search.evaluate.context import SearchEvalContext
from games.endfield.calc.search.evaluate.full_batch_eval import _precompute_final_attacks_for_batch

_CHAR = {
    "名称": "测角",
    "主能力": "力量",
    "副能力": "敏捷",
    "基础攻击力": [150.0] * 90,
    "力量": [40.0] * 90,
    "敏捷": [30.0] * 90,
}

_WEAPONS = {
    "武器甲": {
        "名称": "武器甲",
        "类型": "单手剑",
        "基础攻击力": [250.0] * 90,
        "normal_skills": [{"effect": "攻击力+", "curve": [10.0, 20.0]}],
    },
    "武器乙": {
        "名称": "武器乙",
        "类型": "单手剑",
        "基础攻击力": [300.0] * 90,
    },
}


def _search_eval(*, weapon_names: tuple[str, ...] = ("武器甲", "武器乙")) -> SearchEvalContext:
    return SearchEvalContext(
        char_data=_CHAR,
        char_level=90,
        weapon_level=90,
        trust_level=2,
        weapon_data_by_name={name: _WEAPONS[name] for name in weapon_names},
        weapon_normal_levels=(6,),
        weapon_special_states=(),
    )


def _weapons(*names: str) -> list[WeaponCandidate]:
    return [WeaponCandidate(name=name, final_attack=1000.0) for name in names]


def _expected(
    *,
    weapons: list[WeaponCandidate],
    flat_stats: list[dict[str, float]],
    atk_percents: list[float],
    search_eval: SearchEvalContext,
) -> list[float]:
    result: list[float] = []
    for weapon in weapons:
        weapon_data = search_eval.weapon_data_by_name[weapon.name]
        for stats, atk_percent in zip(flat_stats, atk_percents):
            details = final_attack_details_for_loadout(
                character=search_eval.char_data,
                weapon=weapon_data,
                char_level=search_eval.char_level,
                weapon_level=search_eval.weapon_level,
                trust_level=search_eval.trust_level,
                weapon_normal_levels=list(search_eval.weapon_normal_levels),
                weapon_special_states=list(search_eval.weapon_special_states),
                equipment_stat_bonus=stats,
                equipment_attack_percent=atk_percent,
            )
            result.append(float(details["final_attack"]))
    return result


class TestPrecomputeFinalAttacks(unittest.TestCase):
    def test_duplicate_signatures_are_computed_once_per_weapon(self) -> None:
        flat_stats = [
            {"攻击力": 20.0, "力量": 10.0, "敏捷": 5.0},
            {"攻击力": 20.0, "力量": 10.0, "敏捷": 5.0},
            {"攻击力": 35.0, "力量": 10.0, "敏捷": 5.0},
        ]
        atk_percents = [0.1, 0.1, 0.2]
        search_eval = _search_eval()
        weapons = _weapons("武器甲", "武器乙")

        with mock.patch.object(
            attack_eval,
            "final_attack_details_for_loadout",
            wraps=attack_eval.final_attack_details_for_loadout,
        ) as spy:
            attacks = _precompute_final_attacks_for_batch(
                weapons=weapons,
                equipment_flat_stats=flat_stats,
                equipment_atk_percents=atk_percents,
                search_eval=search_eval,
            )

        assert attacks is not None
        self.assertEqual(len(attacks), 6)
        # 2 武器 × 2 个唯一签名（前两条重复，第三条不同）
        self.assertEqual(spy.call_count, 4)
        self.assertEqual(
            attacks,
            _expected(weapons=weapons, flat_stats=flat_stats, atk_percents=atk_percents, search_eval=search_eval),
        )

    def test_uncached_values_match_direct_calculation(self) -> None:
        flat_stats = [
            {"攻击力": 12.0, "力量": 4.0},
            {"攻击力": 0.0, "敏捷": 8.0},
            {"攻击力": 50.0, "力量": 20.0, "敏捷": 15.0},
        ]
        atk_percents = [0.0, 0.05, 0.25]
        search_eval = _search_eval(weapon_names=("武器甲",))
        weapons = _weapons("武器甲")

        attacks = _precompute_final_attacks_for_batch(
            weapons=weapons,
            equipment_flat_stats=flat_stats,
            equipment_atk_percents=atk_percents,
            search_eval=search_eval,
        )

        self.assertEqual(
            attacks,
            _expected(weapons=weapons, flat_stats=flat_stats, atk_percents=atk_percents, search_eval=search_eval),
        )

    def test_same_equipment_stats_differ_across_weapons(self) -> None:
        flat_stats = [{"攻击力": 20.0, "力量": 10.0}]
        atk_percents = [0.1]
        search_eval = _search_eval()
        weapons = _weapons("武器甲", "武器乙")

        attacks = _precompute_final_attacks_for_batch(
            weapons=weapons,
            equipment_flat_stats=flat_stats,
            equipment_atk_percents=atk_percents,
            search_eval=search_eval,
        )

        assert attacks is not None
        self.assertEqual(len(attacks), 2)
        self.assertNotEqual(attacks[0], attacks[1])

    def test_missing_weapon_data_returns_none(self) -> None:
        search_eval = _search_eval(weapon_names=("武器甲",))

        attacks = _precompute_final_attacks_for_batch(
            weapons=_weapons("武器甲", "未知武器"),
            equipment_flat_stats=[{"攻击力": 10.0}],
            equipment_atk_percents=[0.0],
            search_eval=search_eval,
        )

        self.assertIsNone(attacks)


if __name__ == "__main__":
    unittest.main()
