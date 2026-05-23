# 文档目录（`docs/`）

人类可读说明，与 Cursor 用的 `.agents/`、包内代码注释分工不同。

**推荐阅读顺序**：新对话 / 换模型 → [会话接续手册.md](会话接续手册.md) → 按需 [操作指令集.md](操作指令集.md)、[CONTEXT.md](../CONTEXT.md)、[算法与架构.md](算法与架构.md)。

| 文件 | 用途 |
|------|------|
| [会话接续手册.md](会话接续手册.md) | **Agent 与长期协作**：接缝表、已完成项、勿重复工作、测试基线 |
| [操作指令集.md](操作指令集.md) | **日常首选**：`[根]` / `[工具]` / `[包]` 路径与可复制命令（含 BWIKI §9 侦察与同步） |
| [依赖说明.md](依赖说明.md) | `pyproject.toml` 运行时/开发/打包依赖、传递依赖与打包约定 |
| [数据来源与许可.md](数据来源与许可.md) | 软件 AGPL + 商业双许可、数据 `DATA_LICENSE`、典型情形 |
| [商业许可要点.md](商业许可要点.md) | 商业洽谈提纲（非合同） |
| [合规自查清单.md](合规自查清单.md) | 发布前自检 |
| [算法与架构.md](算法与架构.md) | 公式、乘区、模块结构（原根目录 `PROJECT_DOCUMENTATION.md`） |
| [MVP搜索验收说明.md](MVP搜索验收说明.md) | 全量遍历、并行线程、`search_output/` 导出、GUI/打包验收 |
| [agents/issue-tracker.md](agents/issue-tracker.md) | GitHub Issue、`gh` CLI、**Web 表单模板**（Bug / 功能建议） |
| [agents/triage-labels.md](agents/triage-labels.md) | 分拣标签：`needs-triage`、`ready-for-agent` 等 |
| [agents/domain.md](agents/domain.md) | Issue/文档与 `CONTEXT.md` 术语一致 |

仓库门面与目录树见根目录 [README.md](../README.md)；领域术语见 [CONTEXT.md](../CONTEXT.md)。
