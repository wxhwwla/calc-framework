# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""终末地 ComputeSheet 上下文映射测试。

覆盖 P0-01 追加问题：桌面确认计算时 ComputeSheet 只拿到 17 个输入值，
缺少 ``computed.主能力平值加算`` 等 DAG 必需变量，导致乘区表直接失败。
此外验证原始敌人输入被换算成正确的乘区值（而不是把百分比直接加进乘区）。
"""

from __future__ import annotations

import pytest
from games.endfield.gui.app.compute_sheet_variables import apply_endfield_sheet_context


def _base_context() -> dict:
    return {
        "character": {"暴击率": 0.05, "暴击伤害": 0.5},
        "computed": {
            "抗性": 1.0,
            "失衡易伤": 1.0,
            "伤害加成": 1.0,
            "易伤": 1.0,
            "连击增伤": 1.0,
        },
        "enemy": {"防御": 100.0},
    }


def _user_inputs(**overrides) -> dict:
    values = {
        "user_input.敌人防御": 100.0,
        "user_input.敌人抗性": 0.0,
        "user_input.无视抗性": 0.0,
        "user_input.失衡易伤系数": 1.3,
        "user_input.是否失衡": False,
        "user_input.是否真实伤害": False,
        "user_input.连击层数": 0,
        "user_input.额外暴击率": 0.0,
        "user_input.额外暴击伤害": 0.0,
        "user_input.额外伤害加成": 0.0,
        "user_input.破防层数": 0,
    }
    values.update(overrides)
    return values


class TestResistanceZone:
    def test_enemy_resistance_becomes_multiplier(self):
        ctx = apply_endfield_sheet_context(
            _base_context(),
            _user_inputs(**{"user_input.敌人抗性": 20.0}),
        )

        assert ctx["computed"]["抗性"] == pytest.approx(0.8)

    def test_ignore_resistance_offsets_enemy_resistance(self):
        ctx = apply_endfield_sheet_context(
            _base_context(),
            _user_inputs(**{"user_input.敌人抗性": 20.0, "user_input.无视抗性": 5.0}),
        )

        assert ctx["computed"]["抗性"] == pytest.approx(0.85)

    def test_negative_resistance_increases_damage(self):
        ctx = apply_endfield_sheet_context(
            _base_context(),
            _user_inputs(**{"user_input.敌人抗性": -20.0}),
        )

        assert ctx["computed"]["抗性"] == pytest.approx(1.2)


class TestImbalanceZone:
    def test_not_unbalanced_forces_zone_to_one(self):
        ctx = apply_endfield_sheet_context(
            _base_context(),
            _user_inputs(**{"user_input.失衡易伤系数": 1.5, "user_input.是否失衡": False}),
        )

        assert ctx["computed"]["失衡易伤"] == pytest.approx(1.0)

    def test_unbalanced_uses_coefficient(self):
        ctx = apply_endfield_sheet_context(
            _base_context(),
            _user_inputs(**{"user_input.失衡易伤系数": 1.5, "user_input.是否失衡": True}),
        )

        assert ctx["computed"]["失衡易伤"] == pytest.approx(1.5)


class TestDefenseAndTrueDamage:
    def test_enemy_defense_written_to_context(self):
        ctx = apply_endfield_sheet_context(
            _base_context(),
            _user_inputs(**{"user_input.敌人防御": 420.0}),
        )

        assert ctx["enemy"]["防御"] == pytest.approx(420.0)

    def test_true_damage_ignores_enemy_defense(self):
        ctx = apply_endfield_sheet_context(
            _base_context(),
            _user_inputs(**{"user_input.敌人防御": 420.0, "user_input.是否真实伤害": True}),
        )

        assert ctx["enemy"]["防御"] == pytest.approx(0.0)


class TestComboAndBreakDefense:
    def test_combo_zone_uses_ultimate_table(self):
        ctx = apply_endfield_sheet_context(
            _base_context(),
            _user_inputs(**{"user_input.连击层数": 1}),
            skill_type="终结技",
        )

        assert ctx["computed"]["连击增伤"] == pytest.approx(1.2)

    def test_combo_zone_uses_skill_table(self):
        ctx = apply_endfield_sheet_context(
            _base_context(),
            _user_inputs(**{"user_input.连击层数": 1}),
            skill_type="战技",
        )

        assert ctx["computed"]["连击增伤"] == pytest.approx(1.3)

    def test_break_defense_adds_vulnerability_on_top_of_base(self):
        base = _base_context()
        base["computed"]["易伤"] = 1.1

        ctx = apply_endfield_sheet_context(
            base,
            _user_inputs(**{"user_input.破防层数": 2}),
        )

        assert ctx["computed"]["易伤"] == pytest.approx(1.26)


class TestCritInputs:
    def test_extra_crit_applied_on_top_of_base_character(self):
        ctx = apply_endfield_sheet_context(
            _base_context(),
            _user_inputs(**{"user_input.额外暴击率": 0.10, "user_input.额外暴击伤害": 0.20}),
            use_expected_crit=True,
        )

        assert ctx["character"]["暴击率"] == pytest.approx(0.15)
        assert ctx["character"]["暴击伤害"] == pytest.approx(0.70)

    def test_non_expected_crit_disables_crit_zone(self):
        ctx = apply_endfield_sheet_context(
            _base_context(),
            _user_inputs(**{"user_input.额外暴击率": 0.10}),
            use_expected_crit=False,
        )

        assert ctx["character"]["暴击率"] == pytest.approx(0.0)

    def test_extra_damage_bonus_adds_to_zone(self):
        base = _base_context()
        base["computed"]["伤害加成"] = 1.1

        ctx = apply_endfield_sheet_context(
            base,
            _user_inputs(**{"user_input.额外伤害加成": 0.2}),
        )

        assert ctx["computed"]["伤害加成"] == pytest.approx(1.3)


class TestMissingValues:
    def test_missing_user_values_use_safe_defaults(self):
        ctx = apply_endfield_sheet_context({}, {})

        assert ctx["computed"]["抗性"] == pytest.approx(1.0)
        assert ctx["computed"]["失衡易伤"] == pytest.approx(1.0)
        assert ctx["enemy"]["防御"] == pytest.approx(100.0)
        assert ctx["computed"]["连击增伤"] == pytest.approx(1.0)
