# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""覆盖 EnemyEvalParams 数据类和工厂方法。"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from games.endfield.data_loading.enemy_eval_params import EnemyEvalParams, build_search_job_inputs_from_request


class TestEnemyEvalParams:
    """EnemyEvalParams dataclass。"""

    def test_defaults(self) -> None:
        p = EnemyEvalParams()
        assert p.enemy_defense == 100.0
        assert p.enemy_resistance == 0.0
        assert p.ignore_resistance == 0.0
        assert p.imbalance_vulnerability_coeff == 1.3
        assert p.is_unbalanced is False
        assert p.is_true_damage is False
        assert p.combo_stacks == 0
        assert p.break_defense_stacks == 0
        assert p.attached_effect_multiplier == 1.0
        assert p.corrosion_duration_seconds == 15.0

    def test_custom_values(self) -> None:
        p = EnemyEvalParams(
            enemy_defense=500.0,
            enemy_resistance=0.25,
            ignore_resistance=0.1,
            combo_stacks=2,
            break_defense_stacks=3,
        )
        assert p.enemy_defense == 500.0
        assert p.enemy_resistance == 0.25
        assert p.combo_stacks == 2

    def test_combo_stacks_clamping_in_factory(self) -> None:
        """EnemyEvalParams 构造器不钳位，from_request/from_loadout 钳位。"""
        p = EnemyEvalParams(combo_stacks=10)
        assert p.combo_stacks == 10
        p2 = EnemyEvalParams(combo_stacks=-1)
        assert p2.combo_stacks == -1

    def test_break_defense_stacks_clamping_in_factory(self) -> None:
        p = EnemyEvalParams(break_defense_stacks=10)
        assert p.break_defense_stacks == 10

    def test_from_loadout_clamps_stacks(self) -> None:
        loadout = SimpleNamespace(combo_stacks=10, break_defense_stacks=10, enemy_defense=300)
        p = EnemyEvalParams.from_loadout(loadout)
        assert p.combo_stacks == 4
        assert p.break_defense_stacks == 4

    def test_from_loadout(self) -> None:
        loadout = SimpleNamespace(
            enemy_defense=300.0,
            enemy_resistance=0.1,
            combo_stacks=3,
        )
        p = EnemyEvalParams.from_loadout(loadout)
        assert p.enemy_defense == 300.0
        assert p.enemy_resistance == 0.1
        assert p.combo_stacks == 3
        assert p.ignore_resistance == 0.0  # 默认值

    def test_from_loadout_partial(self) -> None:
        loadout = SimpleNamespace()
        p = EnemyEvalParams.from_loadout(loadout)
        assert p.enemy_defense == 100.0
        assert p.is_unbalanced is False

    def test_from_request(self) -> None:
        req = SimpleNamespace(
            enemy_defense=400.0,
            enemy_resistance=0.2,
            combo_stacks=2,
        )
        p = EnemyEvalParams.from_request(req)
        assert p.enemy_defense == 400.0
        assert p.combo_stacks == 2

    def test_from_defense_only(self) -> None:
        p = EnemyEvalParams.from_defense_only(600.0)
        assert p.enemy_defense == 600.0
        assert p.enemy_resistance == 0.0

    def test_damage_context_fields(self) -> None:
        p = EnemyEvalParams(enemy_defense=300.0, combo_stacks=2)
        fields = p.damage_context_fields(final_attack=1000.0, skill_multiplier=2.0)
        assert fields["enemy_defense"] == 300.0
        assert fields["final_attack"] == 1000.0
        assert fields["skill_multiplier"] == 2.0
        assert fields["combo_stacks"] == 2
        assert fields["damage_type"] == "物理"
        assert fields["skill_type"] == "战技"

    def test_preview_cache_token(self) -> None:
        p = EnemyEvalParams(enemy_defense=300.0)
        token = p.preview_cache_token()
        assert len(token) == 10
        assert token[0] == 300.0

    def test_search_job_kwargs(self) -> None:
        p = EnemyEvalParams(enemy_defense=300.0, combo_stacks=2)
        kwargs = p.search_job_kwargs()
        assert kwargs["enemy_defense"] == 300.0
        assert kwargs["combo_stacks"] == 2
        assert len(kwargs) == 10

    def test_abnormal_eval_kwargs(self) -> None:
        p = EnemyEvalParams(attached_effect_multiplier=0.5, corrosion_duration_seconds=5.0)
        kwargs = p.abnormal_eval_kwargs()
        assert kwargs["attached_effect_multiplier"] == 0.5
        assert kwargs["corrosion_duration_seconds"] == 5.0

    def test_build_search_job_inputs_from_request_needs_full_data(self) -> None:
        """确保 build_search_job_inputs_from_request 在缺数据时不崩溃。"""
        req = SimpleNamespace(
            enemy_defense=300.0,
            char_data={"名称": "测试"},
            char_level=1,
            weapon_level=1,
            trust_level=0,
            skill_name="测试技能",
            skill_type="战技",
            skill_multiplier=1.0,
            damage_type="物理",
            weapon_scope_label="",
            equipment_scope_label="",
            all_weapons=[],
            current_weapon={},
            equipment_catalog={},
            fixed_equipment_names={},
            use_manual_multi_skill_counts=False,
            skill_1_level=8,
            skill_2_level=8,
            skill_3_level=8,
            manual_counts=None,
            physical_abnormal_counts=None,
            spell_abnormal_counts=None,
            damage_component_mode="skill_and_abnormal",
            use_expected_crit=False,
            include_conditional_equipment_crit=False,
            weapon_normal_levels=None,
            weapon_special_states=None,
            weapon_skill_values=None,
        )
        fixed_loadout = SimpleNamespace()
        result = build_search_job_inputs_from_request(req, fixed_loadout=fixed_loadout)
        assert result is not None
        assert result.char_level == 1
        assert result.skill_1_level == 8


