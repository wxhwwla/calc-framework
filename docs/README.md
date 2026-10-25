# 文档目录（`docs/`）

人类可读说明，与 Cursor 用的 `.agents/`、包内代码注释分工不同。

**推荐阅读顺序**：新对话 / 换模型 → [会话接续手册.md](会话接续手册.md)（先看 **§0 代码快照**）→ [项目目标.md](项目目标.md) → 按需 [操作指令集.md](操作指令集.md)、[CONTEXT.md](../CONTEXT.md)、[算法与架构.md](算法与架构.md)。**动结构前** → [代码结构规范.md](代码结构规范.md)、[adr/0001-code-layout-constraints.md](adr/0001-code-layout-constraints.md)。

**归档**：一次性历史计划与已完成迁移方案见 [`archive/README.md`](archive/README.md)；月度接续见 `会话接续手册-2026-0x.md`。

| 文件 | 用途 |
|------|------|
| [会话接续手册.md](会话接续手册.md) | **Agent 与长期协作**：§0 实测快照、接缝表、近期已完成、勿重复工作 |
| [项目目标.md](项目目标.md) | 愿景、三层完成度、真缺口、P5 路线 |
| [操作指令集.md](操作指令集.md) | **日常首选**：`[根]` / `[工具]` / `[包]` 路径与可复制命令 |
| [**上传脚本与-pre-commit.md**](上传脚本与-pre-commit.md) | **上传 GitHub / pre-commit 排障必读** |
| [**错误集.md**](错误集.md) | Bug 记录：「问题 → 原因 → 修复 → 涉及文件」 |
| [代码结构规范.md](代码结构规范.md) | 目录 ≤20、文件 ≤400 行；docstring 分级 |
| [adr/0001-code-layout-constraints.md](adr/0001-code-layout-constraints.md) | 结构约束 ADR |
| [GUI使用说明.md](GUI使用说明.md) | PySide6 GUI 操作详解 |
| [依赖说明.md](依赖说明.md) | 运行时/开发/打包依赖 |
| [数据来源与许可.md](数据来源与许可.md) | AGPL + 数据许可 |
| [算法与架构.md](算法与架构.md) | 公式、乘区、模块结构 |
| [MVP搜索验收说明.md](MVP搜索验收说明.md) | 全量遍历验收 |
| [框架适配新游戏指南.md](框架适配新游戏指南.md) | 新游戏适配 |
| [制造游戏计算器完整流程.md](制造游戏计算器完整流程.md) | 端到端制造流程 |
| [plans/improvement-roadmap.md](plans/improvement-roadmap.md) | **活**改进账本（与代码对齐） |
| [plans/rust-full-batch-plan.md](plans/rust-full-batch-plan.md) | Rust 全批量 / 搜索性能 |
| [plans/i18n-desktop.md](plans/i18n-desktop.md) | Desktop i18n 架构与键表 |
| [plans/phase-4-ecosystem-plan.md](plans/phase-4-ecosystem-plan.md) | Phase 4 生态（含 4.5/4.6 开放项） |
| [archive/README.md](archive/README.md) | 已归档历史文档索引 |

**JSON 数据契约**：[`CONTEXT.md`](../CONTEXT.md) + [`games/endfield/README.md`](../games/endfield/README.md) + `tests/test_game_data_contract.py`。

| agents/ | 用途 |
|---------|------|
| [agents/issue-tracker.md](agents/issue-tracker.md) | GitHub Issue / `gh` |
| [agents/triage-labels.md](agents/triage-labels.md) | 分拣标签 |
| [agents/domain.md](agents/domain.md) | 与 CONTEXT 术语一致 |

仓库门面见根目录 [README_zh.md](../README_zh.md)。
