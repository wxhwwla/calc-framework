# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""无尽的拉格朗日：Wiki 解析结果 → 适配器 weapons.json 数据测试。"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from tools.wiki_scout.wjdlglr_adapter_data import (
    TARGET_TYPES,
    build_weapon_records,
    write_weapon_data,
)


def _ship(name: str, weapon: dict[str, Any], **overrides: Any) -> dict[str, Any]:
    ship: dict[str, Any] = {
        "名称": name,
        "类型": "战机",
        "是否母舰": False,
        "需要母舰": True,
        "武器": [weapon],
    }
    ship.update(overrides)
    return ship


def _weapon(**overrides: Any) -> dict[str, Any]:
    weapon: dict[str, Any] = {
        "名称": "测试炮",
        "系统": "测试系统",
        "武器作用": "能量攻击",
        "友方作用": False,
        "挂载数": 2,
        "单发伤害": 50.0,
        "工作次数": 1,
        "弹药数": 3,
        "冷却(毫秒)": 6000,
        "持续时间(毫秒)": 10000,
        "去程时间(毫秒)": 4000,
        "回程时间(毫秒)": 2000,
        "命中率": [
            {"优先级": 3, "目标": "战机", "命中率": 22},
            {"优先级": 1, "目标": "护卫舰", "命中率": 85},
        ],
    }
    weapon.update(overrides)
    return weapon


def test_target_types_cover_all_sixteen_categories() -> None:
    assert len(TARGET_TYPES) == 16
    assert TARGET_TYPES[0] == ("fighter", "战机")
    assert TARGET_TYPES[-2:] == (("base_ship", "大本营船"), ("base", "基地"))


def test_build_maps_stats_and_hit_rates() -> None:
    parsed = {"舰船": [_ship("测试舰", _weapon())]}

    record = build_weapon_records(parsed)[0]

    assert record["名称"] == "测试舰 · 测试炮"
    assert record["舰船"] == "测试舰"
    assert record["舰船类型"] == "战机"
    assert record["is_mothership"] == 0.0
    assert record["needs_mothership"] == 1.0
    assert record["weapon_count"] == 2
    assert record["ammo_count"] == 3
    assert record["attack_runs"] == 1
    assert record["base_cooldown"] == 6.0
    assert record["base_duration"] == 10.0
    assert record["outbound"] == 4.0
    assert record["inbound"] == 2.0
    assert record["base_damage"] == 50.0
    assert record["friendly"] == 0.0
    assert record["damage_type"] == "能量"
    assert record["is_energy"] == 1.0
    assert record["hit_fighter"] == 22.0
    assert record["hit_frigate"] == 85.0
    assert record["hit_cruiser"] == 0.0


def test_direct_attack_is_physical() -> None:
    parsed = {"舰船": [_ship("测试舰", _weapon(武器作用="直射攻击"))]}

    record = build_weapon_records(parsed)[0]

    assert record["damage_type"] == "实弹"
    assert record["is_energy"] == 0.0


def test_friendly_action_is_support_damage_type() -> None:
    parsed = {"舰船": [_ship("维修舰", _weapon(武器作用="维修", 友方作用=True))]}

    record = build_weapon_records(parsed)[0]

    assert record["damage_type"] == "辅助"
    assert record["is_energy"] == 0.0


def test_friendly_weapon_forces_all_hit_rates_to_hundred() -> None:
    parsed = {
        "舰船": [
            _ship(
                "维修舰",
                _weapon(武器作用="维修", 友方作用=True, 命中率=[{"优先级": 1, "目标": "战机", "命中率": 5}]),
            )
        ]
    }

    record = build_weapon_records(parsed)[0]

    assert record["friendly"] == 1.0
    assert all(record[f"hit_{key}"] == 100.0 for key, _ in TARGET_TYPES)


def test_missing_weapon_fields_fall_back_to_safe_defaults() -> None:
    parsed = {
        "舰船": [
            _ship(
                "空壳舰",
                {
                    "名称": "空壳武器",
                    "友方作用": False,
                    "命中率": [],
                },
            )
        ]
    }

    record = build_weapon_records(parsed)[0]

    assert record["weapon_count"] == 1
    assert record["ammo_count"] == 1
    assert record["attack_runs"] == 1
    assert record["base_cooldown"] == 0.0
    assert record["base_duration"] == 0.0
    assert record["outbound"] == 0.0
    assert record["inbound"] == 0.0
    assert record["base_damage"] == 0.0
    assert record["damage_type"] == "辅助"
    assert record["is_energy"] == 0.0


def test_record_names_are_unique_for_same_weapon_name() -> None:
    parsed = {
        "舰船": [
            _ship("舰A", _weapon(系统="系统一")),
            _ship("舰A", _weapon(系统="系统二")),
        ]
    }

    names = [record["名称"] for record in build_weapon_records(parsed)]

    assert len(names) == 2
    assert len(set(names)) == 2


