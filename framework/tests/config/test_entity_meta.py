# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""``meta.entity_detail`` / ``meta.entity_input_rules`` 归一化测试。"""

from __future__ import annotations

import pytest

from calc_framework.config.entity_meta import (
    EntityMetaError,
    format_detail_value,
    normalize_entity_detail,
    normalize_entity_input_rules,
    rule_matches,
)

_RECORDS = {
    "weapon": [
        {
            "名称": "A · 炮",
            "舰船": "A",
            "舰船分类": ["战机"],
            "is_energy": 0.0,
            "needs_mothership": 0.0,
            "base_damage": 25.0,
        },
        {
            "名称": "B · 炮",
            "舰船": "B",
            "舰船分类": ["护卫舰"],
            "is_energy": 1.0,
            "needs_mothership": 1.0,
            "base_damage": 100.0,
        },
    ]
}

_USER_INPUTS = {
    "user_input.mothership_flight_bonus",
    "user_input.physical_armor",
    "user_input.energy_armor",
}


class TestEntityDetail:
    def test_normalizes_sections_and_fields(self) -> None:
        detail = normalize_entity_detail(
            {
                "source": "weapon",
                "title": "武器数据",
                "sections": [
                    {
                        "title": "基础",
                        "columns": 2,
                        "fields": [
                            {"field": "舰船", "label": "舰船"},
                            {"field": "base_damage", "label": "单发", "format": ".1f"},
                        ],
                    }
                ],
            },
            _RECORDS,
        )

        assert detail == {
            "source": "weapon",
            "title": "武器数据",
            "sections": [
                {
                    "title": "基础",
                    "columns": 2,
                    "fields": [
                        {"field": "舰船", "label": "舰船"},
                        {"field": "base_damage", "label": "单发", "format": ".1f"},
                    ],
                }
            ],
        }

    def test_missing_raw_returns_none(self) -> None:
        assert normalize_entity_detail(None, _RECORDS) is None

    def test_defaults_title_label_and_columns(self) -> None:
        detail = normalize_entity_detail(
            {"source": "weapon", "sections": [{"fields": [{"field": "舰船"}]}]},
            _RECORDS,
        )

        assert detail["title"] == "实体数据"
        section = detail["sections"][0]
        assert section["title"] == "基础"
        assert section["columns"] == 1
        assert section["fields"] == [{"field": "舰船", "label": "舰船"}]

    @pytest.mark.parametrize(
        "raw",
        [
            [],
            {"source": "unknown", "sections": [{"fields": [{"field": "舰船"}]}]},
            {"source": "weapon", "sections": []},
            {"source": "weapon", "sections": [{"fields": []}]},
            {"source": "weapon", "sections": [{"fields": [{"field": "不存在"}]}]},
            {"source": "weapon", "sections": [{"fields": [{"field": "舰船"}], "columns": 0}]},
            {"source": "weapon", "sections": [{"fields": [{"field": "舰船"}], "extra": 1}]},
            {"source": "weapon", "sections": [{"fields": [{"field": "舰船", "extra": 1}]}]},
            {"source": "weapon", "sections": [{"fields": [{"field": "舰船"}], "title": ""}]},
            {"source": "weapon", "sections": [{"fields": [{"field": "舰船"}], "columns": "2"}]},
            {"source": "weapon", "sections": [{"fields": [{"field": "舰船"}]}], "extra": 1},
        ],
    )
    def test_rejects_invalid_detail(self, raw: object) -> None:
        with pytest.raises(EntityMetaError):
            normalize_entity_detail(raw, _RECORDS)


class TestEntityInputRules:
    def test_normalizes_rules(self) -> None:
        rules = normalize_entity_input_rules(
            [
                {
                    "source": "weapon",
                    "field": "needs_mothership",
                    "equals": 0,
                    "disable": ["user_input.mothership_flight_bonus"],
                    "reason": "不需要母舰",
                }
            ],
            data_files=_RECORDS,
            user_input_paths=_USER_INPUTS,
        )

        assert rules == [
            {
                "source": "weapon",
                "field": "needs_mothership",
                "equals": 0.0,
                "disable": ["user_input.mothership_flight_bonus"],
                "reason": "不需要母舰",
            }
        ]

    def test_numeric_equals_is_normalized_to_float(self) -> None:
        rules = normalize_entity_input_rules(
            [{"source": "weapon", "field": "is_energy", "equals": True, "disable": ["user_input.physical_armor"]}],
            data_files=_RECORDS,
            user_input_paths=_USER_INPUTS,
        )

        assert rules[0]["equals"] is True

    @pytest.mark.parametrize(
        "raw",
        [
            [{}],
            [{"source": "weapon", "field": "needs_mothership", "disable": ["user_input.physical_armor"]}],
            [{"source": "weapon", "field": "needs_mothership", "equals": None, "disable": ["user_input.physical_armor"]}],
            [{"source": "weapon", "field": "needs_mothership", "equals": 0, "disable": []}],
            [{"source": "weapon", "field": "needs_mothership", "equals": 0, "disable": ["weapon.base_damage"]}],
            [{"source": "weapon", "field": "needs_mothership", "equals": 0, "disable": ["user_input.unknown"]}],
            [{"source": "unknown", "field": "needs_mothership", "equals": 0, "disable": ["user_input.physical_armor"]}],
            [{"source": "weapon", "field": "不存在", "equals": 0, "disable": ["user_input.physical_armor"]}],
            [
                {
                    "source": "weapon",
                    "field": "needs_mothership",
                    "equals": 0,
                    "disable": ["user_input.physical_armor"],
                    "extra": 1,
                }
            ],
            [
                {
                    "source": "weapon",
                    "field": "needs_mothership",
                    "equals": 0,
                    "disable": ["user_input.physical_armor"],
                    "reason": 1,
                }
            ],
        ],
    )
    def test_rejects_invalid_rules(self, raw: object) -> None:
        with pytest.raises(EntityMetaError):
            normalize_entity_input_rules(raw, data_files=_RECORDS, user_input_paths=_USER_INPUTS)

    def test_rules_missing_field_do_not_match(self) -> None:
        rule = {"source": "weapon", "field": "needs_mothership", "equals": 0.0, "disable": ["x"]}

        assert rule_matches(rule, {"名称": "无字段"}) is False

    def test_rule_matches_numbers_and_lists(self) -> None:
        rule = {"source": "weapon", "field": "is_energy", "equals": 1.0, "disable": ["x"]}

        assert rule_matches(rule, {"is_energy": 1}) is True
        assert rule_matches(rule, {"is_energy": 0}) is False
        assert rule_matches({"field": "舰船分类", "equals": "战机"}, {"舰船分类": ["战机"]}) is True


class TestFormatDetailValue:
    def test_formats_scalars_and_lists(self) -> None:
        assert format_detail_value(None) == "—"
        assert format_detail_value("") == "—"
        assert format_detail_value(12.0) == "12"
        assert format_detail_value(12.5) == "12.5"
        assert format_detail_value(12.345) == "12.35"
        assert format_detail_value(12.345, ".1f") == "12.3"
        assert format_detail_value(True) == "是"
        assert format_detail_value(["战机", "护航艇"]) == "战机、护航艇"
