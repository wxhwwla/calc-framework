# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""测试 DataContextLoader 输出格式 — 验证 loader 返回的上下文结构正确。

TODO: 根据实际游戏的数据字段调整断言。
"""

from __future__ import annotations

from games._template.calc.dag_adapter.loader import TEMPLATEContextLoader


class TestTEMPLATEContextLoader:
    def test_build_context_returns_expected_keys(self, sample_character: dict) -> None:
        loader = TEMPLATEContextLoader()
        ctx = loader.build_context(character=sample_character)

        assert "character" in ctx
        assert "enemy" in ctx
        assert "computed" in ctx

    def test_character_keys(self, sample_character: dict) -> None:
        loader = TEMPLATEContextLoader()
        ctx = loader.build_context(character=sample_character)

        char = ctx["character"]
        assert "攻击力" in char
        assert "防御" in char
        assert "信赖攻击" in char
        assert "潜能攻击" in char

    def test_enemy_defaults(self) -> None:
        loader = TEMPLATEContextLoader()
        ctx = loader.build_context(character={"name": "test", "atk": 100})

        enemy = ctx["enemy"]
        assert enemy["防御"] == 200.0
        assert enemy["法术抗性"] == 50.0

    def test_computed_keys(self) -> None:
        loader = TEMPLATEContextLoader()
        ctx = loader.build_context(
            character={"name": "test", "atk": 100},
            atk_percent_bonus=0.5,
            dmg_bonus=0.3,
        )

        comp = ctx["computed"]
        assert comp["攻击力百分比加成"] == 0.5
        assert comp["伤害加成"] == 0.3

    def test_build_context_minimal(self) -> None:
        """最简输入不应抛异常。"""
        loader = TEMPLATEContextLoader()
        ctx = loader.build_context(character={"atk": 50})
        assert ctx["character"]["攻击力"] == 50.0

    def test_output_values_are_float(self, sample_character: dict) -> None:
        loader = TEMPLATEContextLoader()
        ctx = loader.build_context(character=sample_character)

        for val in ctx["character"].values():
            assert isinstance(val, float), f"Expected float, got {type(val)}: {val}"
