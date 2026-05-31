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



BuildTarget = Literal["calculator", "designer", "pack-designer", "local-backend"]



TARGET_APP_NAMES: dict[BuildTarget, str] = {

    "calculator": "终末地伤害计算器",

    "designer": "数据设计器",

    "pack-designer": "配置包设计器",

    "local-backend": "终末地本地搜索服务器",

}



TARGET_ENTRIES: dict[BuildTarget, str] = {

    "calculator": "main.py",

    "designer": "main_designer.py",

    "pack-designer": "main_pack_designer.py",

    "local-backend": "web/backend/run_packaged_main.py",

}



RELEASE_DATA_FILES: tuple[tuple[str, str], ...] = (

    (CHARACTERS_JSON_PATH, CHARACTERS_JSON_PATH),

    (WEAPONS_JSON_PATH, WEAPONS_JSON_PATH),

    (EQUIPMENTS_JSON_PATH, EQUIPMENTS_JSON_PATH),

)



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





def _calculator_readme(exe_version: str, package_version: str) -> str:

    return f"""终末地伤害计算小工具 — 发布包说明



【版本】EXE v{exe_version}（源码包 v{package_version}）

【软件】终末地伤害计算器.exe — 见 LICENSE（AGPL-3.0 或您已取得的商业许可）

【数据】games/endfield/data/ 下 JSON — 见 DATA_LICENSE（非商业可用；商用不可用本仓库数据）



GUI 框架：PySide6（LGPL-3.0）。仪表盘：matplotlib。

可选 OCR 截图识装（tools/ocr/）：EasyOCR（Apache 2.0）、TorchVision（MIT，替代 YOLO）。



完整说明：docs/数据来源与许可.md（源码仓库）或 GUI「数据来源与许可」按钮。



分发时请保持 exe 与本目录内 JSON、许可文件相对位置不变；可单独更新 JSON 而无需重打 exe。



【全量/MVP 搜索导出】首次运行后在本文件夹下自动创建 search_output/（与 exe 同级）。

【伤害仪表盘】已内置 matplotlib（无需用户另装）。

"""





def _designer_readme(exe_version: str, package_version: str) -> str:

    return f"""数据设计器 — 发布包说明



【版本】EXE v{exe_version}（源码包 v{package_version}）

【软件】数据设计器.exe — 见 LICENSE（AGPL-3.0 或您已取得的商业许可）

【数据】games/endfield/data/ 下 JSON — 见 DATA_LICENSE（非商业可用；商用不可用本仓库数据）



GUI 框架：PySide6（LGPL-3.0）。



本工具用于角色/武器数据的公式反推与数据浏览，不包含伤害计算功能。

数据与计算器共享同一份 JSON，可放心同时使用。



分发时请保持 exe 与本目录内 JSON、许可文件相对位置不变；可单独更新 JSON 而无需重打 exe。

"""





def _pack_designer_readme(exe_version: str, package_version: str) -> str:

    return f"""配置包设计器 — 发布包说明



【版本】EXE v{exe_version}（源码包 v{package_version}）

【软件】配置包设计器.exe — 见 LICENSE（AGPL-3.0 或您已取得的商业许可）



本工具用于创建 .calcpack 配置包，包含数据录入、布局编辑、主题与导出三页签。

生成的 .calcpack 可用启动器或 CalcPackViewer 打开使用。



【三种导出方式】

1. 数据 + 布局 + 主题 → 导出 .calcpack

2. 仅布局 → 导出 layout.json

3. 设置 → 导出 DAG JSON

"""





def _local_backend_readme(exe_version: str, package_version: str) -> str:

    return f"""终末地本地搜索服务器 — 发布包说明



【版本】EXE v{exe_version}（源码包 v{package_version}）

【软件】终末地本地搜索服务器.exe — 见 LICENSE（AGPL-3.0 或您已取得的商业许可）

【数据】games/endfield/data/ 下 JSON — 见 DATA_LICENSE（非商业可用；商用不可用本仓库数据）



用途：在您本地电脑上运行全量搜索后端，与线上 Web 界面配合使用。



使用方法：

1. 双击「终末地本地搜索服务器.exe」

2. 浏览器自动打开 http://localhost:8180

3. 在本地页面中使用全量搜索（使用您电脑的 CPU/GPU 计算）

4. 关闭命令行窗口即可停止服务器



系统要求：Windows 10/11，无需安装 Python 或 Node.js。



分发时请保持 exe 与本目录内 JSON、许可文件相对位置不变；可单独更新 JSON 而无需重打 exe。

"""





def stage_release_folder(

    release_root: Path,

    *,

    project_root: Path,

    repo_root: Path,

    target: BuildTarget = "calculator",

) -> None:

    release_root.mkdir(parents=True, exist_ok=True)



    if target == "local-backend":
        # local-backend 前端 dist 已在 PyInstaller 中通过 --add-data 内嵌
        # 但仍需要游戏数据 JSON 文件在 exe 旁
        for dest_rel, src_rel in RELEASE_DATA_FILES:
            src = project_root / src_rel
            if not src.is_file():
                raise FileNotFoundError(f"缺少游戏数据源文件: {src}")
            dest = release_root / dest_rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
    elif target != "pack-designer":
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

    if target == "calculator":
        readme_fn = _calculator_readme
    elif target == "designer":
        readme_fn = _designer_readme
    elif target == "pack-designer":
        readme_fn = _pack_designer_readme
    elif target == "local-backend":
        readme_fn = _local_backend_readme
    else:
        readme_fn = _calculator_readme

    (release_root / RELEASE_README_NAME).write_text(
        readme_fn(exe_version=exe_version, package_version=package_version),
        encoding="utf-8",
    )





def _read_release_versions() -> tuple[str, str]:

    from please_read_me import get_exe_version, get_version

    return get_exe_version(), get_version()





def release_dir_from_dist(dist_dir: Path, *, target: BuildTarget = "calculator") -> Path:

    return dist_dir / target_app_name(target)
