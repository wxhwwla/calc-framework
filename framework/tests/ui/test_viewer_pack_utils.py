# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""CalcPackViewer 数据工具 — 实体来源映射与 calcpack 安全测试。"""

import zipfile
from pathlib import Path

import pytest

from calc_framework.ui import viewer_pack_utils
from calc_framework.ui.viewer_evaluator import build_viewer_context
from calc_framework.ui.viewer_pack_utils import (
    _DATA_FILE_TO_SOURCE,
    _SOURCE_DISPLAY_NAMES,
    _SOURCE_TO_DATA_FILE,
    build_context_from_entity,
    extract_assets_from_calcpack,
    load_calcpack,
)


def test_entity_source_mappings_include_enemy() -> None:
    assert _SOURCE_TO_DATA_FILE["enemy"] == "enemies"
    assert _DATA_FILE_TO_SOURCE["enemies"] == "enemy"
    assert _SOURCE_DISPLAY_NAMES["enemy"] == "敌人"
    assert _SOURCE_DISPLAY_NAMES["character"] == "角色"


def test_build_context_from_entity_flattens_enemy_scalars() -> None:
    ctx = build_context_from_entity(
        {"名称": "Boss", "等级": 50, "防御": 100, "韧性": [10, 20, 30]},
        "enemy",
        level=2,
    )

    assert ctx == {"防御": 100.0, "韧性": 20.0}


def test_build_viewer_context_uses_enemy_namespace_and_defaults() -> None:
    class _Var:
        default = 0.0

    variables = {"enemy.防御": _Var(), "enemy.抗性": _Var()}

    ctx = build_viewer_context(
        entity_selectors={"enemy": "Boss"},
        entity_data={"enemy": {"Boss": {"名称": "Boss", "防御": 100}}},
        variables=variables,
        level=90,
    )

    assert ctx["enemy"]["防御"] == 100.0
    assert ctx["enemy"]["抗性"] == 0.0


def _write_pack(path: Path, entries: dict[str, bytes]) -> Path:
    with zipfile.ZipFile(path, "w") as zf:
        for name, payload in entries.items():
            zf.writestr(name, payload)
    return path


def test_load_calcpack_accepts_valid_pack(tmp_path: Path) -> None:
    pack = _write_pack(
        tmp_path / "ok.calcpack",
        {"meta.json": b"{}", "assets/icon.png": b"png"},
    )

    data = load_calcpack(pack)

    assert data["meta.json"] == {}
    assert data["assets/icon.png"] == b"png"


@pytest.mark.parametrize(
    "member",
    [
        "../evil.txt",
        "assets/../../evil.txt",
        "/etc/passwd",
        "C:/evil.txt",
        "assets\\..\\evil.txt",
    ],
)
def test_load_calcpack_rejects_unsafe_member(tmp_path: Path, member: str) -> None:
    pack = _write_pack(tmp_path / "bad.calcpack", {member: b"x"})

    with pytest.raises(ValueError, match="非法|越界"):
        load_calcpack(pack)


def test_extract_assets_rejects_traversal_without_writing(tmp_path: Path) -> None:
    pack = _write_pack(
        tmp_path / "bad.calcpack",
        {"assets/../../evil.txt": b"pwn"},
    )
    target = tmp_path / "out"

    with pytest.raises(ValueError, match="非法|越界"):
        extract_assets_from_calcpack(pack, target)

    assert not (tmp_path / "evil.txt").exists()


def test_load_calcpack_rejects_too_many_entries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(viewer_pack_utils, "_MAX_PACK_ENTRIES", 1)
    pack = _write_pack(tmp_path / "many.calcpack", {"a.json": b"{}", "b.json": b"{}"})

    with pytest.raises(ValueError, match="条目过多"):
        load_calcpack(pack)


def test_load_calcpack_rejects_oversized_pack(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(viewer_pack_utils, "_MAX_PACK_BYTES", 1)
    pack = _write_pack(tmp_path / "big.calcpack", {"meta.json": b"{}"})

    with pytest.raises(ValueError, match="超过"):
        load_calcpack(pack)
