# 全面审查第五批：生成器操作符与 AI 嵌套 JSON 实现计划

> **面向 AI 代理的工作者：** 使用 executing-plans；每项先 RED 后 GREEN。禁止代理直接 git add/commit/push。

**目标：** 修复 A-11，使 Web 生成器操作符与引擎互通，AI 返回的完整嵌套 JSON 不再被截断。

**架构：** API 输入模型把现有 UI 操作符别名归一为引擎协议；AI JSON 使用 `json.JSONDecoder.raw_decode` 在候选起始位置解析，直接支持嵌套对象、数组、字符串和 Markdown 前缀，不使用正则截取对象。

**技术栈：** FastAPI、Pydantic、React/TypeScript、pytest、Vitest。

**规格：** `docs/项目全面审查记录.md` A-11。

## 全局约束

- 保留 UI 和 API 的旧别名，同时输出引擎已有的 `+ - * / condition`。
- 不增加 JSON 解析依赖；非对象、无 JSON、无效 JSON 继续返回可读 502。
- 不记录 AI 密钥；外部 AI 请求只在测试中替换，真实解析和响应模型保持执行。

## 审查重点（Review Focus）

- 所有 UI 别名都必须映射，生成的 DAG 节点应能被引擎直接求值。
- 嵌套对象/数组、代码围栏、前后说明文字不得丢失顶层 variables/formula_steps/outputs。
- 无效 JSON 或 JSON 数组不得被误当作有效 AI 配方。

---

### 任务 1：生成器操作符协议

- [x] 在 `web/backend/tests/contracts/` 增加真实 `/api/generator/generate` 测试，发送 `multiply`/`cond`，解析返回 DAG 并断言 `*`/`condition`。
- [x] 确认旧实现生成缺 binary/condition 节点或请求失败。
- [x] 在 `web/backend/api/generator.py::FormulaStep` 归一 `add/subtract/multiply/divide/cond`。
- [x] 运行生成器契约、Web 后端和前端测试。

### 任务 2：AI 嵌套 JSON 解析

- [x] 增加模拟外部 AI、真实 `/api/generator/ai/parse` 的嵌套 JSON 测试，覆盖代码围栏和前后说明；另测无效/非对象输入。
- [x] 确认旧正则丢失顶层数据并失败。
- [x] 用 JSONDecoder 实现对象提取，保留现有错误文案和验证警告。
- [x] 运行定向测试、Pyright、Ruff 和完整回归；更新审查文档。

## 完成记录（2026-11-25）

- CI 类型错误在本机和 N150 均修复到 0 errors / 0 warnings。
- 生成器契约最终 8 passed；独立审查的 JSON 内层提升问题已 RED→GREEN 修复。
- 本机 Web 后端 262 passed / 2 skipped，工具链 249 passed，Pyright/Ruff/布局/链接/OpenAPI 通过。
- 延后的 Minor：永久测试中参数化五种别名并逐一执行 DAG 求值；审查者已实测当前实现全部正确。
- 本批尚未上传，待最终远程复验和 GitHub Actions 检查。
- N150 最终 Web 后端 262 passed / 2 skipped，Pyright 0 errors / 0 warnings。
- 审查记录已写入 `docs/项目全面审查记录.md` §10；上传后需读取新 GitHub Actions 状态。
