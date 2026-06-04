# ADR-0001：代码目录与文件规模约束

**状态**：已采纳（2026-06-03 修订：目录宽度 10→20）  
**日期**：2026-05-25（初版）；2026-06-03（目录宽度修订）  
**决策者**：维护者（Grill 会话）

## 背景

`endfield_damage_calculator` 包内模块曾长期平铺（尤其 `gui_design/`、`calculation/`、`tests/`），单文件过长，同一目录下文件过多，导航与评审成本高，AI/人类都难以建立稳定 mental model。

## 决策

### 1. 目录宽度（硬约束）

- **每个目录的直接子项（文件 + 子文件夹）≤ 20（硬顶）；目标 ≤ 15。**
- 适用范围：**整个 Python 包** `endfield_damage_calculator/`（含 `tests/`、`scripts/` 等），以及仓库内**手写维护**的 `tools/` 子目录（不含 `.venv`、`dist`、`__pycache__` 等生成物）。
- 超过 **20** 时必须**拆子目录**或**合并**相关模块；禁止继续在同一层「堆新文件」。处于 **16–20** 时应规划拆分，避免继续膨胀。
- 子目录命名应反映**领域或职责**，而非技术细节堆砌（优先 `gui/panels/`、`calculation/search/plan/`，避免 `utils2/`）。

### 2. 文件长度（软约束 + 硬上限）

| 类型 | 目标 | 硬上限 |
|------|------|--------|
| 业务 / GUI / 计算 `.py` | **≤ 400 行**（含 docstring） | **> 500 行禁止合并 PR**（除非 ADR 豁免） |
| 测试 `.py` | ≤ 400 行 | > 500 行应拆 fixture 或分文件 |
| 数据 seed / 录入脚本 | 允许更长 | 须拆「数据块」与「逻辑函数」；逻辑部分仍 ≤ 400 行 |

超长文件优先：**按职责拆模块** > mixin > 纯函数辅助模块；禁止「再复制粘贴一个大函数进已有大文件」。

### 3. 分层与导航（目标形态）

生产代码按**领域子包**组织，而非按历史文件名平铺：

```
endfield_damage_calculator/
  calculation/          # 伤害与搜索核心（继续收拢子包）
  gui_design/           # GUI：presentation / app / panels / controls / shell
  data/                 # 加载与门面
  tests/                # 镜像生产结构：tests/calculation/、tests/gui_design/…
  scripts/              # 包内 CLI / 录入（按 character|weapon|equipment 分子目录）
  …
```

**tests/** 必须与生产结构**同构或镜像**（例如 `tests/gui_design/shell/`），禁止在 `tests/` 根目录无节制增加单文件。

### 4. Import 与迁移

- **2026-05-25 已选方案 B（断代）**：根路径 **re-export stub 已全部删除**；全仓库 import 直接走子包路径（如 `gui_design.app.loadout_state`、`calculation.search.plan.controller`）。
- 新代码**必须** import 子包路径；**禁止**恢复根 stub 或新增 `_compat/` 薄层（除非 ADR 修订）。
- Mock / patch 目标必须是**实现所在模块**（如 `gui_design.shell.app_selection.*`、`calculation.search.run.runner.*`），不是已删除的旧路径。

### 5. 评审与 Agent

- 新 PR / Agent 任务：变更后不得使任一目录 **> 20 子项**（目标 ≤ 15）；不得使业务文件 **> 500 行**。
- 人类与 Agent 开工前读 [`docs/代码结构规范.md`](../代码结构规范.md) 与本文。

## 后果

- **正面**：目录可扫视、模块边界清晰、测试与生产对齐、利于并行开发。
- **负面**：大规模迁移一次性 diff 大；断代后旧 import 路径**不再可用**。
- **当前违规（2026-05-25 基线）**：`tests/` 已镜像分层；`gui_design/` 根约 9 项、`calculation/` 根约 10 项；多文件仍 >400 行（见结构规范 §4）。

## 相关文档

- [`docs/代码结构规范.md`](../代码结构规范.md) — 操作细则与迁移清单  
- [`docs/会话接续手册.md`](../会话接续手册.md) — 接缝与已完成迁移  
- [`CONTEXT.md`](../../CONTEXT.md) — 术语表「工程」节
