# Phase 4 Step 4.6 — 明日方舟 Web 扩展范围说明

> 创建：2026-06-17  
> 状态：**不实施** — 待产品明确需求后单独立项

---

## 与 parity 计划的关系

[`arknights-desktop-web-parity.md`](arknights-desktop-web-parity.md) 已收尾：**桌面与 Web 伤害计算对齐**（干员属性、技能、敌人参数等）。

**本 Step 不在 parity 范围内**，指终末地式能力在 Web 上的扩展，例如：

- 全量配装搜索 / 固定配装遍历
- Web 端复杂 loadout 编辑器与 MVP 导出
- 与终末地 `endfield/search` 同等级别的搜索 API

---

## 若未来立项时的候选交付物

| 项 | 说明 | 依赖 |
|----|------|------|
| Web 配装 schema | 与桌面 preset JSON 或 EntitySchema 对齐的 HTTP 请求体 | ADR-0023 数据路径 |
| `POST /api/arknights/search` | 干员/模组组合搜索（若产品需要） | 搜索引擎抽象、算力/超时策略 |
| 前端页面 | 方舟专用搜索/配装 UI | 与现有 Web 路由拆分 |

---

## 当前决策

- **Phase 4 不在此会话/里程碑内实现 4.6**
- 有明确产品需求时再开 Issue / 里程碑，并更新本文件为实施计划

---

## 相关文档

- [`phase-4-ecosystem-plan.md`](phase-4-ecosystem-plan.md)
- [`docs/会话接续手册.md`](../会话接续手册.md) §4.189
- [`docs/plans/improvement-roadmap.md`](improvement-roadmap.md)
