# SPDX-License-Identifier: AGPL-3.0
"""配置包设计器 — 各游戏数据录入模板。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class DataProfile:
    """DataProfile 类。"""
    id: str
    label: str
    adapter_dir: Path
    entity_tabs: tuple[tuple[str, str, list[str]], ...]


PROFILES: dict[str, DataProfile] = {
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
        entity_tabs=(
            ("干员", "operators.json", ["名称", "职业", "星级", "分支"]),
        ),
    ),
}

# 干员 JSON 默认路径（BWIKI 解析产物）
ARKNIGHTS_OPERATORS_JSON = (
    _PROJECT_ROOT / "tools" / "arknights_scout" / "output" / "parsed" / "operators.json"
)

ADAPTER_NAME_TO_PROFILE: dict[str, str] = {
    "终末地伤害计算": "endfield",
    "明日方舟伤害计算": "arknights",
}


def data_dir_for_profile(profile: DataProfile) -> Path:
    """各 profile 的数据文件目录。"""
    if profile.id == "endfield":
        return profile.adapter_dir / "data"
    if profile.id == "arknights":
        return ARKNIGHTS_OPERATORS_JSON.parent
    return profile.adapter_dir / "data"
