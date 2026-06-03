#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""

多游戏伤害计算框架 - 项目说明文档



项目简介：

    本工具是基于 PySide6 和 FastAPI 开发的多游戏伤害计算框架。

    支持《明日方舟：终末地》《明日方舟》等多款游戏的伤害计算，
    提供桌面 GUI（PySide6）和 Web 版（React + FastAPI）两种使用方式。

    玩家可以通过选择角色/武器/装备，查看属性面板和乘区数据，
    帮助优化配装和战斗策略。



功能特性：

    1. 多游戏支持：终末地、明日方舟等，框架可扩展
    2. 角色/武器/装备选择：支持按类型、星级筛选
    3. 属性展示：角色属性列与装备属性列分列显示等级曲线明细
    4. 乘区计算：实时计算能力乘区、能力值加成、攻击力等数据
    5. Web 版：浏览器访问，无需安装
    6. 适配器市场：可发现和下载社区适配器包

"""



# ==================== 版本信息（只在此处修改） ====================

# _VERSION：项目与 pip 包版本（pyproject.toml 通过 dynamic 读取，勿在别处重复写死）

# _EXE_VERSION：窗口标题与 dist/*.exe 用户可见版本（仅重新打包 exe 时手动修改；改后须重新 build.py）

_VERSION = "3.19.13"

_EXE_VERSION = "0.6.0-beta"

# ==============================================================



# ==================== GitHub 上传流程（必读） ====================

UPLOAD_WORKFLOW = """

GitHub 上传与版本号（仓库根目录执行: python github_upload_module.py）



1. 版本分工

   - _VERSION：上传脚本在有「业务改动」并 push 成功时自动递增（第三位 +1 为默认）。commit 消息使用此版本。

   - _EXE_VERSION：GUI 窗口标题与 exe 版本号，仅你手动修改。**git 标签使用此版本**（`--tag` 时）。

   - 第一位 MAJOR：永远只在下方 _VERSION 行手动改，脚本不会动。



2. 何时自动 bump _VERSION

   - 会：本次有新的业务文件改动，将产生新 commit 并推送到远程。

   - 不会：仅补推已有 commit、与远程已同步无改动、或使用了 --no-bump。



3. 升级幅度

   - 默认 Patch：1.8.1 → 1.8.2（第三位 +1）

   - Minor（大改动）：1.8.1 → 1.9.0（第二位 +1，第三位归零）

     · 交互：运行脚本时输入 M 或 minor

     · 非交互：python github_upload_module.py --minor

   - 不涨版本：python github_upload_module.py --no-bump



4. 提交说明（临时写在「本文件最下面」）

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



# ==================== 项目结构文档（自动生成） ====================

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
    │   ├── frontend/                 #   React + TypeScript + MUI 前端
    │   ├── backend/                  #   FastAPI 后端（API 路由、计算服务）
    │   └── hub/                      #   适配器市场目录

    ├── scripts/                      # 入口脚本（统一 _path_setup 模式）
    │   ├── main.py                   #   终末地桌面计算器
    │   ├── main_arknights.py         #   明日方舟桌面计算器
    │   ├── main_designer.py          #   适配器包数据设计器
    │   ├── main_build.py             #   打包构建
    │   ├── main_pack_designer.py     #   适配器包设计器
    │   ├── main_launcher.py          #   框架启动器
    │   ├── launcher.pyw              #   图形化启动器
    │   └── 启动本地服务器.bat        #   Web 本地服务器

    ├── tools/                        # 开发工具脚本
    │   ├── bwiki_scout/              #   BWIKI 数据采集
    │   ├── designer/                 #   适配器包设计工具
    │   ├── endfield_scripts/         #   终末地数据维护
    │   ├── data_pipeline/            #   数据管线（CSV/JSON 读取、校验）
    │   ├── data_sandbox/             #   数据沙箱验证
    │   ├── audit/                    #   审计脚本
    │   ├── ocr/                      #   截图识别工具
    │   └── ...（代码检查、打包发布等）

    ├── docs/                         # 项目文档（20+ 文档）
    ├── installer/                    # NSIS 安装程序构建
    ├── release_bundle/               # 发布打包配置
    ├── utils/                        # 通用工具模块
    ├── resources/                    # 资源文件（捐赠码等）
    │
    ├── README.md / CONTEXT.md        # 门面与领域术语
    ├── LICENSE / DATA_LICENSE        # 软件与数据许可
    ├── AGENTS.md                     # Agent 技能配置
    └── .github/                      # CI 工作流与 Issue 模板

"""



USAGE_INFO = """

使用方法：

    【桌面计算器】

        python scripts/main.py               # 终末地伤害计算器
        python scripts/main_arknights.py      # 明日方舟伤害计算器
        python scripts/launcher.pyw           # 图形化启动器（选择游戏）

    【Web 版】

        python web/run_local.py               # 启动本地 Web 服务
        或双击 scripts/启动本地服务器.bat
        然后浏览器打开 http://localhost:8000

    【数据设计器】

        python scripts/main_designer.py       # 适配器包数据设计
        python scripts/main_pack_designer.py  # 适配器包打包设计

    【打包构建】

        python scripts/main_build.py --target local-backend   # 本地 exe
        python scripts/main_build.py --help                   # 查看所有目标

    【测试】

        python -m pytest framework/tests/ games/endfield/tests/ games/arknights/tests/ -q

    【安装依赖】

        pip install -e ".[dev]"               # 安装所有开发依赖



技术栈：

    - Python 3.10+
    - PySide6（桌面 GUI 框架）
    - FastAPI + React/TypeScript + MUI（Web 前后端）
    - JSON（游戏数据存储）
    - PyInstaller（桌面打包工具）
    - pytest（测试框架）

"""



FORMULA_INFO = """

伤害计算公式：

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





def get_version() -> str:
    """获取项目版本号。"""
    return _VERSION





def get_exe_version() -> str:
    """获取 EXE 版本号。"""
    return _EXE_VERSION





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





import sys  # noqa: E402
from pathlib import Path  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _path_setup import ensure_root  # noqa: E402
ensure_root()

if __name__ == "__main__":

    show_help()

# --- UPLOAD_SUMMARY ---
# TITLE: 更新 6 处文件
# BODY:
# - 修改 scripts/please_read_me.py
# - 修改 tools/generator/templates.py
# - 修改 web/backend/api/generator.py
# - 变更 web/frontend/src/api/generator.ts
# - 变更 web/frontend/src/pages/AIFormulaDialog.tsx
# - 变更 web/frontend/src/pages/GeneratorPage.tsx
# --- END UPLOAD_SUMMARY ---
