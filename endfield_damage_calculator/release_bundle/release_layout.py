#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发布目录布局：软件（exe）与游戏数据（JSON + DATA_LICENSE）分文件存放。

非商业分发须附带 DATA_LICENSE；数据路径与 ``data.loader`` 常量一致，便于 exe 旁加载。

注意：目录名 deliberately 不用 ``packaging``，以免遮蔽 PyInstaller 依赖的 PyPI ``packaging`` 包。
"""

from __future__ import annotations

import shutil
from pathlib import Path

from data.loader import CHARACTERS_JSON_PATH, EQUIPMENTS_JSON_PATH, WEAPONS_JSON_PATH

# PyInstaller onedir 输出目录名 / 压缩包根目录名
RELEASE_APP_NAME = "终末地伤害计算器"

# (相对发布根目录的路径, 包内源路径相对于 project_root)
RELEASE_DATA_FILES: tuple[tuple[str, str], ...] = (
    (CHARACTERS_JSON_PATH, CHARACTERS_JSON_PATH),
    (WEAPONS_JSON_PATH, WEAPONS_JSON_PATH),
    (EQUIPMENTS_JSON_PATH, EQUIPMENTS_JSON_PATH),
)

# 随数据分发的许可与声明（相对 repo 根目录）
LICENSE_FILES: tuple[tuple[str, str], ...] = (
    ("DATA_LICENSE", "DATA_LICENSE"),
    ("LICENSE", "LICENSE"),
    ("NOTICES.md", "NOTICES.md"),
)

RELEASE_README_NAME = "发布说明.txt"


def _release_readme_text(*, exe_version: str, package_version: str) -> str:
    return f"""终末地伤害计算小工具 — 发布包说明

【版本】EXE v{exe_version}（源码包 v{package_version}，见 please_read_me._EXE_VERSION / _VERSION）
【软件】终末地伤害计算器.exe — 见 LICENSE（AGPL-3.0 或您已取得的商业许可）
【数据】character_weapon_equipment/ 下 JSON — 见 DATA_LICENSE（非商业可用；商用不可用本仓库数据）

完整说明：docs/数据来源与许可.md（源码仓库）或 GUI「数据来源与许可」按钮。

分发时请保持 exe 与本目录内 JSON、许可文件相对位置不变；可单独更新 JSON 而无需重打 exe。
修改 _EXE_VERSION 后须重新执行 build.py，否则 exe 内版本不会变。

【全量/MVP 搜索导出】首次运行后在本文件夹下自动创建 search_output/（与 exe 同级，不在 C 盘临时目录）。
  - 内含 search_runs.db、mvp_exports/ 等；可直接备份或删除该文件夹。
【并行线程】GUI「计算与搜索」中「自动」= 逻辑核数减 1；手动选项不会超过本机逻辑核数。
【伤害仪表盘】已内置 matplotlib（无需用户另装）；图表字体与界面一致，深色主题。
【插件 YAML 敌人】可选：plugins/enemies/*.yaml 需自行放置；JSON 敌人插件无需额外依赖。
"""


def stage_release_folder(
    release_root: Path,
    *,
    project_root: Path,
    repo_root: Path,
) -> None:
    """
    在已生成的 exe 目录旁写入游戏 JSON 与许可文件。

    ``release_root`` 通常为 ``dist/终末地伤害计算器/``（与 exe 同级）。
    """
    release_root.mkdir(parents=True, exist_ok=True)
    for dest_rel, src_rel in RELEASE_DATA_FILES:
        src = project_root / src_rel
        if not src.is_file():
            raise FileNotFoundError(f"缺少游戏数据源文件: {src}")
        dest = release_root / dest_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)

    for dest_rel, src_rel in LICENSE_FILES:
        src = repo_root / src_rel
        if not src.is_file():
            raise FileNotFoundError(f"缺少许可文件: {src}")
        shutil.copy2(src, release_root / dest_rel)

    exe_version, package_version = _read_release_versions()
    (release_root / RELEASE_README_NAME).write_text(
        _release_readme_text(
            exe_version=exe_version,
            package_version=package_version,
        ),
        encoding="utf-8",
    )


def _read_release_versions() -> tuple[str, str]:
    """读取当前打包使用的 EXE / 包版本（与 GUI 标题一致）。"""
    from please_read_me import get_exe_version, get_version

    return get_exe_version(), get_version()


def release_dir_from_dist(dist_dir: Path) -> Path:
    """``dist/`` 下发布根目录（含 exe 与外挂数据）。"""
    return dist_dir / RELEASE_APP_NAME
