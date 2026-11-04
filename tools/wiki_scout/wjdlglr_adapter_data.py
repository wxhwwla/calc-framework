# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""把无尽的拉格朗日 Wiki 解析结果转换为适配器武器数据。

查看器从 `data/weapons.json` 读取记录，用 `名称` 生成下拉项；记录中的
数值字段会注入 `weapon.*` 命名空间，供 DAG 变量绑定。

用法::

    python -m tools.wiki_scout.wjdlglr_adapter_data \
        --input tools/wiki_scout/output/wjdlglr/wjdlglr.json \
        --output framework/adapters/wjdlglr/data/weapons.json
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

# 舰船种类展示顺序（同时用于武器下拉的排序与级联选择器）。
# 「未分类」放最后，吸收 Wiki 类型为空的舰船。
SHIP_CLASS_ORDER: tuple[str, ...] = (
    "战机",
    "护航艇",
    "无人机",
    "护卫舰",
    "驱逐舰",
    "巡洋舰",
    "战列巡洋舰",
    "战列舰",
    "航空母舰",
    "支援舰",
    "登陆舰",
    "要塞舰",
    "工程舰",
    "未分类",
)

_SHIP_CLASS_NAMES = frozenset(SHIP_CLASS_ORDER[:-1])
_SHIP_CLASS_RANK = {name: index for index, name in enumerate(SHIP_CLASS_ORDER)}

