# SPDX-License-Identifier: AGPL-3.0
"""打包模式下资源路径与干员库加载测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from utils.path_utils import get_resource_path


def test_get_resource_path_prefers_meipass_in_onefile(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    rel = "framework/adapters/arknights/data/operators_standard.json"
    exe_dir = tmp_path / "release"
    exe_dir.mkdir()
    meipass = tmp_path / "_meipass"
    target = meipass / rel
    target.parent.mkdir(parents=True)
    target.write_text("[]", encoding="utf-8")

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(exe_dir / "Game Calc Platform.exe"), raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(meipass), raising=False)

    resolved = get_resource_path(rel)
    assert resolved.is_file()
    assert resolved == target


def test_load_operators_standard_via_meipass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from games.arknights.operator_catalog import _load_operators_standard_fallback

    rel = "framework/adapters/arknights/data/operators_standard.json"
    repo = Path(__file__).resolve().parents[3]
    src = repo / rel
    if not src.is_file():
        pytest.skip("仓库无 operators_standard.json")

    exe_dir = tmp_path / "release"
    exe_dir.mkdir()
    meipass = tmp_path / "_meipass"
    dst = meipass / rel
    dst.parent.mkdir(parents=True)
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(exe_dir / "app.exe"), raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(meipass), raising=False)

    data = _load_operators_standard_fallback()
    assert len(data) >= 100
