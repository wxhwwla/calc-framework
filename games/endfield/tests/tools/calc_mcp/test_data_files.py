# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""data_files 归一化、校验与告警测试。"""

from __future__ import annotations

import json

import pytest
from tools.generator.data_files import (
    DATA_FILE_BY_SOURCE,
    MAX_DATA_FILE_BYTES,
    DataFileError,
    binding_warnings,
    bound_entity_sources,
    normalize_data_files,
    serialize_data_file,
)
from tools.generator.selectors import SelectorError, normalize_entity_selectors

_SELECTOR_RECORDS = {
    "weapon": [
        {
            "名称": "速射炮",
            "舰船分类": ["护卫舰", "驱逐舰"],
            "舰船": "测试舰",
            "武器标签": "速射炮·短",
        }
    ]
}


def test_none_returns_empty() -> None:
    assert normalize_data_files(None) == ({}, [])


def test_accepts_valid_records() -> None:
    normalized, warnings = normalize_data_files({"enemy": [{"名称": "Boss", "def": 100}]})
    assert normalized == {"enemy": [{"名称": "Boss", "def": 100}]}
    assert warnings == []


@pytest.mark.parametrize("source", ["user_input", "computed", "characters", "enemies"])
def test_rejects_unknown_source(source: str) -> None:
    with pytest.raises(DataFileError, match="来源"):
        normalize_data_files({source: []})


def test_rejects_non_list() -> None:
    with pytest.raises(DataFileError, match="列表"):
        normalize_data_files({"enemy": {"名称": "x"}})


def test_rejects_non_dict_record() -> None:
    with pytest.raises(DataFileError, match="对象"):
        normalize_data_files({"enemy": ["Boss"]})


@pytest.mark.parametrize("name", [None, "", "   ", 1])
def test_rejects_missing_or_blank_name(name: object) -> None:
    record = {"def": 1} if name is None else {"名称": name, "def": 1}
    with pytest.raises(DataFileError, match="名称"):
        normalize_data_files({"enemy": [record]})


def test_rejects_duplicate_names() -> None:
    with pytest.raises(DataFileError, match="重复"):
        normalize_data_files({"enemy": [{"名称": "Boss"}, {"名称": "Boss"}]})


def test_rejects_non_serializable_record() -> None:
    with pytest.raises(DataFileError, match="JSON"):
        normalize_data_files({"enemy": [{"名称": "Boss", "bad": object()}]})


def test_rejects_oversized_file_by_utf8_bytes() -> None:
    oversized = "字" * (MAX_DATA_FILE_BYTES // 3 + 1000)
    with pytest.raises(DataFileError, match="过大"):
        normalize_data_files({"enemy": [{"名称": "Boss", "desc": oversized}]})


def test_empty_records_warn() -> None:
    normalized, warnings = normalize_data_files({"enemy": []})
    assert normalized == {"enemy": []}
    assert len(warnings) == 1


def test_serialize_keeps_chinese_and_indent() -> None:
    text = serialize_data_file([{"名称": "Boss", "def": 10}])

    assert "名称" in text
    assert "\n  " in text
    assert json.loads(text) == [{"名称": "Boss", "def": 10}]


def test_data_file_mapping() -> None:
    assert DATA_FILE_BY_SOURCE == {
        "character": "data/characters.json",
        "weapon": "data/weapons.json",
        "equipment": "data/equipments.json",
        "enemy": "data/enemies.json",
    }


def test_binding_warnings_unbound_and_bound() -> None:
    warnings = binding_warnings(["user_input", "enemy", "weapon"], {"weapon": [{"名称": "剑"}]})
    joined = "\n".join(warnings)

    assert "enemy" in joined
    assert "user_input" in joined
    assert "weapon" in joined


def test_binding_warnings_unused_file() -> None:
    warnings = binding_warnings(["user_input"], {"enemy": [{"名称": "Boss"}]})

    assert any("没有对应" in warning for warning in warnings)


def test_bound_entity_sources_excludes_empty_files() -> None:
    assert bound_entity_sources({"enemy": [], "weapon": [{"名称": "剑"}]}) == {"weapon"}


def test_binding_warnings_empty_file_is_unbound() -> None:
    warnings = binding_warnings(["enemy"], {"enemy": []})
    joined = "\n".join(warnings)

    assert "为空" in joined
    assert "未绑定" in joined
    assert "已绑定" not in joined


def test_entity_selectors_none_returns_empty() -> None:
    assert normalize_entity_selectors(None, {}) == []


def test_entity_selectors_normalized() -> None:
    raw = [
        {
            "source": "weapon",
            "data_file": "data/weapons.json",
            "steps": [
                {"field": "舰船分类", "label": "舰船种类"},
                {"field": "舰船"},
                {"field": "名称", "label": "武器", "display_field": "武器标签"},
            ],
        }
    ]

    assert normalize_entity_selectors(raw, _SELECTOR_RECORDS) == [
        {
            "source": "weapon",
            "data_file": "weapons",
            "steps": [
                {"field": "舰船分类", "label": "舰船种类"},
                {"field": "舰船"},
                {"field": "名称", "label": "武器", "display_field": "武器标签"},
            ],
        }
    ]


def test_entity_selectors_default_data_file() -> None:
    raw = [{"source": "weapon", "steps": [{"field": "名称"}]}]

    assert normalize_entity_selectors(raw, _SELECTOR_RECORDS)[0]["data_file"] == "weapons"


@pytest.mark.parametrize(
    ("raw", "match"),
    [
        ("weapon", "数组"),
        ([{"source": "magic", "steps": [{"field": "名称"}]}], "source"),
        ([{"source": "weapon", "steps": []}], "steps"),
        (
            [
                {"source": "weapon", "steps": [{"field": "名称"}]},
                {"source": "weapon", "steps": [{"field": "名称"}]},
            ],
            "重复",
        ),
        ([{"source": "weapon", "steps": [{"field": "舰船"}]}], "最后一级"),
        ([{"source": "weapon", "steps": [{"field": "不存在"}, {"field": "名称"}]}], "不存在"),
        ([{"source": "weapon", "steps": [{"field": "名称", "display_field": "不存在"}]}], "不存在"),
        ([{"source": "weapon", "data_file": "characters", "steps": [{"field": "名称"}]}], "data_file"),
        ([{"source": "weapon", "steps": [{"field": "名称", "bad": 1}]}], "未知字段"),
    ],
)
def test_entity_selectors_invalid_rejected(raw: object, match: str) -> None:
    with pytest.raises(SelectorError, match=match):
        normalize_entity_selectors(raw, _SELECTOR_RECORDS)


def test_entity_selectors_require_bound_data() -> None:
    raw = [{"source": "weapon", "steps": [{"field": "名称"}]}]

    with pytest.raises(SelectorError, match="data_files"):
        normalize_entity_selectors(raw, {"weapon": []})
