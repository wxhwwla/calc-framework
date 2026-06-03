#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""增强功能与工具模块的补充覆盖率测试。"""



import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from games.endfield.calc.core.parallel_evaluate import evaluate_parallel
from games.endfield.calc.core.preview_cache import cached_preview, sync_confirm_dependencies
from games.endfield.calc.core.result_cache import get_global_result_cache, reset_global_result_cache
from games.endfield.calc.equipment.system import build_runtime_equipment_from_wiki_draft
from games.endfield.data_loading.enemy_params import (
    DEFAULT_ENEMY_DEFENSE,
    enemy_damage_context_overrides,
    list_plugin_enemy_choices,
    resolve_enemy_defense,
)
from games.endfield.data_loading.plugin_registry import PluginRegistry
from games.endfield.gui.app.loadout_preset import (
    BATCH_PRESET_SCHEMA,
    LoadoutPreset,
    export_preset_batch_json,
    import_presets_from_json_text,
)
from games.endfield.gui.shared.calc_history import CalculationHistory, HistoryEntry
from games.endfield.gui.shared.damage_visualization import (
    build_damage_pie_figure,
    build_improvement_bar_figure,
    damage_breakdown_from_skill_map,
    is_matplotlib_available,
)
from games.endfield.gui.shared.preset_batch_compare import compare_presets_parallel
from utils.operation_log import LogLevel, OperationLog


class TestLoadoutPresetBatch(unittest.TestCase):

    def test_batch_roundtrip(self) -> None:

        presets = [

            LoadoutPreset(

                char_name="A",

                weapon_name="W",

                char_level=1,

                weapon_level=1,

                trust_level=0,

                skill_levels=(1, 0, 0),

                calculation_mode="single_hit",

                weapon_scope="",

                equipment_scope="",

                fixed_equipment_names={},

                multi_skill_counts={},

                use_manual_multi_skill_counts=False,

                note="方案A",

            )

        ]

        text = export_preset_batch_json(presets)

        data = json.loads(text)

        self.assertEqual(data["schema"], BATCH_PRESET_SCHEMA)

        restored = import_presets_from_json_text(text)

        self.assertEqual(len(restored), 1)

        self.assertEqual(restored[0].note, "方案A")





class TestEnemyParamsExtended(unittest.TestCase):

    def test_list_choices_includes_default_and_plugins(self) -> None:

        reg = PluginRegistry()

        with tempfile.TemporaryDirectory() as tmp:

            root = Path(tmp)

            (root / "enemies").mkdir()

            (root / "enemies" / "e.json").write_text(

                json.dumps(

                    {"id": "boss", "名称": "首领", "enemy_defense": 300.0},

                    ensure_ascii=False,

                ),

                encoding="utf-8",

            )

            reg.load_from_directory(root)

            with patch("games.endfield.data_loading.enemy_params.get_plugin_registry", return_value=reg):

                choices = list_plugin_enemy_choices()

        self.assertEqual(choices[0][1], "")

        self.assertTrue(any(c[1] == "boss" for c in choices))



    def test_enemy_damage_context_overrides(self) -> None:

        reg = PluginRegistry()

        with tempfile.TemporaryDirectory() as tmp:

            root = Path(tmp)

            (root / "enemies").mkdir()

            (root / "enemies" / "x.json").write_text(

                json.dumps(

                    {

                        "id": "x",

                        "enemy_defense": 200.0,

                        "enemy_resistance": 0.15,

                    },

                    ensure_ascii=False,

                ),

                encoding="utf-8",

            )

            reg.load_from_directory(root)

        with patch("games.endfield.data_loading.enemy_params.get_plugin_registry", return_value=reg):

            empty = enemy_damage_context_overrides("")

            self.assertEqual(empty["enemy_defense"], DEFAULT_ENEMY_DEFENSE)

            full = enemy_damage_context_overrides("x")

        self.assertEqual(full["enemy_defense"], 200.0)

        self.assertAlmostEqual(full["enemy_resistance"], 0.15)



    def test_resolve_unknown_id_returns_default(self) -> None:

        with patch("games.endfield.data_loading.enemy_params.get_plugin_registry", return_value=PluginRegistry()):

            self.assertEqual(resolve_enemy_defense("missing", default=88.0), 88.0)





class TestEvaluateParallelGeneric(unittest.TestCase):

    def test_evaluate_parallel_preserves_order(self) -> None:

        items = list(range(8))



        def double(x: int) -> int:

            return x * 2



        out = evaluate_parallel(items, double, max_workers=3)

        self.assertEqual(out, [0, 2, 4, 6, 8, 10, 12, 14])





