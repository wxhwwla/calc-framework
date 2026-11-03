# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""华法琳 Wiki（终末地）provider — 离线解析测试。

夹具取自真实 API 响应（已裁剪），断言值与 games/endfield/data 中
陈千语（90 级）及武器「工业零点一」一致。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from tools.wiki_scout.fetcher import FetchError
from tools.wiki_scout.providers.warfarin import WarfarinProvider, _as_list

_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "wiki_scout"


class _StubFetcher:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def get_json(self, url: str, **kwargs: object) -> Any:
        del kwargs
        self.calls.append(url)
        if url.endswith("/operators"):
            return {
                "data": [
                    {"slug": "ok", "name": "OK"},
                    {"slug": "bad", "name": "BAD"},
                ]
            }
        if url.endswith("/weapons"):
            return {"data": [{"slug": "w", "name": "W"}]}
        if url.endswith("/gear"):
            return {"data": []}
        if url.endswith("/operators/bad"):
            raise FetchError("boom")
        return {"data": {"characterTable": {}}}


def _load(name: str) -> Any:
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


def _raw_bundle() -> dict[str, Any]:
    lists = _load("warfarin_lists.json")
    chen = next(o for o in lists["operators"] if o["name"] == "陈千语")
    claym = next(w for w in lists["weapons"] if w["name"] == "工业零点一")
    return {
        "operators": [chen],
        "operator_details": {"chen-qianyu": _load("warfarin_operator_chen.json")},
        "weapons": [claym],
        "weapon_details": {"industry-01": _load("warfarin_weapon_claym.json")},
        "gear": lists["gear"],
    }


def test_fetch_records_per_item_errors_and_continues() -> None:
    raw = WarfarinProvider().fetch(_StubFetcher(), refresh=False)  # type: ignore[arg-type]

    assert set(raw["operator_details"]) == {"ok"}
    assert set(raw["weapon_details"]) == {"w"}
    assert raw["errors"] == {"operators/bad": "boom"}

    parsed = WarfarinProvider().parse(raw)
    assert parsed["抓取失败"] == {"operators/bad": "boom"}


def test_as_list_unwraps_api_envelope() -> None:
    payload = {
        "meta": {"lang": "cn", "type": "operator", "version": "1.6", "count": 1},
        "data": [{"name": "陈千语"}],
        "refs": {},
    }

    assert _as_list(payload) == [{"name": "陈千语"}]
    assert _as_list([{"name": "陈千语"}]) == [{"name": "陈千语"}]


def test_parse_keeps_entries_with_empty_details() -> None:
    out = WarfarinProvider().parse(
        {
            "operators": [{"slug": "x", "name": "X"}],
            "operator_details": {"x": {}},
            "weapons": [{"slug": "w", "name": "W"}],
            "weapon_details": {"w": {}},
            "gear": [{}],
        }
    )

    assert out["干员"][0]["名称"] == "X"
    assert out["武器"][0]["名称"] == "W"
    assert out["装备"][0]["名称"] is None


def test_operator_basic_fields() -> None:
    out = WarfarinProvider().parse(_raw_bundle())
    op = out["干员"][0]

    assert op["名称"] == "陈千语"
    assert op["星级"] == 5
    assert op["类型"] == "近卫"
    assert op["武器类型"] == "单手剑"
    assert op["主能力"] == "敏捷"
    assert op["副能力"] == "力量"
    assert op["等级"] == list(range(1, 91))


def test_operator_level_curves_match_local_data() -> None:
    out = WarfarinProvider().parse(_raw_bundle())
    op = out["干员"][0]

    for key in ("力量", "敏捷", "智识", "意志", "基础攻击力", "基础防御力"):
        assert len(op[key]) == 90

    assert op["力量"][0] == 10
    assert op["敏捷"][0] == 20
    assert op["智识"][0] == 8
    assert op["意志"][0] == 9
    assert op["基础攻击力"][0] == 30
    assert op["基础防御力"][0] == 0

    assert op["力量"][89] == 106
    assert op["敏捷"][89] == 171
    assert op["智识"][89] == 85
    assert op["意志"][89] == 93
    assert op["基础攻击力"][89] == 297


def test_operator_skill_multiplier_curves() -> None:
    out = WarfarinProvider().parse(_raw_bundle())
    op = out["干员"][0]

    assert len(op["战技倍率"]) == 1
    assert op["战技倍率"][0][0] == 169.0
    assert op["战技倍率"][0][-1] == 380.0

    assert op["连携技倍率"][0][0] == 120.0
    assert op["连携技倍率"][0][-1] == 270.0

    assert len(op["终结技倍率"]) == 2
    assert op["终结技倍率"][0][0] == 36.0
    assert op["终结技倍率"][0][-1] == 81.0
    assert op["终结技倍率"][1][0] == 455.0
    assert op["终结技倍率"][1][-1] == 1023.0

    assert op["战技段伤害类型"] == ["物理"]
    assert op["连携技段伤害类型"] == ["物理"]
    assert op["终结技段伤害类型"] == ["物理", "物理"]


def test_weapon_base_curve_and_skills() -> None:
    out = WarfarinProvider().parse(_raw_bundle())
    weapon = out["武器"][0]

    assert weapon["名称"] == "工业零点一"
    assert weapon["武器类型"] == "双手剑"
    assert weapon["最大等级"] == 90
    assert len(weapon["基础攻击力曲线"]) == 90
    assert weapon["基础攻击力曲线"][0] == 34
    assert weapon["基础攻击力曲线"][-1] == 341

    assert [s["名称"] for s in weapon["普通技能"]] == ["力量提升·小", "攻击提升·小"]
    assert [s["名称"] for s in weapon["特殊技能"]] == ["压制·应急强化"]
    assert len(weapon["普通技能"][0]["成长"]) == 9


def test_gear_is_read_from_list_payload() -> None:
    out = WarfarinProvider().parse(_raw_bundle())
    gear = out["装备"][0]

    assert gear["名称"] == "简易护甲"
    assert gear["部位"] == "护甲"
    assert gear["稀有度"] == 1
    assert gear["最低穿戴等级"] == 10
    assert {m["属性类型"] for m in gear["属性词条"]} == {"力量", "敏捷", "生命值"}
