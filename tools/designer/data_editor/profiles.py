# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""配置包设计器 — 各游戏数据录入模板。

支持内置配置（终末地、明日方舟）和动态发现新适配器。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from utils.game_data_paths import (
    ARKNIGHTS_OPERATORS_AGGREGATE,
    ENDFIELD_ADAPTER_DATA_DIR,
    REPO_ROOT as _PROJECT_ROOT,
)


@dataclass(frozen=True)
class DataProfile:
    """DataProfile 类。"""

    id: str
    label: str
    adapter_dir: Path
    entity_tabs: tuple[tuple[str, str, list[str]], ...]


# 内置配置（终末地、明日方舟）
_BUILTIN_PROFILES: dict[str, DataProfile] = {
    "endfield": DataProfile(
        id="endfield",
        label="终末地",
        adapter_dir=_PROJECT_ROOT / "framework" / "adapters" / "endfield",
        entity_tabs=(
            ("角色", "characters_standard.json", ["名称", "类型", "星级", "武器", "主能力", "副能力"]),
            ("武器", "weapons_standard.json", ["名称", "类型", "星级"]),
            ("装备", "equipments_standard.json", ["名称", "装备种类", "部位", "稀有度", "所属套组"]),
        ),
    ),
    "arknights": DataProfile(
        id="arknights",
        label="明日方舟",
        adapter_dir=_PROJECT_ROOT / "framework" / "adapters" / "arknights",
        entity_tabs=(("干员", "operators.json", ["名称", "职业", "星级", "分支"]),),
    ),
}

# 干员 JSON 默认路径（BWIKI 解析产物 aggregate）
ARKNIGHTS_OPERATORS_JSON = ARKNIGHTS_OPERATORS_AGGREGATE

_BUILTIN_ADAPTER_NAME_TO_PROFILE: dict[str, str] = {
    "终末地伤害计算": "endfield",
    "明日方舟伤害计算": "arknights",
}


class _AdapterNameToProfileProxy:
    """延迟代理，动态发现新适配器名称到 profile ID 的映射。"""

    def __getitem__(self, key: str) -> str:
        profiles = get_all_profiles()
        # 先查内置映射
        if key in _BUILTIN_ADAPTER_NAME_TO_PROFILE:
            return _BUILTIN_ADAPTER_NAME_TO_PROFILE[key]
        # 再查动态发现的（label 匹配）
        for pid, prof in profiles.items():
            if prof.label == key:
                return pid
        raise KeyError(key)

    def get(self, key: str, default: str | None = None) -> str | None:
        try:
            return self[key]
        except KeyError:
            return default

    def __contains__(self, key: object) -> bool:
        if key in _BUILTIN_ADAPTER_NAME_TO_PROFILE:
            return True
        profiles = get_all_profiles()
        return any(prof.label == key for prof in profiles.values())


ADAPTER_NAME_TO_PROFILE = _AdapterNameToProfileProxy()


def _discover_adapter_profiles() -> dict[str, DataProfile]:
    """扫描 framework/adapters/ 目录，为未注册的适配器动态创建 DataProfile。"""
    adapters_dir = _PROJECT_ROOT / "framework" / "adapters"
    if not adapters_dir.is_dir():
        return {}

    discovered: dict[str, DataProfile] = {}
    for entry in sorted(adapters_dir.iterdir()):
        if not entry.is_dir() or entry.name.startswith("_"):
            continue
        meta_path = entry / "meta.json"
        if not meta_path.is_file():
            continue
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        name = meta.get("name") or entry.name
        profile_id = entry.name

        # 跳过已内置的
        if profile_id in _BUILTIN_PROFILES:
            continue

        # 扫描 data/ 目录下的 JSON 文件作为 entity_tabs
        data_dir = entry / "data"
        entity_tabs: list[tuple[str, str, list[str]]] = []
        if data_dir.is_dir():
            for json_file in sorted(data_dir.glob("*.json")):
                tab_name = json_file.stem
                entity_tabs.append((tab_name, json_file.name, ["名称"]))

        # 如果没有数据文件，从 attr_schema 推断默认标签页
        if not entity_tabs:
            entity_tabs = _infer_tabs_from_attr_schema(entry)

        discovered[profile_id] = DataProfile(
            id=profile_id,
            label=name,
            adapter_dir=entry,
            entity_tabs=tuple(entity_tabs),
        )

    return discovered


def _infer_tabs_from_attr_schema(adapter_dir: Path) -> list[tuple[str, str, list[str]]]:
    """从 attr_schema.json 推断默认的数据标签页。"""
    schema_path = adapter_dir / "attr_schema.json"
    if not schema_path.is_file():
        return [("数据", "data.json", ["名称", "值"])]

    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return [("数据", "data.json", ["名称", "值"])]

    # 按 source 分组
    sources: dict[str, list[str]] = {}
    for attr in schema.get("attributes", []):
        source = attr.get("source", "character")
        name = attr.get("name", "")
        if name:
            sources.setdefault(source, []).append(name)

    # 为每个 source 创建一个标签页
    tabs: list[tuple[str, str, list[str]]] = []
    source_labels = {
        "character": "角色",
        "weapon": "武器",
        "equipment": "装备",
        "enemy": "敌人",
        "computed": "计算",
        "user_input": "输入",
    }
    for source, fields in sources.items():
        label = source_labels.get(source, source)
        filename = f"{source}s.json"
        columns = ["名称"] + fields[:4]  # 最多显示 4 个字段
        tabs.append((label, filename, columns))

    return tabs if tabs else [("数据", "data.json", ["名称", "值"])]


def get_all_profiles() -> dict[str, DataProfile]:
    """返回所有可用的 DataProfile（内置 + 动态发现）。"""
    result = dict(_BUILTIN_PROFILES)
    result.update(_discover_adapter_profiles())
    return result


class _ProfilesProxy:
    """延迟代理，让 PROFILES[key] 动态发现新适配器。"""

    def __getitem__(self, key: str) -> DataProfile:
        return get_all_profiles()[key]

    def __iter__(self):
        return iter(get_all_profiles())

    def __len__(self):
        return len(get_all_profiles())

    def keys(self):
        return get_all_profiles().keys()

    def values(self):
        return get_all_profiles().values()

    def items(self):
        return get_all_profiles().items()

    def __contains__(self, key: object) -> bool:
        return key in get_all_profiles()


PROFILES = _ProfilesProxy()


def data_dir_for_profile(profile: DataProfile) -> Path:
    """各 profile 的数据文件目录。"""
    if profile.id == "endfield":
        return ENDFIELD_ADAPTER_DATA_DIR
    if profile.id == "arknights":
        return ARKNIGHTS_OPERATORS_AGGREGATE.parent
    return profile.adapter_dir / "data"
