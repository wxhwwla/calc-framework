#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""

发布目录布局：软件（exe）与游戏数据（JSON + DATA_LICENSE）分文件存放。



非商业分发须附带 DATA_LICENSE；数据路径与 ``data.loader`` 常量一致，便于 exe 旁加载。



注意：目录名 deliberately 不用 ``packaging``，以免遮蔽 PyInstaller 依赖的 PyPI ``packaging`` 包。

"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Literal

from games.endfield.data_loading.loader import CHARACTERS_JSON_PATH, EQUIPMENTS_JSON_PATH, WEAPONS_JSON_PATH

BuildTarget = Literal["launcher", "toolkit"]

ALL_BUILD_TARGETS: tuple[BuildTarget, ...] = ("launcher", "toolkit")


TARGET_APP_NAMES: dict[BuildTarget, str] = {
    "launcher": "Game Calc Platform",
    "toolkit": "开发者工具箱",
}


TARGET_ENTRIES: dict[BuildTarget, str] = {
    "launcher": "release_bundle/launcher_entry.py",
    "toolkit": "scripts/main_dev_toolkit.py",
}


RELEASE_DATA_FILES: tuple[tuple[str, str], ...] = (
    (CHARACTERS_JSON_PATH, CHARACTERS_JSON_PATH),
    (WEAPONS_JSON_PATH, WEAPONS_JSON_PATH),
    (EQUIPMENTS_JSON_PATH, EQUIPMENTS_JSON_PATH),
)


ARKNIGHTS_DATA_REL = "tools/arknights_scout/output/parsed"


LICENSE_FILES: tuple[tuple[str, str], ...] = (
    ("DATA_LICENSE", "DATA_LICENSE"),
    ("LICENSE", "LICENSE"),
    ("NOTICES.md", "NOTICES.md"),
)


RELEASE_README_NAME = "发布说明.txt"


def target_app_name(target: BuildTarget) -> str:
    return TARGET_APP_NAMES[target]


def target_entry(target: BuildTarget) -> str:
    return TARGET_ENTRIES[target]


def _launcher_readme(exe_version: str, package_version: str) -> str:
    return f"""Game Calc Platform — 发布包说明



【版本】EXE v{exe_version}（源码包 v{package_version}）

【软件】Game Calc Platform.exe — 见 LICENSE（AGPL-3.0 或您已取得的商业许可）

【数据】games/endfield/data/ 下 JSON — 见 DATA_LICENSE（非商业可用；商用不可用本仓库数据）

【明日方舟数据】tools/arknights_scout/output/parsed/ 下干员 JSON — 见 DATA_LICENSE



本软件是统一启动器，包含以下功能：

  - 终末地伤害计算器（--game endfield）

  - 明日方舟伤害计算器（--game arknights）

  - 开发者工具箱（--tool dev_toolkit）

  - 计算包查看器（--tool viewer）

  - 本地 Web 搜索服务器



GUI 框架：PySide6（LGPL-3.0）。仪表盘：matplotlib。

分发时请保持 exe 与本目录内数据文件相对位置不变。

"""


def _toolkit_readme(exe_version: str, package_version: str) -> str:
    return f"""开发者工具箱 — 发布包说明

【版本】EXE v{exe_version}（源码包 v{package_version}）

【软件】开发者工具箱.exe — 见 LICENSE（AGPL-3.0 或您已取得的商业许可）

本工具为框架开发工具集合，包含：数据编辑、布局编辑、图编辑、
DAG调试、计算包查看、AI生成、OCR标注等功能。

独立 exe，无需安装 Python 环境。

"""


def stage_release_folder(
    release_root: Path,
    *,
    project_root: Path,
    repo_root: Path,
    target: BuildTarget = "launcher",
) -> None:
    release_root.mkdir(parents=True, exist_ok=True)

    exe_version, package_version = _read_release_versions()

    if target == "toolkit":
        # 工具箱只复制许可文件和发布说明
        for dest_rel, src_rel in LICENSE_FILES:
            src = repo_root / src_rel
            if not src.is_file():
                raise FileNotFoundError(f"缺少许可文件: {src}")
            shutil.copy2(src, release_root / dest_rel)
        (release_root / RELEASE_README_NAME).write_text(
            _toolkit_readme(exe_version=exe_version, package_version=package_version),
            encoding="utf-8",
        )
        return

    # launcher: 复制游戏数据
    for dest_rel, src_rel in RELEASE_DATA_FILES:
        src = project_root / src_rel
        if not src.is_file():
            raise FileNotFoundError(f"缺少游戏数据源文件: {src}")
        dest = release_root / dest_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)

    # 明日方舟干员数据
    parsed_src = project_root / ARKNIGHTS_DATA_REL
    if parsed_src.is_dir():
        parsed_dst = release_root / ARKNIGHTS_DATA_REL
        parsed_dst.mkdir(parents=True, exist_ok=True)
        for f in parsed_src.iterdir():
            if f.suffix == ".json":
                shutil.copy2(f, parsed_dst)

    # 许可文件
    for dest_rel, src_rel in LICENSE_FILES:
        src = repo_root / src_rel
        if not src.is_file():
            raise FileNotFoundError(f"缺少许可文件: {src}")
        shutil.copy2(src, release_root / dest_rel)

    (release_root / RELEASE_README_NAME).write_text(
        _launcher_readme(exe_version=exe_version, package_version=package_version),
        encoding="utf-8",
    )


def _read_release_versions() -> tuple[str, str]:
    from scripts.please_read_me import get_exe_version, get_version

    return get_exe_version(), get_version()


def release_dir_from_dist(dist_dir: Path, *, target: BuildTarget = "launcher") -> Path:
    name = target_app_name(target)
    result = dist_dir / name
    # 如果目录被 Defender 锁定，用时间戳后缀
    if result.is_dir():
        try:
            test = result / ".write_test"
            test.touch(exist_ok=True)
            test.unlink(missing_ok=True)
        except (PermissionError, OSError):
            import time as _time

            ts = _time.strftime("%Y%m%d_%H%M%S")
            alt = dist_dir / f"{name}_{ts}"
            import logging

            logging.getLogger(__name__).warning("目录被锁定，改用: %s", alt)
            result = alt
    return result
