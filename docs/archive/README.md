# 文档归档（`docs/archive/`）

> **归档日期**：2026-10-24  
> **原则**：已完成的一次性计划、迁移方案、历史对照表移入此处；日常接续仍读 [`../会话接续手册.md`](../会话接续手册.md) 与 [`../项目目标.md`](../项目目标.md)。

## 目录

| 路径 | 内容 |
|------|------|
| [`historical/`](historical/) | 已完成迁移/解耦/对齐快照、NGA 对照、手册摘录 |
| [`plans/`](plans/) | 已完成或已过时效的 `docs/plans/*` 实施计划 |

## 月度会话归档（仍在 `docs/` 根下，便于链接）

| 文件 | 范围 |
|------|------|
| [`../会话接续手册-2026-05.md`](../会话接续手册-2026-05.md) | ≤2026-05 |
| [`../会话接续手册-2026-06.md`](../会话接续手册-2026-06.md) | 2026-06 |
| [`../会话接续手册-2026-07.md`](../会话接续手册-2026-07.md) | 2026-07 |

## 本批移入清单（2026-10-24）

### historical/

| 原路径 | 现路径 | 原因 |
|--------|--------|------|
| `docs/migration-pyside6.md` | [`historical/migration-pyside6.md`](historical/migration-pyside6.md) | PySide6 迁移已完成（2026-05） |
| `docs/decouple-plan.md` | [`historical/decouple-plan.md`](historical/decouple-plan.md) | 解耦计划文内状态 ✅ 完成 |
| `docs/框架对齐分析.md` | [`historical/框架对齐分析.md`](historical/框架对齐分析.md) | 2026-06 对齐快照，非活文档 |
| `docs/nga-46094556-*.md` | [`historical/nga-46094556-终末地机制对照与待办.md`](historical/nga-46094556-终末地机制对照与待办.md) | 旧对照/待办；实现以代码与错误集为准 |

### plans/

| 原路径 | 现路径 | 原因 |
|--------|--------|------|
| `plans/gitignore-and-attrs-cleanup.md` | [`plans/gitignore-and-attrs-cleanup.md`](plans/gitignore-and-attrs-cleanup.md) | 一次性清理已完成 |
| `plans/documentation-improvement-plan.md` | [`plans/documentation-improvement-plan.md`](plans/documentation-improvement-plan.md) | 2026-06 计划阶段文档，长期未跟进 |
| `plans/defect-audit-verification-2026-06-17.md` | [`plans/defect-audit-verification-2026-06-17.md`](plans/defect-audit-verification-2026-06-17.md) | 外部审计核实记录（历史） |
| `plans/缺陷审计报告2-验证与修复计划.md` | [`plans/缺陷审计报告2-验证与修复计划.md`](plans/缺陷审计报告2-验证与修复计划.md) | 同上；条目见 `错误集.md` |
| `plans/game-architecture-migration-plan.md` | [`plans/game-architecture-migration-plan.md`](plans/game-architecture-migration-plan.md) | 迁移步骤多已落地；ADR-0023 仍为规范源 |

原路径保留**短跳转 stub**（避免旧链接 404）。