# (英文键, Wiki 命中率表里的目标名称)
TARGET_TYPES: tuple[tuple[str, str], ...] = (
    ("fighter", "战机"),
    ("escort", "护航艇"),
    ("drone", "无人机"),
    ("landing", "登陆舰(作业态)"),
    ("frigate", "护卫舰"),
    ("destroyer", "驱逐舰"),
    ("cruiser", "巡洋舰"),
    ("battlecruiser", "战列巡洋舰"),
    ("battleship", "战列舰"),
    ("carrier", "航空母舰"),
    ("support", "支援舰"),
    ("engineering_small", "小型工程舰"),
    ("engineering_medium", "中型工程舰"),
    ("engineering_large", "大型工程舰"),
    ("base_ship", "大本营船"),
    ("base", "基地"),
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = _REPO_ROOT / "tools" / "wiki_scout" / "output" / "wjdlglr" / "wjdlglr.json"
DEFAULT_OUTPUT = _REPO_ROOT / "framework" / "adapters" / "wjdlglr" / "data" / "weapons.json"

__all__ = [
    "DEFAULT_INPUT",
    "DEFAULT_OUTPUT",
    "SHIP_CLASS_ORDER",
    "TARGET_TYPES",
    "build_weapon_records",
    "main",
    "write_weapon_data",
]


def _number(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _seconds(value: Any) -> float:
    return _number(value) / 1000.0


def _damage_type(weapon: dict[str, Any]) -> str:
    """按武器作用判断伤害类型：能量 / 实弹 / 辅助。"""
    action = str(weapon.get("武器作用") or "").strip()
    if action == "能量攻击":
        return "能量"
    if action == "直射攻击":
        return "实弹"
    return "辅助"


def _hit_rates(weapon: dict[str, Any], friendly: bool) -> dict[str, float]:
    # 维修/驻防/增益对友方生效，Wiki 上的命中率不可信，统一按 100%。
    if friendly:
        return {f"hit_{key}": 100.0 for key, _ in TARGET_TYPES}

    table = {entry.get("目标"): entry.get("命中率") for entry in weapon.get("命中率") or [] if isinstance(entry, dict)}
    return {f"hit_{key}": _number(table.get(label)) for key, label in TARGET_TYPES}


def _unique_name(base: str, used: set[str]) -> str:
    if base not in used:
        used.add(base)
        return base
    suffix = 2
    while f"{base} #{suffix}" in used:
        suffix += 1
    name = f"{base} #{suffix}"
    used.add(name)
    return name


def _ship_classes(ship_type: str) -> list[str]:
    """把 Wiki 的舰船类型拆成级联选择器用的分类列表。

    Wiki 类型可能是逗号分隔的复合值（如 ``护卫舰,登陆舰``），也可能带
    ``未知/英雄舰/演习舰`` 等变体标签。只保留已知舰种，按展示顺序排列；
    没有已知舰种时归入 ``未分类``。
    """
    classes: list[str] = []
    for part in re.split(r"[,，]", ship_type):
        name = part.strip()
        if name in _SHIP_CLASS_NAMES and name not in classes:
            classes.append(name)
    classes.sort(key=_SHIP_CLASS_RANK.__getitem__)
    return classes or ["未分类"]


def _class_rank(record: dict[str, Any]) -> int:
    """记录所属舰船种类在展示顺序中的最靠前名次。"""
    return min(_SHIP_CLASS_RANK[name] for name in record["舰船分类"])


def build_weapon_records(parsed: dict[str, Any]) -> list[dict[str, Any]]:
    """把 `WjdlglrProvider.parse` 的结果展开为「舰船 × 武器」记录。

    Args:
        parsed: provider 的解析结果，需含 `舰船` 列表。

    Returns:
        每条记录含唯一的 `名称`、`舰船分类`（列表）、`武器标签`（同舰唯一）、
        舰船/母舰标志、武器时间与伤害字段、武器自带暴击
        （`crit_rate`/`crit_damage`/`crit_vs_air`/`crit_target`），以及
        16 个 `hit_<目标>` 命中率（百分数）。需要母舰的舰船所有武器共享
        全舰去程/回程时间。
    """
    used_names: set[str] = set()
    records: list[dict[str, Any]] = []
    for ship in parsed.get("舰船") or []:
        ship_name = str(ship.get("名称") or ship.get("id") or "未知舰船")
        ship_type = str(ship.get("类型") or "")
        ship_classes = _ship_classes(ship_type)
        is_mothership = bool(ship.get("是否母舰"))
        needs_mothership = bool(ship.get("需要母舰"))
        ship_weapons = ship.get("武器") or []
        # 去程/回程属于战机本身，不是单门武器：同一艘需要母舰的舰船
        # 上所有武器共享全舰飞行时间（Wiki 只把 fa/fb 写在主武器上）。
        flight_outbound = max((_seconds(weapon.get("去程时间(毫秒)")) for weapon in ship_weapons), default=0.0)
        flight_inbound = max((_seconds(weapon.get("回程时间(毫秒)")) for weapon in ship_weapons), default=0.0)
        used_labels: set[str] = set()
        for weapon in ship_weapons:
            weapon_name = str(weapon.get("名称") or "未命名武器")
            friendly = bool(weapon.get("友方作用"))
            system = str(weapon.get("系统") or weapon.get("系统ID") or "")
            base_name = f"{ship_name} · {weapon_name}"
            if base_name in used_names and system:
                base_name = f"{ship_name} · {weapon_name}（{system}）"
            label_base = weapon_name
            if label_base in used_labels and system:
                label_base = f"{weapon_name}（{system}）"
            damage_type = _damage_type(weapon)
            record: dict[str, Any] = {
                "名称": _unique_name(base_name, used_names),
                "舰船": ship_name,
                "舰船类型": ship_type,
                "舰船分类": ship_classes,
                "is_mothership": 1.0 if is_mothership else 0.0,
                "needs_mothership": 1.0 if needs_mothership else 0.0,
                "武器": weapon_name,
                "武器标签": _unique_name(label_base, used_labels),
                "武器作用": str(weapon.get("武器作用") or ""),
                "damage_type": damage_type,
                "is_energy": 1.0 if damage_type == "能量" else 0.0,
                "weapon_count": _number(weapon.get("挂载数"), 1.0),
                "ammo_count": _number(weapon.get("弹药数"), 1.0),
                "attack_runs": _number(weapon.get("工作次数"), 1.0),
                "base_cooldown": _seconds(weapon.get("冷却(毫秒)")),
                "base_duration": _seconds(weapon.get("持续时间(毫秒)")),
                "outbound": flight_outbound if needs_mothership else _seconds(weapon.get("去程时间(毫秒)")),
                "inbound": flight_inbound if needs_mothership else _seconds(weapon.get("回程时间(毫秒)")),
                "base_damage": _number(weapon.get("单发伤害")),
                "crit_rate": _number(weapon.get("暴击率")),
                "crit_damage": _number(weapon.get("暴击伤害")),
                "crit_target": str(weapon.get("暴击目标") or ""),
                "crit_vs_air": 1.0 if weapon.get("防空暴击") else 0.0,
                "friendly": 1.0 if friendly else 0.0,
            }
            record.update(_hit_rates(weapon, friendly))
            records.append(record)
    # 先按舰船种类（战机 → 护航艇 → 护卫舰 …），再让需要母舰/友方作用的
    # 记录靠前，最后按显示名排序。这样查看器默认选中战机武器，级联下拉
    # 的舰船种类顺序也稳定可预期。
    records.sort(
        key=lambda record: (
            _class_rank(record),
            -int(record["needs_mothership"]),
            int(record["friendly"]),
            str(record["名称"]),
        )
    )
    return records


def write_weapon_data(records: list[dict[str, Any]], output: Path) -> Path:
    """以紧凑 UTF-8 JSON 写入武器数据文件。"""
    output.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(records, ensure_ascii=False, separators=(",", ":"))
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="生成拉格朗日适配器的 data/weapons.json")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Wiki 解析结果 JSON")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="输出 weapons.json")
    args = parser.parse_args(argv)

    parsed = json.loads(args.input.read_text(encoding="utf-8"))
    records = build_weapon_records(parsed)
    write_weapon_data(records, args.output)
    print(f"写入 {args.output}：{len(records)} 条武器记录")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
