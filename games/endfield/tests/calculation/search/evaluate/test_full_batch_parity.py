# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""Rust 全批量 vs Python evaluate_task 小规模伤害一致性。"""

from __future__ import annotations

import importlib.util
import os
import unittest
from unittest import mock

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


def _runtime_eq(name: str, kind: str, affixes: list[str] | None = None) -> dict:
    from games.endfield.calc.equipment.system import build_runtime_equipment_from_local_record

    return build_runtime_equipment_from_local_record(
        {
            "名称": name,
            "装备种类": kind,
            "套装": "验",
            "效果": [],
            "三件套效果": [],
            "属性词条": list(affixes or []),
        }
    )


def _score_key(score) -> tuple:
    return (
        score.weapon_name,
        score.loadout_names.get("chest", ""),
        score.loadout_names.get("gloves", ""),
        score.loadout_names.get("accessory_a", ""),
        score.loadout_names.get("accessory_b", ""),
    )


@unittest.skipUnless(_full_batch_symbol_available(), "rust_search 无 evaluate_full_batch_py")
class TestFullBatchExpandedParity(unittest.TestCase):
    """扩大样本：多武器×多装备、暴击矩阵、能力词条、runner 端到端。"""

    def tearDown(self) -> None:
        os.environ.pop("CALC_RUST_FULL_BATCH", None)
        os.environ.pop("RUST_SEARCH_FALLBACK", None)

    def _fixture(self) -> tuple:
        from games.endfield.calc.loadout.attack_eval import final_attack_details_for_loadout

        catalog = {
            "chest": [
                _runtime_eq("胸攻", "护甲", ["攻击力15", "攻击力8%"]),
                _runtime_eq("胸力", "护甲", ["力量25", "攻击力5"]),
            ],
            "gloves": [
                _runtime_eq("手1", "护手", ["攻击力5"]),
                _runtime_eq("手2", "护手", []),
            ],
            "accessories": [
                _runtime_eq("件A", "配件", ["攻击力3%"]),
                _runtime_eq("件B", "配件", ["力量10"]),
            ],
        }
        char = {
            "名称": "验角",
            "主能力": "力量",
            "基础攻击力": [180.0] * 90,
            "力量": [40.0] * 90,
        }
        weapons_data = {
            "武甲": {"名称": "武甲", "类型": "单手剑", "基础攻击力": [220.0] * 90},
            "武乙": {"名称": "武乙", "类型": "单手剑", "基础攻击力": [280.0] * 90},
        }
        weapons = []
        for name, wdata in weapons_data.items():
            bare = final_attack_details_for_loadout(
                character=char,
                weapon=wdata,
                char_level=90,
                weapon_level=90,
                trust_level=2,
            )
            weapons.append(WeaponCandidate(name=name, final_attack=float(bare["final_attack"])))
        search_eval = SearchEvalContext(
            char_data=char,
            char_level=90,
            weapon_level=90,
            trust_level=2,
            weapon_data_by_name=weapons_data,
        )
        base = DamageContext(
            final_attack=0.0,
            skill_multiplier=2.5,
            skill_type="战技",
            damage_type="物理",
            enemy_defense=120.0,
            enemy_resistance=5.0,
            crit_rate=0.35,
            crit_damage=0.85,
        )
        return catalog, weapons, search_eval, base, char

    def _assert_batch_matches_tasks(self, *, crit_mode: str) -> int:
        catalog, weapons, search_eval, base, char = self._fixture()
        config = OptimizerConfig(top_n=50, prune_non_beneficial=False, warn_on_unfiltered=False)
        tasks = list(
            enumerate_optimizer_tasks(
                base_context=base,
                weapons=weapons,
                equipment_catalog=catalog,
                config=config,
            )[0]
        )
        self.assertGreaterEqual(len(tasks), 16)  # 2×2×2×2
        ref = {}
        for t in tasks:
            s = evaluate_task(
                base_context=base,
                crit_mode=crit_mode,  # type: ignore[arg-type]
                task=t,
                search_eval=search_eval,
            )
            ref[_score_key(s)] = s.final_damage

        batch = evaluate_full_batch_rust(
            weapons=weapons,
            equipment_catalog=catalog,
            char_data=char,
            char_level=90,
            base_context=base,
            top_n=len(tasks),
            crit_mode=crit_mode,
            allow_duplicate_accessory=True,
            search_eval=search_eval,
        )
        self.assertEqual(len(batch), len(tasks), msg=crit_mode)
        for score in batch:
            key = _score_key(score)
            self.assertIn(key, ref)
            self.assertAlmostEqual(
                score.final_damage,
                ref[key],
                places=4,
                msg=f"{crit_mode} {key}",
            )
        return len(tasks)

    def test_crit_mode_matrix_matches_evaluate_task(self) -> None:
        counts = []
        for mode in ("non_crit", "always_crit", "expected"):
            with self.subTest(crit_mode=mode):
                counts.append(self._assert_batch_matches_tasks(crit_mode=mode))
        self.assertTrue(all(c == counts[0] for c in counts))

    def test_memory_runner_full_batch_matches_soa_topn(self) -> None:
        """端到端：开启全批量后 TopN 应与关闭时（SoA）一致。"""
        from games.endfield.calc.loadout.in_memory_optimizer import run_enumerated_optimizer_parallel

        catalog, weapons, search_eval, base, _char = self._fixture()
        config = OptimizerConfig(top_n=5, prune_non_beneficial=False, warn_on_unfiltered=False)

        os.environ.pop("CALC_RUST_FULL_BATCH", None)
        soa_top, soa_total, soa_processed, _, _ = run_enumerated_optimizer_parallel(
            base_context=base,
            weapons=weapons,
            equipment_catalog=catalog,
            config=config,
            search_eval=search_eval,
            max_workers=1,
        )

        os.environ["CALC_RUST_FULL_BATCH"] = "1"
        with mock.patch(
            "games.endfield.calc.search.evaluate.full_batch_eval._rust_full_batch_importable",
            return_value=True,
        ):
            fb_top, fb_total, fb_processed, _, _ = run_enumerated_optimizer_parallel(
                base_context=base,
                weapons=weapons,
                equipment_catalog=catalog,
                config=config,
                search_eval=search_eval,
                max_workers=1,
            )

        self.assertEqual(soa_total, fb_total)
        self.assertEqual(soa_processed, fb_processed)
        self.assertEqual(len(soa_top), len(fb_top))
        # 同分时枚举顺序可能不同：按伤害降序 + 配装键稳定排序后再比
        soa_sorted = sorted(soa_top, key=lambda s: (-s.final_damage, _score_key(s)))
        fb_sorted = sorted(fb_top, key=lambda s: (-s.final_damage, _score_key(s)))
        for a, b in zip(soa_sorted, fb_sorted):
            self.assertEqual(_score_key(a), _score_key(b))
            self.assertAlmostEqual(a.final_damage, b.final_damage, places=4)


if __name__ == "__main__":
    unittest.main()
