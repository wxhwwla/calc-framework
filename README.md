# 终末地伤害计算小工具

> 《明日方舟：终末地》配装与乘区辅助工具（CustomTkinter GUI）

## 文档分层

| 层级 | 文件 | 适合谁 |
|------|------|--------|
| **门面（本页）** | 仓库根 `README.md` | 第一次打开仓库、GitHub 首页 |
| **详细开发** | [`endfield_damage_calculator/README.md`](endfield_damage_calculator/README.md) | 安装、GUI、测试、API、数据格式 |
| **操作速查** | [`docs/操作指令集.md`](docs/操作指令集.md) | 日常命令与 `[根]` / `[工具]` / `[包]` 目录约定 |
| **文档索引** | [`docs/README.md`](docs/README.md) | `docs/` 下各文件用途 |
| **领域术语** | [`CONTEXT.md`](CONTEXT.md) | Issue、测试、文档统一用语 |
| **算法说明** | [`docs/算法与架构.md`](docs/算法与架构.md) | 公式与架构细节（根目录 `PROJECT_DOCUMENTATION.md` 为跳转） |
| **许可与合规** | [`docs/数据来源与许可.md`](docs/数据来源与许可.md) | 软件/数据双许可、典型情形 |

## 目录约定

| 名称 | 路径 | 典型操作 |
|------|------|----------|
| **仓库根** `[根]` | 本目录 | `github_upload_module.py`、`github_download_module.py`、`CONTEXT.md`、许可文件 |
| **维护工具** `[工具]` | [`tools/`](tools/README.md) | BWIKI 侦察（`tools/bwiki_scout/`）、审计脚本（`tools/audit/`） |
| **人类文档** | [`docs/`](docs/README.md) | 操作指令集、许可说明、算法与架构 |
| **Python 包** `[包]` | `endfield_damage_calculator/` | `main.py`、`pytest`、`build.py`、包内 `scripts/`（反推、seed） |

### 仓库顶层一览

```
[根]/
├── endfield_damage_calculator/   # [包] 产品代码与测试
├── docs/                         # 操作指令集、许可、算法说明
├── tools/                        # [工具] 仓库级维护（非包内 scripts）
├── legacy/                       # 遗留脚本，不参与日常流程
├── .github/                      # CI（勿随意改路径）
├── .agents/                      # Cursor Agent 技能
├── github_upload_module.py
├── github_download_module.py
├── LICENSE · DATA_LICENSE · CONTEXT.md
└── PROJECT_DOCUMENTATION.md      # 跳转 → docs/算法与架构.md
```

IDE 配置目录（`.idea/`、`.trae/`、`.vscode/`）仅本机使用，已在 `.gitignore` 中忽略。

## 快速开始

```powershell
# [包] 安装并启动 GUI
cd endfield_damage_calculator
pip install -e ".[dev]"
python main.py
```

```powershell
# [根] 推送 GitHub（版本号由脚本维护，见包内 please_read_me.py）
python github_upload_module.py
```

更多命令（测试、打包、SSH、拉取覆盖本地）见 [`docs/操作指令集.md`](docs/操作指令集.md)。

## 功能概览

- 角色 / 武器选择，分列展示属性与技能倍率；**计算与搜索**列含单段伤害、全量遍历（实验）
- 确认选择后刷新右侧乘区（能力、攻击力等）
- 角色 / 武器 / **装备** JSON；全量搜索导出至 **`search_output/`**（开发或 exe 同级，非 C 盘临时目录）
- 公式反推与录入脚本；BWIKI 装备同步
- GUI「数据来源与许可」：软件 AGPL / 数据许可说明与链接
- BWIKI 数据侦察与同步（`tools/bwiki_scout/`：拉取缓存、对比报告；可选 `--apply` 以 Wiki 为准更新 JSON/seed，见 [操作指令集 §9](docs/操作指令集.md)）

细节与布局说明见 [**详细 README**](endfield_damage_calculator/README.md)。

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
