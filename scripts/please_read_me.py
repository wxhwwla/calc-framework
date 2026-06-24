#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
多游戏伤害计算框架 - 项目说明文档

💡 版本常量已迁移到 `scripts/_version.py`，此文件为项目文档入口。

项目简介：

    本工具是基于 PySide6 和 FastAPI 开发的多游戏伤害计算框架。

    支持《明日方舟：终末地》《明日方舟》等多款游戏的伤害计算，
    提供桌面 GUI（PySide6）和 Web 版（React + FastAPI）两种使用方式。

    玩家可以通过选择角色/武器/装备，查看属性面板和乘区数据，
    帮助优化配装和战斗策略。

    【AI 计算器生成器】支持通过可视化表单或自然语言（AI 解析）快速生成
    新游戏的计算适配器，无需编程即可创建伤害计算器。
    【BWIKI 数据采集】内置 Wiki 爬虫，可从终末地 BWIKI 自动同步角色/
    武器/装备数据。
    【适配器市场】可发现、下载、分享社区适配器包（calcpack）。


功能特性：

    1. 多游戏支持：终末地、明日方舟等，框架可扩展
    2. 角色/武器/装备选择：支持按类型、星级筛选
    3. 属性展示：角色属性列与装备属性列分列显示等级曲线明细
    4. 乘区计算：实时计算能力乘区、能力值加成、攻击力等数据
    5. AI 计算器生成器：4 步向导（选模板→填信息→生成→导出），支持 AI 自然语言公式解析
    6. BWIKI 数据采集：侦察/解析/同步三阶段工具链，自动同步终末地数据
    7. Web 版：浏览器访问，支持 PWA 离线使用、移动端自适应
    8. 适配器市场：可发现和下载社区适配器包（calcpack）
    9. Docker 部署：一键容器化部署 Web 服务
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripts._path_setup import ensure_root

ensure_root()

from _version import _EXE_VERSION, _VERSION, get_exe_version, get_version

__all__ = [
    "FORMULA_INFO",
    "PROJECT_STRUCTURE",
    "UPLOAD_WORKFLOW",
    "USAGE_INFO",
    "VERSION_INFO",
    "_EXE_VERSION",
    "_VERSION",
    "get_exe_version",
    "get_full_intro",
    "get_version",
    "show_help",
]

# ==============================================================

UPLOAD_WORKFLOW = """

GitHub 上传与版本号（仓库根目录执行: python github_upload_module.py）

版本常量定义在 scripts/_version.py 中。/


1. 版本分工

   - _VERSION：上传脚本在有「业务改动」并 push 成功时自动递增（第三位 +1 为默认）。commit 消息使用此版本。

   - _EXE_VERSION：GUI 窗口标题与 exe 版本号，仅你手动修改。**git 标签使用此版本**（`--tag` 时）。

   - 第一位 MAJOR：永远只在 _version.py 中手动修改，脚本不会动。


2. 何时自动 bump _VERSION

   - 会：本次有新的业务文件改动，将产生新 commit 并推送到远程。

   - 不会：仅补推已有 commit、与远程已同步无改动、或使用了 --no-bump。


3. 升级幅度

   - 默认 Patch：1.8.1 → 1.8.2（第三位 +1）

   - Minor（大改动）：1.8.1 → 1.9.0（第二位 +1，第三位归零）

     · 交互：运行脚本时输入 M 或 minor

     · 非交互：python github_upload_module.py --minor

   - 不涨版本：python github_upload_module.py --no-bump


4. 提交说明（临时写在 _version.py 最下面）

   - 上传前：脚本根据 git 改动自动生成 # --- UPLOAD_SUMMARY --- 块（勿手删标记行）。

   - commit 消息格式：

       v3.11.21: 一句话标题

       - 修改 xxx
       - 更新 weapons.json ...

   - push 成功后：脚本删除该总结块（_VERSION 保留）。

   - push 失败：总结块保留，版本不回滚；修好网络后可只 push 或 --no-bump 再传。


5. 发布标签（Tag）

   - `python github_upload_module.py --tag` 会创建并推送 git 标签。

   - 标签版本使用 **`_EXE_VERSION`**（如 `v0.6.0-beta`），触发 GitHub Actions 自动构建发行版。

   - 确保标签被 SSH 签名（需配置签名密钥并添加到 GitHub Signing keys）。


6. 常用命令

   python github_upload_module.py
   python github_upload_module.py --minor
   python github_upload_module.py --no-bump
   python github_upload_module.py --tag         # 正常推送 + 创建发行版标签
   python github_upload_module.py --no-bump --tag   # 不 bump 版本 + 创建标签


7. 提交签名（推荐，GitHub Verified）

   - 若已配置 commit.gpgsign 和 SSH 签名密钥，commit 和 tag 均会自动签名。

   - 未配置时脚本会打印设置提示；见 docs/操作指令集.md §1.5。


8. 从远程覆盖本地（危险，勿误点）

   - 仓库根：python github_download_module.py

   - 须完整输入确认词「覆盖本地」才会执行；会 reset --hard 并 clean 未跟踪文件。


许可与数据：LICENSE（软件）、DATA_LICENSE（游戏 JSON）、docs/数据来源与许可.md

完整操作指令（GUI、数据、测试、打包、GitHub、BWIKI、Cursor）见仓库根目录：

   docs/操作指令集.md

"""

