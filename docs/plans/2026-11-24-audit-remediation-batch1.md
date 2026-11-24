# 全面审查第一批修复实现计划

> **面向 AI 代理的工作者：** 使用 executing-plans 逐任务实现。所有生产变更必须先写失败测试；步骤用复选框跟踪。项目禁止代理直接 git add/commit/push，因此任务末尾只做验证，不执行提交。

**目标：** 修复审查中已确认、会阻断使用或造成错误结果的六个独立切片，并恢复真实入口验证。

**架构：** 保留现有公共 API 和模块边界。终末地沿用共享 CalculatorShell 与 ComputeSheet；通用搜索在执行器内只维护一次 TopN，并显式聚合失败；Web 计算复用完整装备数据而非精简选择目录；Viewer 和设计器只做最小防御与一致性修复。

**技术栈：** Python 3.10+、PySide6、pytest、React、TypeScript、FastAPI、Vitest/Cypress。

**规格：** `docs/项目全面审查记录.md` 的 A-01～A-04、A-07、A-14、A-16、A-29，以及 CI RUF100。

## 全局约束

- 最小 diff，不顺带重构；公共接口保持兼容。
- 每个行为先 RED 后 GREEN，测试通过公共入口验证。
- 终末地必须补生产 `EndfieldApp` 窗口确认测试，不能只测带补属性的桩。
- 不改变 Wiki 数据；审查发现的「不知归」差异另行处理。
- 不上传、不提交、不提升版本。
- 修改文件不得超过现有布局基线；必要时优先复用辅助函数。

## 审查重点（Review Focus）

- 非默认敌防/抗性必须在终末地首次确认时生效，不得被控件默认值覆盖。
- 搜索任一候选失败时不得写成 completed，失败候选不得被标为已处理。
- 同一搜索结果只能进入 TopN 一次；续跑不能产生重复项。
- 固定装备必须保留属性词条、效果和套装效果，选择目录仍可保持精简。
- 空数组实体字段应忽略；真实空数据不得使 Viewer 崩溃。

---

### 任务 1：恢复终末地生产 ComputeSheet 链

**文件：**
- 修改：`games/endfield/gui/endfield_shell.py`（区域容器公开访问或挂载辅助）
- 修改：`games/endfield/gui/endfield_actions.py:220-267`
- 测试：`games/endfield/tests/gui_design/app/test_refresh_compute_sheet_context.py`
- 测试：`games/endfield/tests/gui_design/app/` 下现有生产窗口测试文件

- [x] 写生产窗口测试：创建真实 `EndfieldApp(embedded=True)`，执行确认，断言无异常、ComputeSheet 已挂载且结果与伤害快照一致。
- [x] 写首次非默认敌参测试：在控件渲染前以非默认敌防/抗性求值，断言首次结果采用 Loadout 值。
- [x] 运行测试，确认当前代码分别因缺属性和首次默认值失败。
- [x] 在 shell 已创建的乘区区域上建立明确挂载点；先访问 `compute_sheet.widget` 完成控件构建，再首次求值；只初始化一次。
- [x] 跑相关测试并执行源码窗口确认，确认不再出现 `_compute_sheet_widget` 错误且乘区表有结果。

### 任务 2：通用搜索去重并传播失败状态

**文件：**
- 修改：`framework/src/calc_framework/search/parallel.py`
- 修改：`framework/src/calc_framework/search/engine.py`
- 测试：`framework/tests/search/test_engine_extra.py`
- 测试：`framework/tests/search/` 下现有 parallel 测试

- [x] 写测试：3 个平方结果在 `top_n=10` 下严格为 `(9,4,1)`，不使用 set 掩盖重复。
- [x] 写测试：候选 2 抛异常时，结果包含成功项，运行状态不是 completed，processed 不包含失败键，metadata 含失败数。
- [x] 运行并确认当前实现分别返回重复项和 completed。
- [x] 从并行执行器移除重复 tracker.offer；让执行器向引擎报告失败，不在失败时调用成功回调；引擎据此写 failed 状态和失败计数。
- [x] 保持既有取消语义，跑 Framework search 全部测试。

### 任务 3：Web 固定装备使用完整修正数据

**文件：**
- 修改：`web/frontend/src/pages/ComputePage.tsx`
- 修改：`web/frontend/src/api/` 下既有数据封装（仅在需要时）
- 测试：`web/frontend/src/` 下现有 loadout/context 测试或新增同目录测试

- [x] 写测试：精简目录用于固定选择时，求值 payload 中对应装备仍包含 `属性词条`、`效果`、`三件套效果`。
- [x] 运行确认当前 payload 丢失这些字段。
- [x] 在实体加载边界按名称补全固定装备，保持 `/api/search/catalog` 精简；避免把完整装备库重复塞进每次求值。
- [x] 跑 Vitest、TypeScript、ESLint；用真实 API 选择带词条装备比较结果。

### 任务 4：修明日方舟桌面明细键与连发展示

**文件：**
- 修改：`games/arknights/gui/ArknightsDamageApp.py`
- 测试：`games/arknights/tests/test_damage_app_shell_layout.py` 或同目录现有展示测试

- [x] 写真实窗口测试：确认后基础攻击力等于实际干员 atk，最终攻击力与明细一致。
- [x] 写连发测试：DAG 已给合计口径时，明细不得再次除以 hit_count。
- [x] 运行确认当前实现失败。
- [x] 统一读取 DAG 实际键并删除重复归一，不改核心伤害公式。
- [x] 跑明日方舟测试并截图复核非零基础攻击力。

### 任务 5：Viewer 忽略空数值数组

**文件：**
- 修改：`framework/src/calc_framework/ui/viewer_pack_utils.py:328-337`
- 测试：`framework/tests/ui/` 下现有 viewer context 测试

- [x] 写公共函数测试：`{'空曲线': []}` 被忽略，非空曲线仍按 1-indexed level 取值。
- [x] 运行确认空数组触发 IndexError。
- [x] 在数值列表分支增加非空判断，保持其他字段行为不变。
- [x] 跑 Framework UI 相关测试。

### 任务 6：恢复审计测试与 CI lint 可信度

**文件：**
- 修改：`scripts/auto_test/desktop_test.py`
- 修改：`web/backend/tests/test_healthcheck.py:23`
- 测试：`tools/tests/test_auto_test_packaged_process.py` 或现有桌面脚本契约测试

- [x] 用当前实际“计算/高级”标签和确认流程更新桌面源码测试，不再只验证启动；设计器入口缺失不得被记为通过。
- [x] 删除 unused `noqa`，运行 CI 同款 Ruff。
- [x] 执行桌面脚本，要求所有配置场景真实执行并通过；若发现新生产故障，记录并转入对应任务，不放宽断言。

## 第一批验收

- 上述测试全部经过 RED→GREEN。
- Framework、终末地、明日方舟、Web 后端和前端相关测试通过。
- 真实终末地源码窗口确认成功；明日方舟明细非零且一致。
- Web 固定装备业务测试和真实计算对照通过。
- CI Ruff、链接、OpenAPI、布局门禁通过。
- 更新 `docs/项目全面审查记录.md` 状态、`docs/错误集.md` 和接续手册；未覆盖项保持开放，不借测试数量宣称全部完成。
