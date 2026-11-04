# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""级联实体选择器纯逻辑测试（无 Qt 依赖）。"""

from calc_framework.ui.entity_cascade import (
    field_values,
    matching_records,
    option_displays,
    step_options,
)

_STEPS: list[dict[str, str]] = [
    {"field": "舰船分类", "label": "舰船种类"},
    {"field": "舰船", "label": "舰船"},
    {"field": "名称", "label": "武器", "display_field": "武器标签"},
]

_RECORDS: list[dict[str, object]] = [
    {
        "名称": "A · 炮1",
        "舰船分类": ["战机"],
        "舰船": "A",
        "武器标签": "炮1",
        "攻击": 1,
    },
    {
        "名称": "A · 炮2",
        "舰船分类": ["战机"],
        "舰船": "A",
        "武器标签": "炮2",
        "攻击": 2,
    },
    {
        "名称": "B · 炮1",
        "舰船分类": ["护卫舰", "登陆舰"],
        "舰船": "B",
        "武器标签": "炮1",
        "攻击": 3,
    },
    {
        "名称": "C · 刀",
        "舰船分类": ["未分类"],
        "舰船": "C",
        "武器标签": "刀",
        "攻击": 4,
    },
]


class TestFieldValues:
    def test_scalar_field_returns_single_value(self) -> None:
        assert field_values({"舰船": "A"}, "舰船") == ("A",)

    def test_list_field_returns_all_values(self) -> None:
        assert field_values({"舰船分类": ["护卫舰", "登陆舰"]}, "舰船分类") == (
            "护卫舰",
            "登陆舰",
        )

    def test_missing_or_empty_field_returns_empty(self) -> None:
        assert field_values({}, "舰船") == ()
        assert field_values({"舰船": ""}, "舰船") == ()
        assert field_values({"舰船": None}, "舰船") == ()
        assert field_values({"舰船分类": []}, "舰船分类") == ()


class TestStepOptions:
    def test_first_step_expands_list_values_in_record_order(self) -> None:
        assert step_options(_RECORDS, _STEPS, [None, None, None], 0) == [
            "战机",
            "护卫舰",
            "登陆舰",
            "未分类",
        ]

    def test_second_step_filters_by_parent_selection(self) -> None:
        assert step_options(_RECORDS, _STEPS, ["战机", None, None], 1) == ["A"]

    def test_list_value_matches_each_of_its_categories(self) -> None:
        assert step_options(_RECORDS, _STEPS, ["护卫舰", None, None], 1) == ["B"]
        assert step_options(_RECORDS, _STEPS, ["登陆舰", None, None], 1) == ["B"]

    def test_third_step_filters_by_ship(self) -> None:
        assert step_options(_RECORDS, _STEPS, ["战机", "A", None], 2) == [
            "A · 炮1",
            "A · 炮2",
        ]

    def test_none_selection_does_not_filter(self) -> None:
        assert step_options(_RECORDS, _STEPS, [None, None, None], 1) == ["A", "B", "C"]

    def test_unknown_field_returns_empty(self) -> None:
        steps = [{"field": "不存在", "label": "X"}]
        assert step_options(_RECORDS, steps, [None], 0) == []


class TestMatchingRecords:
    def test_filters_all_steps(self) -> None:
        matched = matching_records(_RECORDS, _STEPS, ["战机", "A", "A · 炮2"])
        assert [record["名称"] for record in matched] == ["A · 炮2"]

    def test_none_steps_return_all_records(self) -> None:
        assert matching_records(_RECORDS, _STEPS, [None, None, None]) == _RECORDS


class TestOptionDisplays:
    def test_display_field_maps_value_to_label(self) -> None:
        displays = option_displays(_RECORDS, _STEPS, ["战机", "A", None], 2)
        assert displays == {"A · 炮1": "炮1", "A · 炮2": "炮2"}

    def test_missing_display_field_falls_back_to_value(self) -> None:
        displays = option_displays(_RECORDS, _STEPS, ["战机", None, None], 1)
        assert displays == {"A": "A"}
