# 文档目录（`docs/`）

人类可读说明，与 Cursor 用的 `.agents/`、包内代码注释分工不同。

**推荐阅读顺序**：新对话 / 换模型 → [会话接续手册.md](会话接续手册.md) → 按需 [操作指令集.md](操作指令集.md)、[CONTEXT.md](../CONTEXT.md)、[算法与架构.md](算法与架构.md)。**动结构前** → [代码结构规范.md](代码结构规范.md)、[adr/0001-code-layout-constraints.md](adr/0001-code-layout-constraints.md)。

| 文件 | 用途 |
|------|------|
| [代码结构规范.md](代码结构规范.md) | **目录 ≤20（目标 ≤15）、文件 ≤400 行**；docstring 分级要求；迁移 backlog、PR 自检 |
| [adr/0001-code-layout-constraints.md](adr/0001-code-layout-constraints.md) | 结构约束 ADR（Agent/评审依据） |
| [代码规范-ruff修复模式.md](代码规范-ruff修复模式.md) | **ruff + pyright 规范修复模式**：E501/F401/N806/E741/`**kwargs`拆包/QDoubleSpinBox stub |
| [会话接续手册.md](会话接续手册.md) | **Agent 与长期协作**：接缝表、已完成项、勿重复工作、测试基线 |
| [操作指令集.md](操作指令集.md) | **日常首选**：`[根]` / `[工具]` / `[包]` 路径与可复制命令（含 BWIKI §9 侦察与同步） |
| [**上传脚本与-pre-commit.md**](上传脚本与-pre-commit.md) | **上传 GitHub / pre-commit 排障必读**：两轮 hook、`_version` 标记、stash、CRLF、`--no-bump` |
| [GUI使用说明.md](GUI使用说明.md) | **PySide6 GUI 操作详解**：双页签布局、全量搜索、异常矩阵、预设系统、工具与分享 |
| [依赖说明.md](依赖说明.md) | `pyproject.toml` 运行时/开发/打包依赖、传递依赖与打包约定 |
| [数据来源与许可.md](数据来源与许可.md) | 软件 AGPL + 商业双许可、数据 `DATA_LICENSE`、典型情形 |
| [商业许可要点.md](商业许可要点.md) | 商业洽谈提纲（非合同） |
| [合规自查清单.md](合规自查清单.md) | 发布前自检 |
| [算法与架构.md](算法与架构.md) | 公式、乘区、模块结构 |
| [MVP搜索验收说明.md](MVP搜索验收说明.md) | 全量遍历、并行线程、`search_output/` 导出、GUI/打包验收 |
| [**错误集.md**](错误集.md) | **Bug 记录**：「问题 → 原因 → 修复 → 涉及文件 → 检查清单」 |

**JSON 数据契约**（角色/武器/预设字段）：[`CONTEXT.md`](../CONTEXT.md) 术语表 + [`games/endfield/README.md`](../games/endfield/README.md)「数据格式」节 + `tests/test_game_data_contract.py`。
| [agents/issue-tracker.md](agents/issue-tracker.md) | GitHub Issue、`gh` CLI、**Web 表单模板**（Bug / 功能建议） |
| [agents/triage-labels.md](agents/triage-labels.md) | 分拣标签：`needs-triage`、`ready-for-agent` 等 |
| [agents/domain.md](agents/domain.md) | Issue/文档与 `CONTEXT.md` 术语一致 |

仓库门面与目录树见根目录 [README.md](../README.md)；领域术语见 [CONTEXT.md](../CONTEXT.md)。
