# SPDX-License-Identifier: AGPL-3.0
from __future__ import annotations

from unittest.mock import patch

from games.endfield.gui.shared.damage_visualization import (
    DamageSlice,
    build_damage_pie_figure,
    build_improvement_bar_figure,
    damage_breakdown_from_skill_map,
    is_matplotlib_available,
)


class TestIsMatplotlibAvailable:
    def test_returns_bool(self) -> None:
        result = is_matplotlib_available()

        assert isinstance(result, bool)


class TestDamageBreakdownFromSkillMap:
    def test_positive_values(self) -> None:
        result = damage_breakdown_from_skill_map({"战技:1": 1000.0, "连携技:1": 2000.0})

        assert len(result) == 2

        assert result[0].label == "战技:1"

        assert result[1].value == 2000.0

    def test_filters_zero_values(self) -> None:
        result = damage_breakdown_from_skill_map({"战技:1": 0.0, "连携技:1": 2000.0})

        assert len(result) == 1

        assert result[0].label == "连携技:1"

    def test_filters_negative_values(self) -> None:
        result = damage_breakdown_from_skill_map({"战技:1": -100.0, "连携技:1": 2000.0})

        assert len(result) == 1

        assert result[0].label == "连携技:1"

    def test_empty_dict(self) -> None:
        result = damage_breakdown_from_skill_map({})

        assert result == ()

    def test_all_zero(self) -> None:
        result = damage_breakdown_from_skill_map({"a": 0.0, "b": 0.0})

        assert result == ()


class TestBuildDamagePieFigure:
    def test_no_data(self) -> None:
        fig = build_damage_pie_figure([], title="测试")

        assert fig is not None

    def test_with_data(self) -> None:
        slices = [DamageSlice(label="A", value=100.0), DamageSlice(label="B", value=200.0)]

        fig = build_damage_pie_figure(slices, title="测试")

        assert fig is not None

    def test_single_slice(self) -> None:
        slices = [DamageSlice(label="唯一", value=500.0)]

        fig = build_damage_pie_figure(slices)

        assert fig is not None


class TestBuildImprovementBarFigure:
    def test_empty_no_crash(self) -> None:
        fig = build_improvement_bar_figure([])

        assert fig is not None

    def test_with_data(self) -> None:
        items = [("方案A", 10.0), ("方案B", 20.0), ("方案C", -5.0)]

        fig = build_improvement_bar_figure(items)

        assert fig is not None

    def test_single_item(self) -> None:
        items = [("唯一", 15.0)]

        fig = build_improvement_bar_figure(items)

        assert fig is not None


class TestMatplotlibNotAvailable:
    def test_no_crash(self) -> None:
        with patch("utils.optional_deps.is_matplotlib_available", return_value=False):
            result = is_matplotlib_available()

            assert result is False
