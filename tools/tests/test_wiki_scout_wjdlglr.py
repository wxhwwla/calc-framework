# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""无尽的拉格朗日 Wiki provider — EnhTreeData / 舰船页离线解析测试。

关键口径（已用 AT021 / 维塔斯 / BR050 页面交叉验证）：
- `fa` = 去程时间（出击飞行），`fb` = 回程时间（返航飞行）。
- 攻击次数 = `at`（工作次数）× `rep`（弹药数）。
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
from tools.wiki_scout.providers.wjdlglr import (
    _REFERER,
    WjdlglrProvider,
    extract_enh_data,
    parse_ship_page,
)

_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "wiki_scout"


class _StubFetcher:
    def get_json(self, url: str, **kwargs: object) -> Any:
        del kwargs
        if "categorymembers" in url:
            return {"query": {"categorymembers": [{"title": "A"}, {"title": "B"}]}}
        if "action=parse" in url:
            if "page=A" in url:
                raise FetchError("parse failed")
            return {"parse": {"wikitext": "{{新舰船/基础数据|类型=护卫舰}}"}}
        raise AssertionError(url)

    def get_text(self, url: str, **kwargs: object) -> str:
        del kwargs
        if "EnhTreeData" in url:
            return (
                'Object.assign(window.__ETW_DATA,{"1":{"ship":{"name":"B","base":{"hp":1}},"systems":[],"weps":{}}});'
            )
        raise FetchError("raw failed")


def _text(name: str) -> str:
    return (_FIXTURES / name).read_text(encoding="utf-8")


def _raw_bundle() -> dict[str, Any]:
    return {
        "pages": [
            {"title": "AT021-脉冲攻击机", "wikitext": _text("wjdlglr_ship_page.wikitext")},
            {"title": "枪骑兵级-驱逐舰", "wikitext": _text("wjdlglr_second_page.wikitext")},
        ],
        "chunks": [{"title": "MediaWiki:EnhTreeData1.js", "text": _text("enh_tree_sample.js")}],
    }


def test_referer_is_ascii_for_http_headers() -> None:
    assert _REFERER.isascii()
    assert "%E8%88%B0%E8%88%B9" in _REFERER


def test_page_without_data_ship_falls_back_to_exact_title() -> None:
    raw = {
        "pages": [
            {
                "title": "测试舰",
                "wikitext": "{{新舰船/基础数据|类型=护卫舰|指挥值=5}}",
            }
        ],
        "chunks": [
            {
                "text": (
                    'Object.assign(window.__ETW_DATA,{"999":{"ship":'
                    '{"name":"测试舰","base":{"hp":100}},"systems":[],"weps":{}}});'
                )
            }
        ],
    }
    ship = WjdlglrProvider().parse(raw)["舰船"][0]

    assert ship["类型"] == "护卫舰"
    assert ship["指挥值"] == 5
    assert ship["血量"] == 100


def test_fetch_skips_failed_pages_and_reports_them() -> None:
    raw = WjdlglrProvider().fetch(_StubFetcher(), refresh=False)  # type: ignore[arg-type]

    assert [page["title"] for page in raw["pages"]] == ["B"]
    assert raw["errors"] == {"A": "raw failed"}

    parsed = WjdlglrProvider().parse(raw)
    assert parsed["抓取失败"] == {"A": "raw failed"}
    assert parsed["舰船"][0]["类型"] == "护卫舰"


def test_utility_weapon_has_no_attack_count_and_is_friendly() -> None:
    raw = {
        "pages": [],
        "chunks": [
            {
                "text": (
                    'Object.assign(window.__ETW_DATA,{"777":{"ship":'
                    '{"name":"维修舰","base":{"hp":10}},"systems":[],'
                    '"weps":{"1":{"mod":"维修无人机","typ":7,"act":4}}}});'
                )
            }
        ],
    }
    weapon = WjdlglrProvider().parse(raw)["舰船"][0]["武器"][0]

    assert weapon["武器类型"] == "子系统平台"
    assert weapon["武器作用"] == "维修"
    assert weapon["友方作用"] is True
    assert weapon["攻击次数"] is None
    assert weapon["单发伤害"] is None


