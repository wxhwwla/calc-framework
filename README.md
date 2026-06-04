# Calc Framework — 通用伤害计算框架

> 通用伤害计算框架 · 目前支持《明日方舟：终末地》与《明日方舟》（Arknights）
>
> **Web 端（已部署）**：[wxhwwla.pythonanywhere.com](https://wxhwwla.pythonanywhere.com) · 部署指南：[docs/PythonAnywhere-部署指南.md](docs/PythonAnywhere-部署指南.md)

## 文档分层

| 层级 | 文件 | 适合谁 |
|------|------|--------|
| **门面（本页）** | 仓库根 `README.md` | 第一次打开仓库、GitHub 首页 |
| **详细开发** | [`games/endfield/README.md`](games/endfield/README.md) | 安装、GUI、测试、API、数据格式 |
| **操作速查** | [`docs/操作指令集.md`](docs/操作指令集.md) | 日常命令与 `[根]` / `[工具]` / `[包]` 目录约定 |
| **文档索引** | [`docs/README.md`](docs/README.md) | `docs/` 下各文件用途 |
| **领域术语** | [`CONTEXT.md`](CONTEXT.md) | Issue、测试、文档统一用语 |
| **算法说明** | [`docs/算法与架构.md`](docs/算法与架构.md) | 公式与架构细节 |
| **许可与合规** | [`docs/数据来源与许可.md`](docs/数据来源与许可.md) | 软件/数据双许可、典型情形 |

## 目录约定

| 名称 | 路径 | 典型操作 |
|------|------|----------|
| **仓库根** `[根]` | 本目录 | `github_upload_module.py`、`github_download_module.py`、`CONTEXT.md`、许可文件 |
| **通用框架** `[框架]` | [`framework/`](framework/) | `calc-framework` 独立 pip 包：DAG 引擎 + 数据引擎 + 声明式 UI + 布局编辑器 |
| **Web 版** `[Web]` | [`web/`](web/) | React + FastAPI 完整 Web 应用（三个 PySide6 GUI 的 Web 版） |
| **维护工具** `[工具]` | [`tools/`](tools/README.md) | BWIKI 侦察（`tools/bwiki_scout/`）、审计脚本（`tools/audit/`） |
| **人类文档** | [`docs/`](docs/README.md) | 操作指令集、许可说明、算法与架构 |
| **Python 包** `[包]` | `games/endfield/` | `main.py`、`pytest`、`build.py`、包内 `scripts/`（反推、seed） |

### 仓库顶层一览

```
[根]/
├── framework/                    # [框架] 通用计算框架 calc-framework
├── web/                          # [Web] React + FastAPI 前端
│   ├── backend/                  #   FastAPI 后端（/api/*）
│   ├── frontend/                 #   React 前端（三个 GUI 的 Web 版）
│   └── hub/                      #   Calc Hub 静态主页
├── games/                        # [包] 游戏适配包
│   ├── endfield/                  #   终末地伤害计算器（产品代码与测试）
│   └── arknights/                 #   明日方舟伤害计算适配包（DAG + API + 测试）
├── docs/                         # 操作指令集、许可、算法说明
├── tools/                        # [工具] 仓库级维护（非包内 scripts）
├── legacy/                       # 遗留脚本，不参与日常流程
├── .github/                      # CI、Issue 表单模板（Bug / 功能建议）
├── .agents/                      # Cursor Agent 技能
├── github_upload_module.py
├── github_download_module.py
├── git_backup/                   # Minor 上传前 .git 本地快照（snapshots/ 不纳入 Git）
├── LICENSE · DATA_LICENSE · CONTEXT.md · CONTRIBUTING.md · AGENTS.md
└── .github/                      # CI 与 Issue 模板
```

IDE 配置目录（`.idea/`、`.trae/`、`.vscode/`）仅本机使用，已在 `.gitignore` 中忽略。

## 快速开始

### 推荐：使用启动器选择游戏

```powershell
# [根] 统一启动器 — 自动发现已安装的游戏适配包
python scripts/main_launcher.py

# 或双击 bat 文件
scripts\启动.bat
```

启动器会列出所有可用的游戏，点击即可启动对应的桌面计算器。

### 直接启动

```powershell
# [包] 终末地计算器
cd games/endfield
pip install -e ".[dev]"
python main.py
```

```powershell
# [根] 明日方舟桌面 GUI
python scripts/main_arknights.py
```

```powershell
# [根] 开发者工具箱（数据设计、图编辑器、调试器、AI 生成等）
python scripts/main_dev_toolkit.py
scripts\启动.bat
```

### 发布与上传

```powershell
# [根] 推送 GitHub（版本号由脚本维护）
python github_upload_module.py
```

更多命令（测试、打包、SSH、拉取覆盖本地）见 [`docs/操作指令集.md`](docs/操作指令集.md)。

## 功能概览

### 终末地伤害计算器

- 角色 / 武器 / 装备选择；**高级页**含全量遍历、**固定配装 0–4**、多技能次数；全量可按单技能或**手动次数加权总伤**排序（实验）
- 确认选择后刷新右侧乘区（能力、攻击力等）
- 角色 / 武器 / **装备** JSON；全量搜索导出至 **`search_output/`**（开发或 exe 同级，非 C 盘临时目录）
- 公式反推与录入脚本；BWIKI 装备同步
- GUI「数据来源与许可」：软件 AGPL / 数据许可说明与链接
  - 高级页「工具与分享」（「更多设置」折叠内）：配装预设、操作日志、计算历史、伤害仪表盘（见 [操作指令集 §6.1](docs/操作指令集.md)）
  - BWIKI 数据侦察与同步（`tools/bwiki_scout/`：拉取缓存、对比报告；可选 `--apply` 以 Wiki 为准更新 JSON/seed，见 [操作指令集 §9](docs/操作指令集.md)）

### 明日方舟（Arknights）伤害计算

支持原始《明日方舟》（非终末地）的伤害计算，通过框架适配器系统实现：

- **数据爬取**：`tools/arknights_scout/` — BWIKI 爬虫，全量解析 420+ 干员（星级/职业/基础属性/技能/天赋/潜能/模组）
- **游戏适配包**：`framework/adapters/arknights/` — 28 属性 + 5 自定义函数 + 51 节点 DAG 计算图
- **伤害公式**：物理（`max(ATK×倍率-DEF, ATK×倍率×5%)×(1+伤害加成)`）、法术（`ATK×倍率×(1-RES/100)×(1+伤害加成)`）、真实伤害
- **Web API**：`/api/arknights/` — 3 个端点（干员列表/详情/计算）
- **测试覆盖**：37 个 pytest（含真实数据集成测试）

### 计算框架（通用）

- **跨品类适配**：通过 `framework/adapters/` 下的命名空间包自动发现，已支持 endfield（终末地）、arknights（明日方舟）、card_rpg/fps/moba（验证用玩具适配器）

## Web 版

三个 PySide6 GUI 的 Web 移植版（React + FastAPI），采用声明式同步策略：

| Web 版 | 对应 PySide6 GUI | 路由 |
|--------|-----------------|------|
| 伤害计算器 | `main.py` | `/` |
| 数据设计器 | `main_designer.py` | `/designer` |
| 配置包设计器 | `main_pack_designer.py` | `/pack-designer` |

**同步机制**：`layout.json`/`attr_schema.json`/计算引擎/数据文件共享同一份，Web 通过 FastAPI API 调用。

```powershell
# 启动 Web 后端
cd web/backend && pip install -r requirements.txt && uvicorn main:app --reload --port 8002

# 启动 Web 前端（新终端）
cd web/frontend && npm install && npm run dev
```

详见 [`docs/操作指令集.md`](docs/操作指令集.md) §1.7 和 [`docs/项目目标.md`](docs/项目目标.md) §P4。

细节与布局说明见 [**详细 README**](games/endfield/README.md)。

## 反馈与 Issue

| 方式 | 说明 |
|------|------|
| **GitHub Issues** | 仓库 **Issues → New issue** → 选 **Bug 报告** 或 **功能建议**（`.github/ISSUE_TEMPLATE/`） |
| **模板字段** | 描述、复现步骤、期望行为、OS / Python / 项目版本；Bug 默认标签 `needs-triage` |
| **命令行** | `gh issue create`（需 `gh auth login`）；见 [`docs/操作指令集.md`](docs/操作指令集.md) §1.3 |
| **协作约定** | Agent / 维护者见 [`docs/agents/issue-tracker.md`](docs/agents/issue-tracker.md)、[`triage-labels.md`](docs/agents/triage-labels.md) |
| **测试覆盖率** | [![CI](https://github.com/wxhwwla/calc-framework/actions/workflows/ci.yml/badge.svg)](https://github.com/wxhwwla/calc-framework/actions/workflows/ci.yml) + `pytest-cov`（门槛 **57%**→80%，含 GUI 集成测） |

## 社区与交流

| 方式 | 说明 |
|------|------|
| **[GitHub Issues]** | Bug 报告 / 功能建议（推荐，可追踪） |
| **[GitHub Discussions]** | 技术讨论 / 问题求助 |
| **QQ 群** | `1040157567`（建设中） |
| **Discord** | 邀请链接建设中 |

欢迎 Star 和 Fork！如果你觉得这个工具有用，请给仓库点个 ⭐。

[GitHub Issues]: https://github.com/wxhwwla/calc-framework/issues
[GitHub Discussions]: https://github.com/wxhwwla/calc-framework/discussions

## 许可证与数据来源

| 内容 | 说明 |
|------|------|
| **本软件** | **AGPL-3.0**（默认）或书面 **商业许可** → [`LICENSE`](LICENSE) |
| **游戏数据** | 单独许可 → [`DATA_LICENSE`](DATA_LICENSE)（**商用不可用本仓库数据**） |
| **完整说明** | [`docs/数据来源与许可.md`](docs/数据来源与许可.md)（含典型情形对照） |
| **商业洽谈** | [`docs/商业许可要点.md`](docs/商业许可要点.md)（提纲，非合同） |
| **发布自检** | [`docs/合规自查清单.md`](docs/合规自查清单.md) |
| **第三方声明** | [`NOTICES.md`](NOTICES.md) |

使用或分发即视为接受相应许可。GUI「数据来源与许可」可查看简略版并打开链接。