def test_ship_class_splits_composite_types() -> None:
    parsed = {"舰船": [_ship("登陆护卫舰", _weapon(), 类型="护卫舰,登陆舰")]}

    record = build_weapon_records(parsed)[0]

    assert record["舰船分类"] == ["护卫舰", "登陆舰"]


def test_ship_class_drops_variant_tags_and_unknown() -> None:
    parsed = {
        "舰船": [
            _ship("英雄驱逐", _weapon(), 类型="驱逐舰,英雄舰"),
            _ship("未知护卫", _weapon(), 类型="未知,护卫舰"),
            _ship("无类型舰", _weapon(), 类型=""),
        ]
    }

    by_ship = {record["舰船"]: record["舰船分类"] for record in build_weapon_records(parsed)}

    assert by_ship == {
        "英雄驱逐": ["驱逐舰"],
        "未知护卫": ["护卫舰"],
        "无类型舰": ["未分类"],
    }


def test_weapon_label_is_unique_within_ship() -> None:
    parsed = {
        "舰船": [
            _ship(
                "舰A",
                _weapon(系统="系统一"),
                # 同一舰船安装两门同名武器
            )
        ]
    }
    parsed["舰船"][0]["武器"].append(_weapon(系统="系统二"))

    records = build_weapon_records(parsed)
    labels = [record["武器标签"] for record in records]

    assert len(labels) == 2
    assert len(set(labels)) == 2
    assert labels[0] == "测试炮"


def test_records_sorted_by_ship_class_first() -> None:
    parsed = {
        "舰船": [
            _ship("护卫舰A", _weapon(), 类型="护卫舰", 需要母舰=False),
            _ship("战机A", _weapon(), 类型="战机", 需要母舰=True),
            _ship("驱逐舰A", _weapon(), 类型="驱逐舰", 需要母舰=False),
        ]
    }

    classes = [record["舰船分类"][0] for record in build_weapon_records(parsed)]

    assert classes == ["战机", "护卫舰", "驱逐舰"]


def test_crit_stats_are_copied_from_weapon() -> None:
    parsed = {
        "舰船": [
            _ship(
                "测试舰",
                _weapon(暴击率=15.0, 暴击伤害=170.0, 暴击目标="舰船", 防空暴击=False),
            )
        ]
    }

    record = build_weapon_records(parsed)[0]

    assert record["crit_rate"] == 15.0
    assert record["crit_damage"] == 170.0
    assert record["crit_target"] == "舰船"
    assert record["crit_vs_air"] == 0.0


def test_anti_air_crit_marks_target_and_flag() -> None:
    parsed = {
        "舰船": [
            _ship(
                "防空舰",
                _weapon(暴击率=25.0, 暴击伤害=100.0, 暴击目标="舰载机", 防空暴击=True),
            )
        ]
    }

    record = build_weapon_records(parsed)[0]

    assert record["crit_target"] == "舰载机"
    assert record["crit_vs_air"] == 1.0


def test_missing_crit_stats_default_to_zero() -> None:
    parsed = {"舰船": [_ship("测试舰", _weapon())]}

    record = build_weapon_records(parsed)[0]

    assert record["crit_rate"] == 0.0
    assert record["crit_damage"] == 0.0
    assert record["crit_target"] == ""
    assert record["crit_vs_air"] == 0.0


def test_aircraft_weapons_share_ship_level_flight_time() -> None:
    first = _weapon(**{"去程时间(毫秒)": 8000, "回程时间(毫秒)": 4000})
    second = _weapon(名称="第二门炮", **{"去程时间(毫秒)": None, "回程时间(毫秒)": None})
    parsed = {"舰船": [_ship("战机A", first, 武器=[first, second])]}

    records = build_weapon_records(parsed)

    assert [record["outbound"] for record in records] == [8.0, 8.0]
    assert [record["inbound"] for record in records] == [4.0, 4.0]


def test_non_aircraft_keeps_per_weapon_flight_time() -> None:
    first = _weapon(**{"去程时间(毫秒)": 6000, "回程时间(毫秒)": 4000})
    second = _weapon(名称="第二门炮", **{"去程时间(毫秒)": None, "回程时间(毫秒)": None})
    parsed = {
        "舰船": [
            _ship("驱逐舰A", first, 类型="驱逐舰", 需要母舰=False, 武器=[first, second]),
        ]
    }

    records = build_weapon_records(parsed)

    assert [record["outbound"] for record in records] == [6.0, 0.0]
    assert [record["inbound"] for record in records] == [4.0, 0.0]


def test_write_weapon_data_is_compact_utf8(tmp_path: Path) -> None:
    records = build_weapon_records({"舰船": [_ship("测试舰", _weapon())]})
    output = tmp_path / "weapons.json"

    write_weapon_data(records, output)

    raw = output.read_bytes()
    assert b"\n" not in raw
    assert "测试舰".encode() in raw
    assert json.loads(raw.decode("utf-8")) == records
