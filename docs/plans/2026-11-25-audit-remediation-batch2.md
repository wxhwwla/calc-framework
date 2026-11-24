# 全面审查第二批修复实现计划

> **面向 AI 代理的工作者：** 使用 executing-plans 逐任务实现。所有生产变更先写失败测试；项目禁止代理直接 git add/commit/push，任务末尾只做验证。

**目标：** 修复 ETL、公开入口、浏览器搜索续跑、Web 状态恢复和 DAG 编辑器中的剩余确定性缺陷。

**架构：** 保持现有 API 与目录结构。ETL 的只读校验不经过转换；Web 通过统一实体加载与状态恢复边界修复；DAG 编辑器以 Zustand 为唯一事实源；搜索续跑从已有 scores 恢复 TopN，并完整签名计算输入。

**技术栈：** Python、FastAPI、pytest、React、TypeScript、Zustand、sql.js、Vitest/Cypress。

**规格：** `docs/项目全面审查记录.md` A-08、A-09、A-12、A-22、A-25、A-28。

## 全局约束

- 最小 diff，公共接口向后兼容，不顺带重构。
- 每项先 RED 后 GREEN；测试验证真实行为，不检查源文本。
- 标准 JSON 只读校验不得改变实体技能或字段。
- 搜索签名改变后不得复用旧进度；已完成任务续跑仍返回历史 TopN。
- 不上传、不提交、不提升版本。

## 审查重点（Review Focus）

- 标准实体含嵌套技能时，校验输入和输出语义完全一致。
- 多行 stacked CSV 必须按名称合并，数值 0/1 不得静默变 bool。
- 已完成搜索再次运行不得返回空 TopN；仅改敌参必须产生新签名。
- 导入、OCR、历史恢复不得混用新名称与旧实体。
- DAG 编辑、删边和导出必须无损保留 variables/outputs/subgraphs。

---

### 任务 1：ETL 只读校验、stacked 合并与数值类型

**文件：** `tools/data_pipeline/cli.py`、`transformers/to_standard.py`、对应测试。
- [x] 标准 JSON 含 3 技能时 `--validate` 保留技能并通过。
- [x] stacked CSV 同名实体合并技能，非 bool 字段的 0/1 保持 int。
- [x] 先运行确认旧行为失败，再实现只读分支、stacked 转换和键感知类型推断。

### 任务 2：数据设计器适配器映射与 publish 入口

**文件：** `web/backend/api/data.py`、`framework/src/calc_framework/publish/__main__.py`、对应测试。
- [x] 为两个游戏的真实 meta.name 写 DAG 验证测试，拒绝旧短名。
- [x] 为 `python -m calc_framework.publish --help` 写子进程测试，并验证 catalog 可生成。
- [x] 实现映射修正和最小 argparse CLI。

### 任务 3：浏览器搜索恢复 TopN 与完整签名

**文件：** `web/frontend/src/calc/search/*`、对应测试。
- [x] 已完成小搜索再次运行返回历史 TopN；仅改敌防产生不同签名。
- [x] 从 searchResumeDb 恢复 scores 到新 tracker，并补齐敌参、暴击、武器技能和技能等级签名。
- [x] 跑 Vitest 与真实小型搜索。

### 任务 4：预设、OCR 与历史的完整状态恢复

**文件：** `web/frontend/src/pages/ComputePage.tsx`、`components/calculator/CharacterSelector.tsx`、相关 API/测试。
- [x] 测试新名称不会与旧实体混用，等级/敌参/次数完整恢复。
- [x] 统一按名称加载角色武器详情的边界，再应用预设、OCR 和历史状态。
- [x] 跑 Vitest、TypeScript、ESLint 与真实页面恢复。

### 任务 5：Web DAG 编辑器单一状态与无损导出

**文件：** `web/frontend/src/components/dag/DagEditorCanvas.tsx`、`store/editorStore.ts`、`pages/EditorPage.tsx`、测试。
- [x] 测试渲染、节点编辑、删边后画布与 store 一致，导出保留 variables/outputs/subgraphs。
- [x] 以 store 为唯一事实源同步 React Flow；修真实 Endfield 示例名。
- [x] 跑 Vitest、TypeScript、ESLint 和 Cypress 编辑器语义回归。

## 第二批验收

- 每项 RED→GREEN，相关 Python/TS 套件通过。
- ETL 标准 JSON 校验和 stacked CSV 实测正确。
- publish CLI、DAG 验证、搜索续跑、状态恢复、DAG 导出实测通过。
- 更新审查记录、错误集与接续手册，剩余项继续开放。