# ==============================================================

PROJECT_STRUCTURE = """

项目结构：

    ├── framework/                    # 计算框架核心库
    │   ├── src/calc_framework/       #   DAG 引擎、UI（ComputeSheet）、编辑器、搜索、逆推
    │   ├── adapters/                 #   游戏适配器定义
    │   │   ├── endfield/             #     终末地计算适配
    │   │   ├── arknights/            #     明日方舟计算适配
    │   │   ├── fps/                  #     通用 FPS 示例适配
    │   │   ├── moba/                 #     通用 MOBA 示例适配
    │   │   └── card_rpg/             #     卡牌 RPG 示例适配
    │   └── tests/                    #     框架测试

    ├── games/                        # 游戏适配包（薄包装、数据、GUI）
    │   ├── endfield/                 #   明日方舟：终末地 桌面计算器
    │   └── arknights/                #   明日方舟 桌面计算器

    ├── web/                          # Web 前后端
    │   ├── frontend/                 #   React + TypeScript + MUI 前端（含 PWA 离线支持）
    │   ├── backend/                  #   FastAPI 后端（API 路由、计算服务、生成器 API）
    │   ├── hub/                      #   适配器市场目录
    │   ├── scripts/                  #   部署脚本（PythonAnywhere 等）
    │   └── Dockerfile                #   容器化部署

    ├── scripts/                      # 入口脚本（统一 _path_setup 模式）
    │   ├── _version.py               #   版本常量（唯一源头）
    │   ├── main_launcher.py          #   框架启动器（推荐入口）
    │   ├── main_dev_toolkit.py       #   开发者工具箱
    │   ├── main_build.py             #   打包构建
    │   └── ...（其他入口）

    ├── tools/                        # 开发工具脚本
    ├── docs/                         # 项目文档（30+ 文档）
    ├── installer/                    # NSIS 安装程序构建
    └── ...

"""

USAGE_INFO = """

使用方法：

    【桌面计算器】

        python scripts/启动.bat 游戏       # 启动器（选择游戏，推荐）
        python scripts/main_launcher.py    # 同上

    【开发者工具箱】

        python scripts/启动.bat 工具箱        # 数据设计/图编辑/调试/AI生成
        python scripts/main_dev_toolkit.py    # 同上

    【AI 计算器生成器】

        python tools/export_sample_calcpacks.py --list-templates  # 列出模板
        python tools/export_sample_calcpacks.py --from-template simple --name "我的游戏"  # 从模板导出

    【Web 版】

        python web/run_local.py            # 启动本地 Web 服务
        或 启动.bat 服务器
        然后浏览器打开 http://localhost:8180
        （支持 PWA 离线安装到桌面）

    【Docker 部署】

        docker-compose up -d               # 启动 Web 服务（端口 8000）

    【BWIKI 数据采集】

        python tools/bwiki_scout/scout.py                   # 侦察（拉取 Wiki 数据）
        python tools/bwiki_scout/sync_all.py --apply         # 同步到本地 JSON

    【打包构建】

        python scripts/main_build.py --target local-backend  # 本地 exe
        python scripts/main_build.py --help                  # 查看所有目标

    【测试】

        python -m pytest framework/tests/ games/endfield/tests/ games/arknights/tests/ -q

    【安装依赖】

        pip install -e ".[dev]"              # 安装所有开发依赖


技术栈：

    - Python 3.10+
    - PySide6（桌面 GUI 框架）
    - FastAPI + React/TypeScript + MUI（Web 前后端）
    - JSON（游戏数据存储）
    - PyInstaller（桌面打包工具）
    - pytest（测试框架）
    - Docker（容器化部署，可选）
    - OpenAI 兼容 API（AI 公式解析，可选）

"""

FORMULA_INFO = """

伤害计算公式（终末地示例）：

    最终攻击力 = 中间攻击力 × (能力值加成 + 1)

    中间攻击力 = 攻击加成攻击力 + 附加攻击力+

    攻击加成攻击力 = 基础攻击力 × 攻击力+乘区

    能力值加成 = 主能力×0.005 + 副能力×0.002

"""

VERSION_INFO = f"""

版本信息：

    项目版本: v{_VERSION}

    EXE版本:  v{_EXE_VERSION}

"""


def get_full_intro() -> str:
    """获取完整的项目介绍文档。"""
    return f"""

多游戏伤害计算框架 v{_VERSION}

{"=" * 50}

{PROJECT_STRUCTURE}

{USAGE_INFO}

{FORMULA_INFO}

{VERSION_INFO}

{UPLOAD_WORKFLOW}

    """


def show_help() -> None:
    """显示项目帮助信息。"""
    print(f"""

============================================================

多游戏伤害计算框架 v{_VERSION}

============================================================

{PROJECT_STRUCTURE}

{USAGE_INFO}

{FORMULA_INFO}

{VERSION_INFO}

{UPLOAD_WORKFLOW}

    """)


if __name__ == "__main__":
    show_help()
