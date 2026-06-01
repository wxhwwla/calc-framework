# SPDX-License-Identifier: AGPL-3.0
"""ArknightsContextLoader 单元测试。"""

from __future__ import annotations

from games.arknights.calc.dag_adapter.loader import (
    ArknightsContextLoader,
    _get_num,
    _parse_potential_atk,
)


class TestGetNum:
    def test_existing_key(self) -> None:
        assert _get_num({"atk": 100}, "atk") == 100.0

    def test_missing_key_returns_default(self) -> None:
        assert _get_num({"atk": 100}, "def") == 0.0

    def test_custom_default(self) -> None:
        assert _get_num({}, "res", 50.0) == 50.0

    def test_string_number(self) -> None:
        assert _get_num({"atk": "150"}, "atk") == 150.0

    def test_none_value(self) -> None:
        assert _get_num({"atk": None}, "atk") == 0.0

    def test_empty_dict(self) -> None:
        assert _get_num({}, "atk") == 0.0


class TestParsePotentialAtk:
    def test_single_atk_bonus(self) -> None:
        pots = ["攻击力+30"]
        assert _parse_potential_atk(pots) == 30.0

    def test_multiple_atk_bonuses(self) -> None:
        pots = ["攻击力+30", "部署费用-1", "攻击力+45"]
        assert _parse_potential_atk(pots) == 75.0

    def test_no_atk_bonus(self) -> None:
        pots = ["部署费用-1", "生命上限+200"]
        assert _parse_potential_atk(pots) == 0.0

    def test_empty_list(self) -> None:
        assert _parse_potential_atk([]) == 0.0

    def test_mixed_content(self) -> None:
        pots = ["生命上限+200", "部署费用-1", "攻击力+30", "天赋效果增强"]
        assert _parse_potential_atk(pots) == 30.0

    def test_invalid_number_skipped(self) -> None:
        """攻击力+后跟非数值字符串 → 跳过（触发 ValueError）"""
        pots = ["攻击力+abc", "攻击力+30"]
        assert _parse_potential_atk(pots) == 30.0


class TestArknightsContextLoader:
    def test_build_context_has_correct_keys(self, amiya_operator: dict) -> None:
        loader = ArknightsContextLoader()
        ctx = loader.build_context(operator=amiya_operator)

        assert "character" in ctx
        assert "enemy" in ctx
        assert "computed" in ctx

        assert "攻击力" in ctx["character"]
        assert "防御" in ctx["character"]
        assert "信赖攻击" in ctx["character"]
        assert "潜能攻击" in ctx["character"]

        assert "防御" in ctx["enemy"]
        assert "法术抗性" in ctx["enemy"]

        assert "技能倍率" in ctx["computed"]
        assert "攻击力百分比加成" in ctx["computed"]
        assert "伤害加成" in ctx["computed"]
        assert "物理穿透" in ctx["computed"]
        assert "法术穿透" in ctx["computed"]

    def test_build_context_amiya_values(self, amiya_operator: dict) -> None:
        loader = ArknightsContextLoader()
        ctx = loader.build_context(operator=amiya_operator)

        assert ctx["character"]["攻击力"] == 390.0
        assert ctx["character"]["防御"] == 81.0
        assert ctx["character"]["法术抗性"] == 10.0
        assert ctx["character"]["信赖攻击"] == 70.0
        assert ctx["character"]["潜能攻击"] == 30.0

        assert ctx["enemy"]["防御"] == 200.0
        assert ctx["enemy"]["法术抗性"] == 50.0

        assert ctx["computed"]["技能倍率"] == 1.0
        assert ctx["computed"]["攻击力百分比加成"] == 0.0
        assert ctx["computed"]["伤害加成"] == 0.0
        assert ctx["computed"]["物理穿透"] == 0.0
        assert ctx["computed"]["法术穿透"] == 0.0

    def test_build_context_with_custom_params(self, amiya_operator: dict) -> None:
        loader = ArknightsContextLoader()
        ctx = loader.build_context(
            operator=amiya_operator,
            skill_multiplier=1.5,
            enemy_def=300.0,
            enemy_res=60.0,
            atk_percent_bonus=0.1,
            dmg_bonus=0.05,
            def_penetration=50.0,
            res_penetration=0.2,
        )

        assert ctx["computed"]["技能倍率"] == 1.5
        assert ctx["enemy"]["防御"] == 300.0
        assert ctx["enemy"]["法术抗性"] == 60.0
        assert ctx["computed"]["攻击力百分比加成"] == 0.1
        assert ctx["computed"]["伤害加成"] == 0.05
        assert ctx["computed"]["物理穿透"] == 50.0
        assert ctx["computed"]["法术穿透"] == 0.2

    def test_build_context_minimal_operator(self, minimal_operator: dict) -> None:
        loader = ArknightsContextLoader()
        ctx = loader.build_context(operator=minimal_operator)

        assert ctx["character"]["攻击力"] == 100.0
        assert ctx["character"]["防御"] == 50.0
        assert ctx["character"]["法术抗性"] == 0.0
        assert ctx["character"]["信赖攻击"] == 0.0
        assert ctx["character"]["潜能攻击"] == 0.0

    def test_build_context_with_skill_level(self, amiya_operator: dict) -> None:
        loader = ArknightsContextLoader()
        ctx = loader.build_context(operator=amiya_operator, skill_level=10)
        assert "技能倍率" in ctx["computed"]