# ── enemy_params.py 直接函数测试 ────────────────────────────────────────


class TestEnemyParamsFunctions:
    """enemy_params.py 中的独立函数。"""

    def test_default_enemy_params(self) -> None:
        from games.endfield.data_loading.enemy_params import default_enemy_params

        params = default_enemy_params()
        assert params["enemy_defense"] == 100.0
        assert params["enemy_resistance"] == 0.0
        assert params["imbalance_vulnerability_coeff"] == 1.3
        assert params["is_unbalanced"] is False
        assert params["combo_stacks"] == 0
        assert params["attached_effect_multiplier"] == 1.0
        assert params["corrosion_duration_seconds"] == 15.0
        assert params["break_defense_stacks"] == 0

    def test_default_is_copy(self) -> None:
        """default_enemy_params 每次返回新对象。"""
        from games.endfield.data_loading.enemy_params import default_enemy_params

        a = default_enemy_params()
        b = default_enemy_params()
        assert a is not b
        assert a == b

    def test_list_plugin_enemy_choices_includes_default(self) -> None:
        """list_plugin_enemy_choices 包含默认敌人。"""
        from games.endfield.data_loading.enemy_params import list_plugin_enemy_choices

        choices = list_plugin_enemy_choices()
        assert choices[0] == ("默认敌人", "")

    def test_ENEMY_PARAM_FIELDS(self) -> None:
        from games.endfield.data_loading.enemy_params import ENEMY_PARAM_FIELDS

        assert "enemy_defense" in ENEMY_PARAM_FIELDS
        assert "enemy_resistance" in ENEMY_PARAM_FIELDS
        assert "combo_stacks" in ENEMY_PARAM_FIELDS

    def test_resolve_enemy_defense_empty(self) -> None:
        from games.endfield.data_loading.enemy_params import resolve_enemy_defense

        assert resolve_enemy_defense("") == 100.0
        assert resolve_enemy_defense("", default=200.0) == 200.0

    def test_resolve_enemy_resistance_empty(self) -> None:
        from games.endfield.data_loading.enemy_params import resolve_enemy_resistance

        assert resolve_enemy_resistance("") == 0.0

    def test_resolve_ignore_resistance_empty(self) -> None:
        from games.endfield.data_loading.enemy_params import resolve_ignore_resistance

        assert resolve_ignore_resistance("") == 0.0

    def test_resolve_imbalance_vulnerability_empty(self) -> None:
        from games.endfield.data_loading.enemy_params import resolve_imbalance_vulnerability

        assert resolve_imbalance_vulnerability("") == 1.3

    def test_resolve_is_unbalanced_empty(self) -> None:
        from games.endfield.data_loading.enemy_params import resolve_is_unbalanced

        assert resolve_is_unbalanced("") is False
        assert resolve_is_unbalanced("", default=True) is True

    def test_resolve_enemy_tier_empty(self) -> None:
        from games.endfield.data_loading.enemy_params import resolve_enemy_tier

        assert resolve_enemy_tier("") == "普通"

    def test_resolve_enemy_max_hp_empty(self) -> None:
        from games.endfield.data_loading.enemy_params import resolve_enemy_max_hp

        assert resolve_enemy_max_hp("") is None
        assert resolve_enemy_max_hp("", default=10000.0) == 10000.0

    def test_enemy_damage_context_overrides_empty(self) -> None:
        from games.endfield.data_loading.enemy_params import enemy_damage_context_overrides

        result = enemy_damage_context_overrides("")
        assert result["enemy_defense"] == 100.0
        assert result["is_unbalanced"] is False

    @patch("games.endfield.data_loading.enemy_params.get_plugin_registry")
    def test_resolve_enemy_defense_with_id(self, mock_reg: MagicMock) -> None:
        """resolve_enemy_defense 通过插件 id 查找。"""
        from games.endfield.data_loading.enemy_params import resolve_enemy_defense

        mock_instance = MagicMock()
        mock_instance.get_enemy.return_value = {"enemy_defense": 500.0}
        mock_reg.return_value = mock_instance
        assert resolve_enemy_defense("some_id") == 500.0

    @patch("games.endfield.data_loading.enemy_params.get_plugin_registry")
    def test_resolve_enemy_defense_with_id_missing(self, mock_reg: MagicMock) -> None:
        """resolve_enemy_defense 插件 id 不存在时返回默认值。"""
        from games.endfield.data_loading.enemy_params import resolve_enemy_defense

        mock_instance = MagicMock()
        mock_instance.get_enemy.return_value = None
        mock_reg.return_value = mock_instance
        assert resolve_enemy_defense("missing_id") == 100.0

    @patch("games.endfield.data_loading.enemy_params.get_plugin_registry")
    def test_resolve_enemy_resistance_with_id(self, mock_reg: MagicMock) -> None:
        from games.endfield.data_loading.enemy_params import resolve_enemy_resistance

        mock_instance = MagicMock()
        mock_instance.get_enemy.return_value = {"enemy_resistance": 0.25}
        mock_reg.return_value = mock_instance
        assert resolve_enemy_resistance("some_id") == 0.25

    @patch("games.endfield.data_loading.enemy_params.get_plugin_registry")
    def test_resolve_ignore_resistance_with_id(self, mock_reg: MagicMock) -> None:
        from games.endfield.data_loading.enemy_params import resolve_ignore_resistance

        mock_instance = MagicMock()
        mock_instance.get_enemy.return_value = {"ignore_resistance": 0.1}
        mock_reg.return_value = mock_instance
        assert resolve_ignore_resistance("some_id") == 0.1

    @patch("games.endfield.data_loading.enemy_params.get_plugin_registry")
    def test_resolve_imbalance_vulnerability_with_id(self, mock_reg: MagicMock) -> None:
        from games.endfield.data_loading.enemy_params import resolve_imbalance_vulnerability

        mock_instance = MagicMock()
        mock_instance.get_enemy.return_value = {"imbalance_vulnerability_coeff": 1.5}
        mock_reg.return_value = mock_instance
        assert resolve_imbalance_vulnerability("some_id") == 1.5

    @patch("games.endfield.data_loading.enemy_params.get_plugin_registry")
    def test_resolve_is_unbalanced_with_id(self, mock_reg: MagicMock) -> None:
        from games.endfield.data_loading.enemy_params import resolve_is_unbalanced

        mock_instance = MagicMock()
        mock_instance.get_enemy.return_value = {"is_unbalanced": True}
        mock_reg.return_value = mock_instance
        assert resolve_is_unbalanced("some_id") is True

    @patch("games.endfield.data_loading.enemy_params.get_plugin_registry")
    def test_resolve_enemy_tier_with_id(self, mock_reg: MagicMock) -> None:
        from games.endfield.data_loading.enemy_params import resolve_enemy_tier

        mock_instance = MagicMock()
        mock_instance.get_enemy.return_value = {"enemy_tier": "精英"}
        mock_reg.return_value = mock_instance
        assert resolve_enemy_tier("some_id") == "精英"

    @patch("games.endfield.data_loading.enemy_params.get_plugin_registry")
    def test_resolve_enemy_tier_with_etc_fallback(self, mock_reg: MagicMock) -> None:
        """enemy_tier 降级到 等阶 字段。"""
        from games.endfield.data_loading.enemy_params import resolve_enemy_tier

        mock_instance = MagicMock()
        mock_instance.get_enemy.return_value = {"等阶": "BOSS"}
        mock_reg.return_value = mock_instance
        assert resolve_enemy_tier("some_id") == "BOSS"

    @patch("games.endfield.data_loading.enemy_params.get_plugin_registry")
    def test_resolve_enemy_max_hp_with_id(self, mock_reg: MagicMock) -> None:
        from games.endfield.data_loading.enemy_params import resolve_enemy_max_hp

        mock_instance = MagicMock()
        mock_instance.get_enemy.return_value = {"enemy_max_hp": 50000.0}
        mock_reg.return_value = mock_instance
        assert resolve_enemy_max_hp("some_id") == 50000.0

    @patch("games.endfield.data_loading.enemy_params.get_plugin_registry")
    def test_enemy_damage_context_overrides_with_id(self, mock_reg: MagicMock) -> None:
        from games.endfield.data_loading.enemy_params import enemy_damage_context_overrides

        mock_instance = MagicMock()
        mock_instance.get_enemy.return_value = {
            "enemy_defense": 300.0,
            "enemy_resistance": 0.15,
        }
        mock_reg.return_value = mock_instance
        result = enemy_damage_context_overrides("some_id")
        assert result["enemy_defense"] == 300.0
        assert result["enemy_resistance"] == 0.15

    @patch("games.endfield.data_loading.enemy_params.get_plugin_registry")
    def test_list_plugin_enemy_choices_with_plugins(self, mock_reg: MagicMock) -> None:
        """list_plugin_enemy_choices 包含插件敌人。"""
        from games.endfield.data_loading.enemy_params import list_plugin_enemy_choices

        mock_instance = MagicMock()
        mock_instance.list_enemy_ids.return_value = ["enemy_01"]
        mock_instance.get_enemy.return_value = {"名称": "精英敌人", "enemy_defense": 300}
        mock_reg.return_value = mock_instance
        choices = list_plugin_enemy_choices()
        assert len(choices) == 2
        assert choices[1] == ("精英敌人 (防300)", "enemy_01")