def test_attack_weapon_is_not_friendly() -> None:
    out = WjdlglrProvider().parse(_raw_bundle())
    at021 = next(ship for ship in out["舰船"] if ship["id"] == "12501")

    assert at021["武器"][0]["友方作用"] is False


def test_aircraft_requires_mothership_but_is_not_mothership() -> None:
    out = WjdlglrProvider().parse(_raw_bundle())
    ships = {ship["id"]: ship for ship in out["舰船"]}

    assert ships["12501"]["是否母舰"] is False
    assert ships["12501"]["需要母舰"] is True
    assert ships["40801"]["是否母舰"] is False
    assert ships["40801"]["需要母舰"] is False


def test_ship_with_docks_is_mothership() -> None:
    raw = {
        "pages": [{"title": "航母", "wikitext": "{{新舰船/基础数据|类型=航空母舰}}"}],
        "chunks": [
            {
                "text": (
                    'Object.assign(window.__ETW_DATA,{"601":{"ship":'
                    '{"name":"航母","base":{"hp":10}},"systems":[],"weps":{},'
                    '"docks":{"1":{"name":"战机"}}}});'
                )
            }
        ],
    }
    ship = WjdlglrProvider().parse(raw)["舰船"][0]

    assert ship["是否母舰"] is True
    assert ship["需要母舰"] is False


def test_te_ship_without_page_type_uses_name_to_detect_mothership_need() -> None:
    raw = {
        "pages": [],
        "chunks": [
            {
                "text": (
                    "Object.assign(window.__ETW_DATA,{"
                    '"1":{"ship":{"name":"理智A101-TE-战斗攻击机","base":{},"systems":[],"weps":{},"docks":{}}},'
                    '"2":{"ship":{"name":"野火-TE-鱼雷艇","base":{},"systems":[],"weps":{},"docks":{}}},'
                    '"3":{"ship":{"name":"V055火炮-TE","base":{},"systems":[],"weps":{},"docks":{}}}'
                    "});"
                )
            }
        ],
    }
    ships = {ship["名称"]: ship for ship in WjdlglrProvider().parse(raw)["舰船"]}

    assert ships["理智A101-TE-战斗攻击机"]["需要母舰"] is True
    assert ships["野火-TE-鱼雷艇"]["需要母舰"] is True
    assert ships["V055火炮-TE"]["需要母舰"] is False


def test_parse_ship_page_strips_html_comments() -> None:
    meta = parse_ship_page("{{新舰船/基础数据|类型=驱逐舰,英雄舰 <!--工程舰/护卫舰-->|指挥值=8}}")

    assert meta["类型"] == "驱逐舰,英雄舰"
    assert meta["指挥值"] == "8"


def test_extract_enh_data_reads_assignment_block() -> None:
    ships = extract_enh_data(_text("enh_tree_sample.js"))

    assert set(ships) == {"12501", "40801"}
    assert ships["12501"]["ship"]["name"] == "AT021-脉冲攻击机"


def test_ship_stats_and_metadata_are_joined_by_data_ship_id() -> None:
    out = WjdlglrProvider().parse(_raw_bundle())
    ships = {ship["id"]: ship for ship in out["舰船"]}

    at021 = ships["12501"]
    assert at021["名称"] == "AT021-脉冲攻击机"
    assert at021["类型"] == "战机"
    assert at021["稀有度"] == "2星"
    assert at021["所属"] == "未央公约组织"
    assert at021["武器类型"] == "脉冲"
    assert at021["舰船站位"] == "后排"
    assert at021["指挥值"] == 8
    assert at021["血量"] == 4920
    assert at021["物理护甲"] == 2
    assert at021["能量护甲"] == 0
    assert at021["护盾值"] == 0

    lancer = ships["40801"]
    assert lancer["血量"] == 22710
    assert lancer["物理护甲"] == 20
    assert lancer["能量护甲"] == 2


