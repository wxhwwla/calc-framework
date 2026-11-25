# 全面审查第四批：通用搜索续跑、超时与进度实现计划

> **面向 AI 代理的工作者：** 使用 executing-plans 逐任务实现；每项先 RED 后 GREEN。项目禁止代理直接 git add/commit/push。

**目标：** 修复 A-05/A-06，使通用搜索续跑恢复历史 TopN、进度包含已跳过项，并让 `max_seconds` 真正停止后续任务提交。

**架构：** `run_parallel` 增加可选的总候选数、进度偏移和秒数预算；`SearchRunStore` 用 JSON 保存通用结果，`SearchEngine` 提供可覆盖的安全序列化接缝。续跑时先把历史结果放入 TopN，再评估未完成候选；写结果与 processed 在同一 SQLite 事务中提交。

**技术栈：** Python 3.12、SQLite、ThreadPoolExecutor、pytest。

**规格：** `docs/项目全面审查记录.md` A-05、A-06。

## 全局约束

- 公共 API 只增加可选参数，不改变现有默认行为。
- JSON 只接受可安全序列化的数据；不支持的游戏结果必须覆盖序列化方法，不使用 pickle。
- 超时是协作式取消：停止新提交并取消尚未开始的 future，不承诺强杀正在运行的评估。
- 不提交、不上传、不提升版本；最终由用户调用上传脚本。

## 审查重点（Review Focus）

- 续跑恢复的历史高分不得因本轮低分而丢失；序列化错误不得把候选标为已完成。
- `max_seconds<=0` 必须在首项前停止；运行中任务只能协作结束，metadata 必须可区分超时完成与正常完成。
- 续跑进度总数保持原候选总数，processed 从 skipped 开始；空 pending 也要返回历史 TopN。
- 多线程完成回调不得重复写键或破坏 TopN 容量。

---

### 任务 1：并行执行器的总进度与时间预算

**文件：**
- 修改：`framework/src/calc_framework/search/parallel.py`
- 修改：`framework/src/calc_framework/search/engine.py`
- 测试：`framework/tests/search/test_parallel.py`、`framework/tests/search/test_engine_extra.py`

- [x] 写 `run_parallel(total_candidates=20, processed_offset=10)` 进度测试，断言最后 `processed=20,total=20`；写 `max_seconds=0` 与短任务超时测试。
- [x] 运行定向测试，确认旧实现因未知参数 FAIL。
- [x] 为 `run_parallel` 增加 `total_candidates: int | None = None`、`processed_offset: int = 0`、`max_seconds: float | None = None`；deadline 到期时调用 cancel、取消 pending futures，并停止继续提交。
- [x] 在内存和持久化引擎路径传入总量；持久化路径偏移为 skipped，metadata 增加 `deadline_exceeded`。
- [x] 运行 `python -m pytest framework/tests/search -q`，预期全绿。

### 任务 2：通用续跑恢复 TopN

**文件：**
- 修改：`framework/src/calc_framework/search/persist.py`
- 修改：`framework/src/calc_framework/search/engine.py`
- 测试：`framework/tests/search/test_persist.py`、`framework/tests/search/test_engine_extra.py`

- [x] 写两轮同签名测试：第一轮只处理部分候选，第二轮从同库恢复后必须包含历史最高分且不超过 top_n；空 pending 同样覆盖。
- [x] 写结果序列化/反序列化接缝测试，使用非 JSON 默认结果时由子类覆盖 `serialize_result`/`deserialize_result`；写持久化失败不误标 processed 的既有路径回归。
- [x] 在 store schema 增加独立的 `result_scores(signature,combo_key,score,payload)`（避免游戏侧 `scores` 表冲突），实现批量原子写入和按 signature 读取；旧库通过 `CREATE TABLE IF NOT EXISTS` 自动升级。
- [x] 在 engine 增加默认可覆盖的 JSON 结果序列化方法；`_on_result` 缓冲 `(key,score,payload)` 并批量写入，开始前把历史结果 offer 给 tracker。
- [x] 运行 `python -m pytest framework/tests/search -q`，预期全绿；再跑 Framework 全套。

### 任务 3：记录与整体验证

- [x] 更新 `docs/项目全面审查记录.md` A-05/A-06、`docs/错误集.md`、`docs/会话接续手册.md` 和本计划。
- [x] 运行 Framework、终末地、方舟、工具、Web 后端、前端完整测试及 Ruff/布局/链接/OpenAPI 门禁。
- [x] 独立审查本批 diff；Critical/Important 必须 RED→GREEN 修复并复验。
