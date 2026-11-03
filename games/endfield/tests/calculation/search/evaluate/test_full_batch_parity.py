# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""Rust 全批量 vs Python evaluate_task 小规模伤害一致性。"""

from __future__ import annotations

import importlib.util
import os
import unittest

from games.endfield.calc.damage.engine import DamageContext
from games.endfield.calc.loadout.optimizer import (
    OptimizerConfig,
    WeaponCandidate,
    enumerate_optimizer_tasks,
    evaluate_task,
)
from games.endfield.calc.search.evaluate.context import SearchEvalContext
from games.endfield.calc.search.evaluate.full_batch_eval import evaluate_full_batch_rust


def _eq(name: str, kind: str) -> dict:
    return {
        "名称": name,
        "装备种类": kind,
        "效果": [],
        "三件套效果": [],
        "属性词条": [],
    }


def _full_batch_symbol_available() -> bool:
    if importlib.util.find_spec("rust_search") is None:
        return False
    try:
        import rust_search as _rs
    except ImportError:
        return False
    return hasattr(_rs, "evaluate_full_batch_py")


@unittest.skipUnless(_full_batch_symbol_available(), "rust_search 无 evaluate_full_batch_py")
class TestFullBatchDamageParity(unittest.TestCase):
    """在「无角色基础攻、无装备攻%」简化条件下，全批量与逐任务应一致。

    说明：Rust ``calculate_final_attack`` 使用 ``char_base + weapon.final_attack``；
    当 char_base=0 且装备无平铺/攻% 时，与 Python 侧直接使用 ``weapon.final_attack`` 对齐。
    """

    def tearDown(self) -> None:
        os.environ.pop("CALC_RUST_FULL_BATCH", None)
        os.environ.pop("RUST_SEARCH_FALLBACK", None)

    def test_top_scores_match_evaluate_task_when_char_base_zero(self) -> None:
        catalog = {
            "chest": [_eq("胸1", "护甲")],
            "gloves": [_eq("手1", "护手")],
            "accessories": [_eq("件1", "配件"), _eq("件2", "配件")],
        }
        weapons = [
            WeaponCandidate(name="武器A", final_attack=1000.0),
            WeaponCandidate(name="武器B", final_attack=1200.0),
        ]
        base = DamageContext(
            final_attack=0.0,
            skill_multiplier=2.0,
            skill_type="战技",
            damage_type="物理",
            enemy_defense=100.0,
            crit_rate=0.0,
            crit_damage=0.5,
        )
        search_eval = SearchEvalContext(
            char_data={"名称": "测", "基础攻击": [0.0]},
            char_level=90,
            weapon_level=90,
            trust_level=0,
            # 故意不提供 weapon_data，使 evaluate_task 不重算攻击力
            weapon_data_by_name={},
        )
        config = OptimizerConfig(top_n=5, prune_non_beneficial=False, warn_on_unfiltered=False)

        tasks = list(
            enumerate_optimizer_tasks(
                base_context=base,
                weapons=weapons,
                equipment_catalog=catalog,
                config=config,
            )[0]
        )
        self.assertGreater(len(tasks), 1)

        ref_by_key: dict[tuple, float] = {}
        for task in tasks:
            score = evaluate_task(
                base_context=base,
                crit_mode="non_crit",
                task=task,
                search_eval=search_eval,
            )
            key = (
                score.weapon_name,
                score.loadout_names.get("chest", ""),
                score.loadout_names.get("gloves", ""),
                score.loadout_names.get("accessory_a", ""),
                score.loadout_names.get("accessory_b", ""),
            )
            ref_by_key[key] = score.final_damage

        batch_scores = evaluate_full_batch_rust(
            weapons=weapons,
            equipment_catalog=catalog,
            char_data=search_eval.char_data,
            char_level=search_eval.char_level,
            base_context=base,
            top_n=len(tasks),
            crit_mode="non_crit",
            allow_duplicate_accessory=True,
        )
        self.assertEqual(len(batch_scores), len(tasks))

        for score in batch_scores:
            key = (
                score.weapon_name,
                score.loadout_names.get("chest", ""),
                score.loadout_names.get("gloves", ""),
                score.loadout_names.get("accessory_a", ""),
                score.loadout_names.get("accessory_b", ""),
            )
            self.assertIn(key, ref_by_key)
            self.assertAlmostEqual(score.final_damage, ref_by_key[key], places=4, msg=str(key))