class TestPresetBatchCompareMultiSkill(unittest.TestCase):

    def _fixtures(self):

        char = {

            "名称": "测",

            "战技倍率": [[150] * 3],

            "连携技倍率": [[100] * 3],

            "终结技倍率": [[50] * 3],

            "基础攻击力": [100] * 3,

        }

        weapon = {"名称": "武", "基础攻击力": [100] * 3}

        equip = build_runtime_equipment_from_wiki_draft(

            {"名称": "甲", "_wiki_params": {"装备种类": "护甲", "所属套组": "X"}}

        )

        return char, weapon, [equip]



    def test_manual_counts_use_weighted_total(self) -> None:

        char, weapon, equipments = self._fixtures()

        preset = LoadoutPreset(

            char_name="测",

            weapon_name="武",

            char_level=1,

            weapon_level=1,

            trust_level=0,

            skill_levels=(1, 1, 0),

            calculation_mode="multi_skill_search",

            weapon_scope="",

            equipment_scope="",

            fixed_equipment_names={"chest": "甲"},

            multi_skill_counts={"战技": 2, "连携技": 1, "终结技": 0},

            use_manual_multi_skill_counts=True,

        )

        rows = compare_presets_parallel(

            [preset],

            characters=[char],

            weapons=[weapon],

            equipments=equipments,

        )

        self.assertEqual(len(rows), 1)

        self.assertFalse(rows[0].error)

        self.assertGreater(rows[0].final_damage, 0)





class TestMiscEnhancements(unittest.TestCase):

    def test_sync_confirm_enemy_defense_invalidates_cache(self) -> None:

        reset_global_result_cache()

        kwargs = dict(

            char_data={"名称": "c"},

            weapon_data={"名称": "w"},

            char_level=1,

            weapon_level=1,

            trust_level=0,

            skill_levels=(1, 0, 0),

            calculation_mode="single_hit",

        )

        sync_confirm_dependencies(**kwargs, enemy_defense=100.0)  # type: ignore[arg-type]

        cached_preview("z", lambda: 1)

        sync_confirm_dependencies(**kwargs, enemy_defense=200.0)  # type: ignore[arg-type]

        _, hit = cached_preview("z", lambda: 2)

        self.assertFalse(hit)

        self.assertGreater(get_global_result_cache().stats()["dependencies"], 0)



    def test_history_invalid_index_returns_none(self) -> None:

        history = CalculationHistory(max_entries=2)

        history.push(HistoryEntry(label="a", summary="s", preset_snapshot={}))

        self.assertIsNone(history.get_snapshot(5))



    def test_operation_log_clear_and_hidden_detail_filter(self) -> None:

        log = OperationLog(min_level=LogLevel.DEBUG)

        log.record(LogLevel.DEBUG, "trace", {"_hidden": 1, "visible": 2})

        entry = log.export_payload()["entries"][0]

        filtered = log._entries[0].to_dict(include_debug_fields=False)

        self.assertNotIn("_hidden", filtered["detail"])

        self.assertIn("visible", filtered["detail"])

        log.clear()

        self.assertEqual(len(log.export_payload()["entries"]), 0)

        self.assertEqual(entry["action"], "trace")



    @unittest.skipUnless(is_matplotlib_available(), "需要 matplotlib")

    def test_bar_figure_custom_ylabel(self) -> None:

        import matplotlib



        matplotlib.use("Agg")

        import matplotlib.pyplot as plt



        fig = build_improvement_bar_figure(

            [("乘区A", 30.0), ("乘区B", 70.0)],

            title="占比",

            ylabel="占比 %",

        )

        self.assertEqual(fig.axes[0].get_ylabel(), "占比 %")

        plt.close(fig)



    @unittest.skipUnless(is_matplotlib_available(), "需要 matplotlib")

    def test_pie_figure_empty_data(self) -> None:

        import matplotlib



        matplotlib.use("Agg")

        import matplotlib.pyplot as plt



        fig = build_damage_pie_figure((), title="空")

        plt.close(fig)



    def test_breakdown_filters_non_positive(self) -> None:

        parts = damage_breakdown_from_skill_map({"战技": 0.0, "连携技": 10.0})

        self.assertEqual(len(parts), 1)

        self.assertEqual(parts[0].label, "连携技")





if __name__ == "__main__":

    unittest.main()

