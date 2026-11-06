# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""无尽的拉格朗日 Wiki（wiki.biligame.com/wjdlglr）provider。

数据来源：
- `Category:舰船` 页面 wikitext：稀有度、类型、所属、站位、指挥值。
- `MediaWiki:EnhTreeData1.js` … `EnhTreeData8.js`：官方全量配置，
  通过 `window.__ETW_DATA` 提供舰船基础属性与武器数据。

武器字段口径（已用 AT021 / 维塔斯 / BR050 页面交叉验证）：
- `fa` = 去程时间（出击飞行），`fb` = 回程时间（返航飞行）。
- 攻击次数 = `at`（工作次数）× `rep`（弹药数）。
- `cd` 冷却、`dur` 持续时间、`lock` 锁定时间、`iv` 攻击间隔，单位均为毫秒。
- 舰船 `docks` 非空 → `是否母舰`；类型为战机/护航艇/无人机 → `需要母舰`
  （无页面类型的 TE 舰船按名称关键词兜底）。
- 武器作用为维修/驻防/增益（`act` 4/5/6）→ `友方作用=True`，命中率按 100% 处理。
"""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import quote

from ..fetcher import Fetcher, FetchError
from ..registry import register_provider
from .base import BaseProvider

_WIKI = "https://wiki.biligame.com/wjdlglr"
_API = f"{_WIKI}/api.php"
# HTTP 头只能是 latin-1，中文路径必须百分号编码。
_REFERER = f"{_WIKI}/{quote('舰船图鉴', safe='')}"
_CATEGORY = "舰船"
_CHUNK_COUNT = 8

_WEAPON_TYPES = {
    1: "火炮",
    2: "轨道炮",
    3: "离子炮",
    4: "脉冲炮",
    5: "导弹",
    6: "鱼雷",
    7: "子系统平台",
    8: "舰载机",
}

_WEAPON_ACTIONS = {
    1: "能量攻击",
    2: "直射攻击",
    3: "干扰",
    4: "维修",
    5: "驻防",
    6: "增益",
    7: "减益",
    8: "无动作",
    9: "操作",
}

# 维修/驻防/增益作用于友方，命中率按 100% 处理。
_FRIENDLY_ACTIONS = frozenset({4, 5, 6})
# 页面类型缺失的 TE 舰船用名称兜底判断是否需要母舰。
_AIRCRAFT_NAME_KEYWORDS = (
    "战机",
    "战斗机",
    "攻击机",
    "轰炸机",
    "侦察机",
    "拦截机",
    "护航艇",
    "鱼雷艇",
    "导弹艇",
    "炮艇",
    "无人机",
)

# 舰船 affix 中的暴击词条，例如「有20%概率对目标额外造成150%暴击伤害」。
_CRIT_PATTERN = re.compile(r"有\s*(\d+(?:\.\d+)?)\s*%\s*概率对(.+?)额外造成\s*(\d+(?:\.\d+)?)\s*%\s*暴击伤害")


@register_provider
class WjdlglrProvider(BaseProvider):
    """无尽的拉格朗日 Wiki 数据源。"""

    name = "wjdlglr"
    description = "无尽的拉格朗日 Wiki — 舰船/武器/命中率/去回程时间"

    def fetch(
        self,
        fetcher: Fetcher,
        *,
        limit: int | None = None,
        refresh: bool = False,
    ) -> dict[str, Any]:
        members = self._fetch_category(fetcher, refresh)
        pages: list[dict[str, str]] = []
        errors: dict[str, str] = {}
        for member in members[:limit]:
            title = member.get("title")
            if not title:
                continue
            try:
                wikitext = self._fetch_wikitext(fetcher, title, refresh)
            except FetchError as exc:
                errors[title] = str(exc)
                continue
            pages.append({"title": title, "wikitext": wikitext})

        chunks: list[dict[str, str]] = []
        for index in range(1, _CHUNK_COUNT + 1):
            title = f"MediaWiki:EnhTreeData{index}.js"
            chunks.append({"title": title, "text": self._fetch_raw(fetcher, title, refresh)})

        return {"pages": pages, "chunks": chunks, "errors": errors}

    def parse(self, raw: dict[str, Any]) -> dict[str, Any]:
        ships_by_id: dict[str, Any] = {}
        version = ""
        for chunk in raw.get("chunks", []):
            text = chunk.get("text", "")
            version = _newer_version(version, _parse_version(text))
            ships_by_id.update(extract_enh_data(text))

        names_by_id: dict[str, str] = {}
        for ship_id, ship in ships_by_id.items():
            name = str((ship.get("ship") or {}).get("name") or "").strip()
            if name:
                names_by_id.setdefault(name, ship_id)

        pages_by_ship: dict[str, tuple[str, dict[str, str]]] = {}
        unmatched: list[str] = []
        for page in raw.get("pages", []):
            title = page.get("title", "")
            meta = parse_ship_page(page.get("wikitext", ""))
            ship_id = meta.get("data-ship")
            if ship_id not in ships_by_id:
                # 少数页面没有 enh-tree 组件，退化为「标题 == 配置名称」精确匹配。
                ship_id = names_by_id.get(title)
            if ship_id is not None and ship_id in ships_by_id:
                pages_by_ship.setdefault(ship_id, (title, meta))
            else:
                unmatched.append(title)

        ships = [
            _build_ship(ship_id, ship, *pages_by_ship.get(ship_id, ("", {}))) for ship_id, ship in ships_by_id.items()
        ]
        ships.sort(key=_ship_sort_key)

        result: dict[str, Any] = {
            "游戏": "无尽的拉格朗日",
            "来源": _WIKI,
            "数据版本": version,
            "舰船": ships,
            "未匹配页面": unmatched,
        }
        if raw.get("errors"):
            result["抓取失败"] = raw["errors"]
        return result

    def _fetch_category(self, fetcher: Fetcher, refresh: bool) -> list[dict[str, Any]]:
        members: list[dict[str, Any]] = []
        continue_token: str | None = None
        while True:
            url = (
                f"{_API}?action=query&list=categorymembers"
                f"&cmtitle=Category:{quote(_CATEGORY, safe='')}"
                "&cmnamespace=0&cmlimit=500&format=json"
            )
            if continue_token:
                url += f"&cmcontinue={quote(continue_token, safe='')}"
            payload = fetcher.get_json(url, refresh=refresh, referer=_REFERER)
            members.extend(payload.get("query", {}).get("categorymembers", []))
            continue_token = (payload.get("continue") or {}).get("cmcontinue")
            if not continue_token:
                return members

    def _fetch_wikitext(self, fetcher: Fetcher, title: str, refresh: bool) -> str:
        url = f"{_API}?action=parse&page={quote(title, safe='')}&prop=wikitext&formatversion=2&format=json"
        try:
            payload = fetcher.get_json(url, refresh=refresh, referer=_REFERER)
            wikitext = (payload.get("parse") or {}).get("wikitext")
            if wikitext:
                return wikitext
        except (FetchError, json.JSONDecodeError):
            pass
        return self._fetch_raw(fetcher, title, refresh)

    def _fetch_raw(self, fetcher: Fetcher, title: str, refresh: bool) -> str:
        url = f"{_WIKI}/index.php?title={quote(title, safe='')}&action=raw"
        return fetcher.get_text(url, refresh=refresh, referer=_REFERER)


def extract_enh_data(text: str) -> dict[str, Any]:
    """从 `Object.assign(window.__ETW_DATA, {...});` 中提取舰船配置。"""
    marker = "Object.assign(window.__ETW_DATA,"
    ships: dict[str, Any] = {}
    position = 0
    while True:
        start = text.find(marker, position)
        if start < 0:
            break
        brace = text.find("{", start)
        if brace < 0:
            break
        end = _find_matching_brace(text, brace)
        if end < 0:
            break
        block = json.loads(text[brace : end + 1])
        ships.update(block)
        position = end + 1
    return ships


def _find_matching_brace(text: str, start: int) -> int:
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        else:
            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return index
    return -1


def parse_ship_page(wikitext: str) -> dict[str, str]:
    """提取舰船页模板参数与 `data-ship` 关联 ID。"""
    meta: dict[str, str] = {}
    for match in re.finditer(r"\|\s*([^|=\n{}]+?)\s*=\s*([^\n|}]*)", wikitext):
        key = match.group(1).strip()
        value = re.sub(r"<!--.*?-->", "", match.group(2)).strip()
        if key and value:
            meta[key] = value

    ship_id = re.search(r'data-ship=["\']?(\d+)', wikitext)
    if ship_id:
        meta["data-ship"] = ship_id.group(1)
    return meta


def _parse_version(text: str) -> str:
    match = re.search(r"ver(\d+)", text)
    return match.group(1) if match else ""


def _newer_version(current: str, candidate: str) -> str:
    if not candidate:
        return current
    if not current:
        return candidate
    return candidate if int(candidate) > int(current) else current


def _needs_mothership(name: str, ship_type: str | None) -> bool:
    """判断舰船是否只能由母舰搭载出战。

    页面类型可靠时只认战机/护航艇/无人机；TE 舰船缺页面类型，
    退化为按名称关键词判断（登陆舰自带动力，不算需要母舰）。
    """
    if ship_type:
        return any(keyword in ship_type for keyword in ("战机", "护航艇", "无人机"))
    return any(keyword in name for keyword in _AIRCRAFT_NAME_KEYWORDS)


def _build_ship(
    ship_id: str,
    ship: dict[str, Any],
    title: str,
    meta: dict[str, str],
) -> dict[str, Any]:
    ship_data = ship.get("ship") or {}
    base = ship_data.get("base") or {}
    systems = {str(system.get("id")): system.get("name") for system in ship.get("systems") or []}
    affix = ship.get("affix") or {}
    weapons = [
        _build_weapon(raw, systems, affix.get(str(weapon_id)) or [])
        for weapon_id, raw in (ship.get("weps") or {}).items()
    ]
    weapons.sort(key=lambda weapon: (weapon["系统ID"], weapon["名称"] or ""))

    command = meta.get("指挥值")
    if isinstance(command, str) and command.isdigit():
        command = int(command)

    name = ship_data.get("name") or meta.get("名称") or title
    ship_type = meta.get("类型")

    return {
        "id": ship_id,
        "名称": name,
        "类型": ship_type,
        "是否母舰": bool(ship.get("docks")),
        "需要母舰": _needs_mothership(name, ship_type),
        "稀有度": meta.get("稀有度"),
        "所属": meta.get("所属"),
        "武器类型": meta.get("武器类型"),
        "舰船站位": meta.get("舰船站位"),
        "指挥值": command,
        "血量": base.get("hp"),
        "物理护甲": base.get("resist"),
        "能量护甲": base.get("resist_energy"),
        "护盾值": base.get("shield"),
        "对空火力": base.get("aa"),
        "攻城火力": base.get("siege"),
        "巡航速度": base.get("speed"),
        "建造时间(秒)": base.get("time"),
        "建造成本": base.get("res"),
        "仓储容量": base.get("pool"),
        "武器": weapons,
    }


def _build_weapon(
    raw: dict[str, Any],
    systems: dict[str, str],
    affix_entries: list[Any] | None = None,
) -> dict[str, Any]:
    at_raw = raw.get("at")
    rep_raw = raw.get("rep")
    attack_runs = _as_int(at_raw) if at_raw is not None else 1
    ammo = _as_int(rep_raw) if rep_raw is not None else 1
    has_attack = at_raw is not None or rep_raw is not None
    system_id = str(raw.get("sys")) if raw.get("sys") is not None else ""
    sub_units = raw.get("sub") or []
    weapon_type = _as_int(raw.get("typ"))
    action = _as_int(raw.get("act"))
    type_raw = raw.get("typ")
    action_raw = raw.get("act")
    crit_rate, crit_damage, crit_target, crit_vs_air = _crit_stats(affix_entries)

    return {
        "名称": raw.get("mod"),
        "系统ID": system_id,
        "系统": systems.get(system_id, ""),
        "武器类型": _WEAPON_TYPES.get(weapon_type, f"类型{type_raw}" if type_raw is not None else ""),
        "武器作用": _WEAPON_ACTIONS.get(action, f"作用{action_raw}" if action_raw is not None else ""),
        "友方作用": action in _FRIENDLY_ACTIONS,
        "挂载数": raw.get("n"),
        "单发伤害": _to_float(raw.get("atk")),
        "暴击率": crit_rate,
        "暴击伤害": crit_damage,
        "暴击目标": crit_target,
        "防空暴击": crit_vs_air,
        "攻击次数": attack_runs * ammo if has_attack else None,
        "工作次数": raw.get("at"),
        "弹药数": raw.get("rep"),
        "冷却(毫秒)": raw.get("cd"),
        "持续时间(毫秒)": raw.get("dur"),
        "锁定时间(毫秒)": raw.get("lock"),
        "攻击间隔(毫秒)": raw.get("iv"),
        "去程时间(毫秒)": raw.get("fa"),
        "回程时间(毫秒)": raw.get("fb"),
        "对舰火力": raw.get("ship"),
        "对空火力": raw.get("aa"),
        "攻城火力": raw.get("sq"),
        "命中率": [
            {"优先级": hit[0], "目标": hit[1], "命中率": hit[2]}
            for hit in raw.get("hits") or []
            if isinstance(hit, list) and len(hit) >= 3
        ],
        "内载无人机": [{"名称": unit.get("nm"), "数量": unit.get("k")} for unit in sub_units if isinstance(unit, dict)],
    }


def _crit_stats(entries: list[Any] | None) -> tuple[float | None, float | None, str, bool | None]:
    """从武器 affix 词条中提取暴击率、暴击伤害与作用目标。

    Args:
        entries: ``ship["affix"][weapon_id]`` 的词条列表。

    Returns:
        ``(暴击率, 暴击伤害, 暴击目标, 是否防空暴击)``；没有暴击词条时
        前三项为 ``(None, None, "")``、最后一项为 ``None``。
    """
    for entry in entries or []:
        if not isinstance(entry, dict):
            continue
        match = _CRIT_PATTERN.search(str(entry.get("d") or ""))
        if not match:
            continue
        target = match.group(2).strip()
        vs_air = "舰载机" in target
        return (
            float(match.group(1)),
            float(match.group(3)),
            "舰载机" if vs_air else "舰船",
            vs_air,
        )
    return None, None, "", None


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _ship_sort_key(ship: dict[str, Any]) -> tuple[int, Any]:
    ship_id = str(ship.get("id", ""))
    return (0, int(ship_id)) if ship_id.isdigit() else (1, ship_id)
