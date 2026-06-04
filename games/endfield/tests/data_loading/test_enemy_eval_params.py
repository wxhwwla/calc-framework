# SPDX-License-Identifier: AGPL-3.0
"""覆盖 EnemyEvalParams 数据类和工厂方法。"""

from __future__ import annotations

from types import SimpleNamespace

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
