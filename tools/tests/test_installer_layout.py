# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""NSIS 安装器目录校验与失败退出测试（P1-07/P1-08）。"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from installer import build_installer
from release_bundle.release_layout import TARGET_APP_NAMES


def _make_launcher_only_dist(dist_dir: Path) -> Path:
    launcher_name = TARGET_APP_NAMES["launcher"]
    app_dir = dist_dir / launcher_name
    app_dir.mkdir(parents=True)
    (app_dir / f"{launcher_name}.exe").write_bytes(b"MZ")
    return app_dir


def test_validate_dist_accepts_current_launcher_layout(tmp_path: Path) -> None:
    """当前发布布局只有 launcher，不应再误报旧四应用缺失。"""
    _make_launcher_only_dist(tmp_path)

    assert build_installer._validate_dist(tmp_path) == []


def test_validate_dist_reports_missing_launcher(tmp_path: Path) -> None:
    issues = build_installer._validate_dist(tmp_path)

    launcher_name = TARGET_APP_NAMES["launcher"]
    assert any(launcher_name in issue for issue in issues)


def test_build_installer_fails_when_dist_incomplete(tmp_path: Path, monkeypatch) -> None:
    """产物缺失时不得继续构建或返回成功。"""
    monkeypatch.setattr(build_installer, "_ensure_nsis", lambda: "makensis")

    assert build_installer.build_installer(tmp_path, "1.0.0", dry_run=True) == 1


def test_build_installer_fails_when_nsis_missing(tmp_path: Path, monkeypatch) -> None:
    """NSIS 不可用时必须失败，而不是输出警告后继续。"""
    _make_launcher_only_dist(tmp_path)
    monkeypatch.setattr(build_installer, "_ensure_nsis", lambda: None)

    assert build_installer.build_installer(tmp_path, "1.0.0") == 1


def test_build_installer_fails_when_nsis_compile_fails(tmp_path: Path, monkeypatch) -> None:
    _make_launcher_only_dist(tmp_path)
    monkeypatch.setattr(build_installer, "_ensure_nsis", lambda: "makensis")

    class _Result:
        returncode = 2

    monkeypatch.setattr(build_installer.subprocess, "run", lambda *_, **__: _Result())

    assert build_installer.build_installer(tmp_path, "1.0.0") == 1


def test_build_installer_fails_when_output_missing(tmp_path: Path, monkeypatch) -> None:
    """NSIS 返回 0 但未产出安装包时仍应失败。"""
    _make_launcher_only_dist(tmp_path)
    monkeypatch.setattr(build_installer, "_ensure_nsis", lambda: "makensis")

    class _Result:
        returncode = 0

    monkeypatch.setattr(build_installer.subprocess, "run", lambda *_, **__: _Result())

    assert build_installer.build_installer(tmp_path, "1.0.0") == 1
