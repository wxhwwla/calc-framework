#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""终末地 wheel 打包回归测试（P0-03）。

背景：``games/endfield/pyproject.toml`` 曾只声明顶层 ``main``/``please_read_me``
模块和已不存在的旧包名，构建出的 wheel 只有 7 个文件，无法在干净环境中运行。

本测试实际构建 wheel 并检查运行必需的包、数据、适配器资源与控制台入口。
构建使用 ``--no-build-isolation``，不依赖网络。
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

_PKG_ROOT = Path(__file__).resolve().parents[2]
_REPO_ROOT = _PKG_ROOT.parents[1]

_REQUIRED_WHEEL_MEMBERS = frozenset(
    {
        "games/endfield/main.py",
        "games/endfield/calc/dag_adapter/adapter.py",
        "games/endfield/data/characters.json",
        "games/endfield/data/weapons.json",
        "games/endfield/data/equipments.json",
        "games/endfield/gui/endfield_app.py",
        "games/endfield/gui/legal/wechat_reward.jpg",
        "utils/path_utils.py",
        "scripts/_version.py",
        "scripts/please_read_me.py",
        "framework/adapters/endfield/meta.json",
        "framework/adapters/endfield/dag/endfield_full.dag.json",
        "framework/adapters/endfield/ui/layout.json",
        "resources/donation/donation_q.jpg",
        "tools/ocr/__init__.py",
        "tools/ocr/endfield_classes.yaml",
    }
)

_REQUIRED_FRAMEWORK_WHEEL_MEMBERS = frozenset(
    {
        "calc_framework/ui/i18n.py",
        "calc_framework/ui/i18n_data/en.json",
        "calc_framework/ui/i18n_data/zh-CN.json",
        "calc_framework/configs/endfield_full.dag.json",
    }
)

_IGNORE = shutil.ignore_patterns(
    "__pycache__",
    "*.pyc",
    "build",
    "*.egg-info",
    ".pytest_cache",
    ".ruff_cache",
    ".benchmarks",
    ".coverage",
    ".cov75",
    "tests",
)


def _stage_clean_source(destination: Path) -> Path:
    """把打包所需的源码复制成干净布局，避免旧 build/ 与 egg-info 污染 wheel。"""
    package_dir = destination / "games" / "endfield"
    shutil.copytree(_PKG_ROOT, package_dir, ignore=_IGNORE)
    shutil.copy2(_REPO_ROOT / "games" / "__init__.py", destination / "games" / "__init__.py")
    (destination / "tools").mkdir(parents=True, exist_ok=True)
    shutil.copy2(_REPO_ROOT / "tools" / "__init__.py", destination / "tools" / "__init__.py")
    for rel in ("utils", "scripts", "tools/ocr", "framework/adapters/endfield", "resources/donation"):
        shutil.copytree(_REPO_ROOT / rel, destination / rel, ignore=_IGNORE)
    return package_dir


def _stage_framework_source(destination: Path) -> Path:
    """复制框架打包输入，避免源码树中的 build/ 与 egg-info 污染 wheel。"""
    framework_dir = destination / "framework"
    (framework_dir / "src").mkdir(parents=True)
    shutil.copy2(_REPO_ROOT / "framework" / "pyproject.toml", framework_dir / "pyproject.toml")
    shutil.copy2(_REPO_ROOT / "framework" / "README.md", framework_dir / "README.md")
    shutil.copytree(
        _REPO_ROOT / "framework" / "src" / "calc_framework",
        framework_dir / "src" / "calc_framework",
        ignore=_IGNORE,
    )
    return framework_dir


def _build_wheel(project_dir: Path, output_dir: Path, pattern: str) -> Path:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            str(project_dir),
            "--no-deps",
            "--no-build-isolation",
            "-w",
            str(output_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    wheels = list(output_dir.glob(pattern))
    assert len(wheels) == 1, f"应只生成一个 wheel，实际: {wheels}"
    return wheels[0]


@pytest.mark.slow
def test_wheel_contains_runtime_modules_and_data(tmp_path: Path) -> None:
    project_dir = _stage_clean_source(tmp_path / "repo")
    wheel = _build_wheel(project_dir, tmp_path / "dist", "calc_framework_endfield-*.whl")

    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        missing = sorted(_REQUIRED_WHEEL_MEMBERS - names)
        assert not missing, f"wheel 缺少运行必需文件: {missing}"
        assert not any(name.startswith("games/endfield/tests/") for name in names)
        assert "main.py" not in names, "不应再安装顶层 main.py；入口应走 games.endfield.main"
        assert "please_read_me.py" not in names, "不应再安装顶层 please_read_me.py"

        entry_points = next(name for name in names if name.endswith("entry_points.txt"))
        entry_text = archive.read(entry_points).decode("utf-8")
        assert "endfield-calculator = games.endfield.main:main" in entry_text

        metadata = next(name for name in names if name.endswith("METADATA"))
        metadata_text = archive.read(metadata).decode("utf-8")
        assert "Requires-Dist: calc-framework>=0.3.1" in metadata_text


@pytest.mark.slow
def test_framework_wheel_contains_i18n_data(tmp_path: Path) -> None:
    """终末地 GUI 依赖框架 i18n；框架 wheel 必须带 JSON 翻译与 DAG 配置。"""
    project_dir = _stage_framework_source(tmp_path / "framework-src")
    wheel = _build_wheel(project_dir, tmp_path / "dist", "calc_framework-*.whl")

    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        missing = sorted(_REQUIRED_FRAMEWORK_WHEEL_MEMBERS - names)
        assert not missing, f"framework wheel 缺少运行必需文件: {missing}"
