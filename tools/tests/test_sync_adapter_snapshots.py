# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""game_data_paths 与 sync_adapter_snapshots 单元测试。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from tools.sync_adapter_snapshots import sync_arknights_snapshot, sync_endfield_snapshots
from utils.game_data_paths import (
    ARKNIGHTS_OPERATORS_STANDARD,
    ARKNIGHTS_OPERATORS_STANDARD_REL,
    ENDFIELD_ADAPTER_DATA_DIR,
    ENDFIELD_CHARACTERS_JSON,
    ENDFIELD_CHARACTERS_STANDARD,
    REPO_ROOT,
)


def test_repo_root_is_project_root() -> None:
    assert (REPO_ROOT / "games" / "endfield").is_dir()
    assert (REPO_ROOT / "framework" / "adapters").is_dir()


def test_endfield_paths_under_repo() -> None:
    assert ENDFIELD_CHARACTERS_JSON.is_relative_to(REPO_ROOT)
    assert ENDFIELD_CHARACTERS_STANDARD.parent == ENDFIELD_ADAPTER_DATA_DIR


def test_arknights_standard_rel_matches_adapter_file() -> None:
    assert REPO_ROOT.joinpath(*ARKNIGHTS_OPERATORS_STANDARD_REL.split("/")) == ARKNIGHTS_OPERATORS_STANDARD


def test_sync_endfield_dry_run_success() -> None:
    stats = sync_endfield_snapshots(apply=False)
    assert stats["success"] is True
    assert len(stats["outputs"]) == 3
    assert all(o["written"] is False for o in stats["outputs"])


def test_sync_arknights_dry_run_missing_dir(tmp_path: Path) -> None:
    missing = tmp_path / "empty_parsed"
    stats = sync_arknights_snapshot(parsed_dir=missing, apply=False)
    assert stats["success"] is False


def test_sync_endfield_apply_to_tmp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """在临时目录验证写入逻辑，不修改仓库内 standard 文件。"""
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    dst.mkdir()

    char = [{"名称": "测试角色", "战技倍率": [100], "战技段伤害类型": ["物理"]}]
    (src / "characters.json").write_text(json.dumps(char, ensure_ascii=False), encoding="utf-8")
    (src / "weapons.json").write_text("[]", encoding="utf-8")
    (src / "equipments.json").write_text("[]", encoding="utf-8")

    import tools.sync_adapter_snapshots as sync_mod

    monkeypatch.setattr(sync_mod, "ENDFIELD_CHARACTERS_JSON", src / "characters.json")
    monkeypatch.setattr(sync_mod, "ENDFIELD_WEAPONS_JSON", src / "weapons.json")
    monkeypatch.setattr(sync_mod, "ENDFIELD_EQUIPMENTS_JSON", src / "equipments.json")
    monkeypatch.setattr(sync_mod, "ENDFIELD_CHARACTERS_STANDARD", dst / "characters_standard.json")
    monkeypatch.setattr(sync_mod, "ENDFIELD_WEAPONS_STANDARD", dst / "weapons_standard.json")
    monkeypatch.setattr(sync_mod, "ENDFIELD_EQUIPMENTS_STANDARD", dst / "equipments_standard.json")

    stats = sync_mod.sync_endfield_snapshots(apply=True)
    assert stats["success"] is True
    assert (dst / "characters_standard.json").is_file()
    data = json.loads((dst / "characters_standard.json").read_text(encoding="utf-8"))
    assert data[0]["名称"] == "测试角色"
