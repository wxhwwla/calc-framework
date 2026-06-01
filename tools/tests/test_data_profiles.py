# SPDX-License-Identifier: AGPL-3.0
"""Web data_profiles API 测试。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi import HTTPException

from web.backend.api import data_profiles as dp


def test_profiles_metadata_includes_endfield_and_arknights():
    ids = {p["id"] for p in dp.profiles_metadata()}
    assert ids >= {"endfield", "arknights"}


def test_list_endfield_characters_non_empty():
    rows = dp.list_entity_rows("endfield", "characters")
    assert len(rows) > 0
    assert "名称" in rows[0]


def test_arknights_operators_list():
    if not dp.ARKNIGHTS_OPERATORS.is_file():
        pytest.skip("operators.json 未生成")
    rows = dp.list_entity_rows("arknights", "operators")
    assert len(rows) >= 1


def test_entity_crud_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    sample = tmp_path / "sample.json"
    sample.write_text(json.dumps([{"名称": "测试A", "类型": "物理", "星级": 5}], ensure_ascii=False), encoding="utf-8")
    ent = dp.EntityDef("characters", "角色", sample, ("名称", "类型", "星级"))
    profile = dp.ProfileDef("test", "测试", (ent,))
    monkeypatch.setitem(dp.PROFILES, "test", profile)

    rows = dp.list_entity_rows("test", "characters")
    assert len(rows) == 1

    dp.create_entity_row("test", "characters", {"名称": "测试B", "类型": "能量", "星级": 4})
    assert len(dp.list_entity_rows("test", "characters", full=True)) == 2

    dp.update_entity_row("test", "characters", "测试B", {"名称": "测试B", "类型": "电磁", "星级": 4})
    updated = dp.list_entity_rows("test", "characters", full=True)
    assert updated[1]["类型"] == "电磁"

    dp.delete_entity_row("test", "characters", "测试A")
    assert len(dp.list_entity_rows("test", "characters")) == 1


def test_unknown_profile_raises():
    with pytest.raises(HTTPException) as exc:
        dp.get_profile("no_such")
    assert exc.value.status_code == 404