def test_weapon_fields_include_hit_table_and_travel_times() -> None:
    out = WjdlglrProvider().parse(_raw_bundle())
    at021 = next(ship for ship in out["舰船"] if ship["id"] == "12501")
    weapon = at021["武器"][0]

    assert weapon["名称"] == "SP-190D型大口径脉冲机炮"
    assert weapon["系统"] == "脉冲机炮系统"
    assert weapon["武器类型"] == "脉冲炮"
    assert weapon["武器作用"] == "能量攻击"
    assert weapon["单发伤害"] == 190.0
    assert weapon["攻击次数"] == 2
    assert weapon["工作次数"] == 1
    assert weapon["弹药数"] == 2
    assert weapon["冷却(毫秒)"] == 6000
    assert weapon["持续时间(毫秒)"] == 35000
    assert weapon["锁定时间(毫秒)"] == 10000
    assert weapon["攻击间隔(毫秒)"] == 18000
    assert weapon["去程时间(毫秒)"] == 8000
    assert weapon["回程时间(毫秒)"] == 4000
    assert weapon["命中率"][0] == {"优先级": 3, "目标": "战机", "命中率": 22}


def test_weapon_affix_parses_crit_stats() -> None:
    out = WjdlglrProvider().parse(_raw_bundle())
    at021 = next(ship for ship in out["舰船"] if ship["id"] == "12501")
    weapon = at021["武器"][0]

    assert weapon["暴击率"] == 15.0
    assert weapon["暴击伤害"] == 170.0
    assert weapon["暴击目标"] == "舰船"
    assert weapon["防空暴击"] is False


def test_weapon_without_crit_affix_has_empty_crit_stats() -> None:
    out = WjdlglrProvider().parse(_raw_bundle())
    lancer = next(ship for ship in out["舰船"] if ship["id"] == "40801")
    weapon = lancer["武器"][0]

    assert weapon["暴击率"] is None
    assert weapon["暴击伤害"] is None
    assert weapon["暴击目标"] == ""
    assert weapon["防空暴击"] is None


def test_anti_air_crit_affix_targets_aircraft() -> None:
    raw = {
        "pages": [],
        "chunks": [
            {
                "text": (
                    "Object.assign(window.__ETW_DATA,{"
                    '"888":{"ship":{"name":"防空舰","base":{},"systems":[]},'
                    '"weps":{"88801":{"mod":"防空炮","typ":1,"act":2}},'
                    '"affix":{"88801":[{"n":"防空暴击","d":"有25%概率对舰载机目标额外造成100%暴击伤害"}]}}}'
                    "});"
                )
            }
        ],
    }
    weapon = WjdlglrProvider().parse(raw)["舰船"][0]["武器"][0]

    assert weapon["暴击率"] == 25.0
    assert weapon["暴击伤害"] == 100.0
    assert weapon["暴击目标"] == "舰载机"
    assert weapon["防空暴击"] is True


def test_non_aircraft_weapon_has_no_travel_times() -> None:
    out = WjdlglrProvider().parse(_raw_bundle())
    lancer = next(ship for ship in out["舰船"] if ship["id"] == "40801")
    weapon = lancer["武器"][0]

    assert weapon["攻击次数"] == 4
    assert weapon["去程时间(毫秒)"] is None
    assert weapon["回程时间(毫秒)"] is None


def test_output_reports_enhtree_data_version() -> None:
    out = WjdlglrProvider().parse(_raw_bundle())

    assert out["游戏"] == "无尽的拉格朗日"
    assert out["数据版本"] == "34101"


def test_parse_is_json_serializable() -> None:
    out = WjdlglrProvider().parse(_raw_bundle())

    assert json.loads(json.dumps(out, ensure_ascii=False))["舰船"][0]["id"]