@unittest.skipUnless(_full_batch_symbol_available(), "rust_search 无 evaluate_full_batch_py")
class TestFullBatchSearchEvalParity(unittest.TestCase):
    """带 search_eval 重算攻击力（装备平铺/攻%）时，全批量应与 evaluate_task 一致。"""

    def tearDown(self) -> None:
        os.environ.pop("CALC_RUST_FULL_BATCH", None)
        os.environ.pop("RUST_SEARCH_FALLBACK", None)

    def test_matches_evaluate_task_with_equip_flat_and_percent(self) -> None:
        from games.endfield.calc.equipment.system import build_runtime_equipment_from_local_record

        chest = build_runtime_equipment_from_local_record(
            {
                "名称": "胸甲高攻",
                "装备种类": "护甲",
                "套装": "测",
                "效果": [],
                "三件套效果": [],
                "属性词条": ["攻击力20", "攻击力10%"],
            }
        )
        gloves = build_runtime_equipment_from_local_record(
            {
                "名称": "护手平",
                "装备种类": "护手",
                "套装": "测",
                "效果": [],
                "三件套效果": [],
                "属性词条": [],
            }
        )
        acc = build_runtime_equipment_from_local_record(
            {
                "名称": "配件平",
                "装备种类": "配件",
                "套装": "测",
                "效果": [],
                "三件套效果": [],
                "属性词条": [],
            }
        )
        catalog = {"chest": [chest], "gloves": [gloves], "accessories": [acc]}
        char = {"名称": "测角", "基础攻击力": [150.0] * 90}
        weapon_data = {"名称": "测武", "类型": "单手剑", "基础攻击力": [250.0] * 90}
        # 无装备最终攻 = 150+250 = 400（与 job 构建 WeaponCandidate 一致）
        from games.endfield.calc.loadout.attack_eval import final_attack_details_for_loadout

        bare = final_attack_details_for_loadout(
            character=char,
            weapon=weapon_data,
            char_level=90,
            weapon_level=90,
        )
        weapons = [WeaponCandidate(name="测武", final_attack=float(bare["final_attack"]))]
        search_eval = SearchEvalContext(
            char_data=char,
            char_level=90,
            weapon_level=90,
            trust_level=0,
            weapon_data_by_name={"测武": weapon_data},
        )
        base = DamageContext(
            final_attack=0.0,
            skill_multiplier=2.0,
            skill_type="战技",
            damage_type="物理",
            enemy_defense=100.0,
            crit_rate=0.0,
            crit_damage=0.5,
        )
        config = OptimizerConfig(top_n=5, prune_non_beneficial=False, warn_on_unfiltered=False)
        tasks = list(
            enumerate_optimizer_tasks(
                base_context=base,
                weapons=weapons,
                equipment_catalog=catalog,
                config=config,
            )[0]
        )
        self.assertGreaterEqual(len(tasks), 1)

        ref = {
            (
                s.weapon_name,
                s.loadout_names.get("chest", ""),
                s.loadout_names.get("gloves", ""),
                s.loadout_names.get("accessory_a", ""),
                s.loadout_names.get("accessory_b", ""),
            ): s.final_damage
            for s in (
                evaluate_task(base_context=base, crit_mode="non_crit", task=t, search_eval=search_eval) for t in tasks
            )
        }
        # 装备后最终攻应高于裸装（否则本用例无意义）
        with_equip = final_attack_details_for_loadout(
            character=char,
            weapon=weapon_data,
            char_level=90,
            weapon_level=90,
            equipment_stat_bonus={"攻击力": 20.0},
            equipment_attack_percent=0.1,
        )
        self.assertGreater(float(with_equip["final_attack"]), float(bare["final_attack"]))

        batch_scores = evaluate_full_batch_rust(
            weapons=weapons,
            equipment_catalog=catalog,
            char_data=char,
            char_level=90,
            base_context=base,
            top_n=len(tasks),
            crit_mode="non_crit",
            allow_duplicate_accessory=True,
            search_eval=search_eval,
        )
        self.assertEqual(len(batch_scores), len(tasks))
        for score in batch_scores:
            key = (
                score.weapon_name,
                score.loadout_names.get("chest", ""),
                score.loadout_names.get("gloves", ""),
                score.loadout_names.get("accessory_a", ""),
                score.loadout_names.get("accessory_b", ""),
            )
            self.assertIn(key, ref)
            self.assertAlmostEqual(score.final_damage, ref[key], places=4, msg=str(key))


if __name__ == "__main__":
    unittest.main()
