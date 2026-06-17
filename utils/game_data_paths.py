# SPDX-License-Identifier: AGPL-3.0
"""各游戏 JSON 与适配器快照路径常量（ADR-0023 / Phase 4 Step 4.3）。

层 A：运行时主数据（games/*/data 或 scout parsed）
层 B：适配器快照（framework/adapters/*/data/*_standard.json）

修改路径时须同步更新 ``docs/数据路径对照表.md`` 与本模块。
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# ── 终末地 层 A ──────────────────────────────────────────
ENDFIELD_DATA_DIR = REPO_ROOT / "games" / "endfield" / "data"
ENDFIELD_CHARACTERS_JSON = ENDFIELD_DATA_DIR / "characters.json"
ENDFIELD_WEAPONS_JSON = ENDFIELD_DATA_DIR / "weapons.json"
ENDFIELD_EQUIPMENTS_JSON = ENDFIELD_DATA_DIR / "equipments.json"
ENDFIELD_DATA_VERSION_JSON = ENDFIELD_DATA_DIR / "data_version.json"

# ── 终末地 层 B ──────────────────────────────────────────
ENDFIELD_ADAPTER_DATA_DIR = REPO_ROOT / "framework" / "adapters" / "endfield" / "data"
ENDFIELD_CHARACTERS_STANDARD = ENDFIELD_ADAPTER_DATA_DIR / "characters_standard.json"
ENDFIELD_WEAPONS_STANDARD = ENDFIELD_ADAPTER_DATA_DIR / "weapons_standard.json"
ENDFIELD_EQUIPMENTS_STANDARD = ENDFIELD_ADAPTER_DATA_DIR / "equipments_standard.json"

# ── 明日方舟 scout / 层 A ────────────────────────────────
ARKNIGHTS_SCOUT_OUTPUT_DIR = REPO_ROOT / "tools" / "arknights_scout" / "output"
ARKNIGHTS_PARSED_DIR = ARKNIGHTS_SCOUT_OUTPUT_DIR / "parsed"
ARKNIGHTS_OPERATORS_AGGREGATE = ARKNIGHTS_PARSED_DIR / "operators.json"

# ── 明日方舟 层 B ──────────────────────────────────────────
ARKNIGHTS_ADAPTER_DATA_DIR = REPO_ROOT / "framework" / "adapters" / "arknights" / "data"
ARKNIGHTS_OPERATORS_STANDARD = ARKNIGHTS_ADAPTER_DATA_DIR / "operators_standard.json"

# get_resource_path 用相对路径（PyInstaller _MEIPASS）
ARKNIGHTS_OPERATORS_STANDARD_REL = "framework/adapters/arknights/data/operators_standard.json"

# 终末地 loader 用相对路径
ENDFIELD_CHARACTERS_JSON_REL = "games/endfield/data/characters.json"
ENDFIELD_WEAPONS_JSON_REL = "games/endfield/data/weapons.json"
ENDFIELD_EQUIPMENTS_JSON_REL = "games/endfield/data/equipments.json"


def repo_relative(path: Path) -> str:
    """仓库根下的 POSIX 相对路径。"""
    return path.relative_to(REPO_ROOT).as_posix()
