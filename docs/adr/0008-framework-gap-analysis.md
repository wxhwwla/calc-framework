# ADR-0008：框架差距分析 — 六大核心模块评估

**状态**：已批准  
**日期**：2026-05-28  
**决策者**：维护者  
**影响范围**：整个 `framework/` + `endfield_damage_calculator/` + 后续路线

---

## 1. 说明

本文档对照一位外部评估者对「通用计算框架」六大核心模块的打分，逐一校验当前代码事实，
修正误判项，确认真实缺口，并将缺口排入后续开发路线。

> 评估原文标记为「用户评估」，代码事实标记为「代码实况」。修正后的分数反映实际现状。

---

## 2. 核心计算引擎

**用户评估：60%**  
**修正后：70%**

### 已完成（代码实况）

- DAG 引擎（`framework/src/calc_framework/dag/`）：9 种节点类型（const/var/unary/binary/condition/expr/user_input/call），拓扑排序，AST 沙箱，子图展开
- **乘区顺序和伤害公式已是可配置的**：公式定义在 `endfield_full.dag.json`，改变乘区顺序、增删乘区、修改计算公式**无需改代码**，只需编辑 JSON
- 计算核心与游戏业务逻辑在目录级别分离（`framework/` vs `endfield_damage_calculator/`）

### 用户误判说明

> 用户说「乘区顺序、伤害类型只能改代码，不能配」

→ 这是**代码事实之外的误判**。当前的 DAG JSON 本身就是外部配置文件。修改 `endfield_full.dag.json` 即可重新排列 15 乘区、添加或删除乘区节点、修改公式表达式。这正是"可配置"。

### 真实缺口

| 缺口 | 严重程度 | 说明 |
|------|---------|------|
| ~~无自定义算法扩展接口~~ | ✅ **已解决** | `sandbox.register_function()` + `AdapterPackage` 自动加载 + 终末地适配器注册示例（clamp/lerp/percent_of） |
| 无异常伤害/持续伤害预置模板 | 🟡 中 | DAG 引擎本身可以表达 DoT，但没有开箱即用的预置子图模板 |
| 无分步调试/断点求值 | 🟡 中 | 求值全量一次性完成，无法在中间节点设断点观察 |

---

## 3. 数据配置层

**用户评估：30%**  
**修正后：65%**

### 已完成（代码实况）

- **统一配置规范**已存在：[ADR-0005](file:///e:/endfield_damage_calculator/docs/adr/0005-data-schema-design.md) 定义了四层数据契约（EntitySchema / SkillSchema / SegmentSchema），`tools/data_pipeline/schema.py` 中有 TypedDict 定义
- **游戏配置包隔离**已存在：[ADR-0003](file:///e:/endfield_damage_calculator/docs/adr/0003-generic-calc-framework.md) §6.1 定义适配包目录结构，[ADR-0006](file:///e:/endfield_damage_calculator/docs/adr/0006-calcpack-and-designer.md) 定义 `.calcpack` ZIP 打包格式
- **配置校验**已存在：`tools/data_pipeline/validators/schema_check.py` 检查必填字段、标签合法性、段完整性
- **版本管理**基础存在：`meta.json` 中的 `schema_version` 和 `version` 字段

### 用户误判说明

> 用户说「无统一配置规范」「无游戏配置包隔离」「无配置校验」

→ 三项均为**误判**。四层数据契约、适配包目录结构和 schema_check 已经全面覆盖这些需求。

### 真实缺口

| 缺口 | 严重程度 | 说明 |
|------|---------|------|
| 不支持热加载 | 🔴 高 | 切换游戏/数据需要重启程序，没有运行时热切换 |
| 配置版本兼容机制 | 🟡 中 | 虽然有 version 字段，但没有版本迁移/兼容代码 |
| 无配置迁移工具（跨版本） | 🟡 中 | data_pipeline 只能从旧 JSON/CSV 迁移到当前版本，不能从 v1 schema 迁移到 v2 |

---

## 4. 接口 / 适配层

**用户评估：20%**  
**修正后：55%**

### 已完成（代码实况）

- **通用适配器接口已存在**：
  - `calc_framework.data.loader.DataContextLoader` — 抽象基类（ABC）
  - `calc_framework.config.adapter.AdapterPackage` — 加载 meta.json → DAGService
  - `EndfieldContextLoader` — 具体实现，`build_context()` 将终末地 raw data → 标准 DataContext
- **数据解析通用层已存在**：
  - `tools/data_pipeline/` 完整 ETL 工具链：readers（CSV/JSON）→ transformers（`from_legacy_endfield`、`to_standard`）→ validators（`schema_check`）
  - 四层标准 schema 作为数据交换格式

### 用户误判说明

> 用户说「无通用适配器接口」「无数据解析通用层」

→ 两项均为**误判**。`DataContextLoader` 正是为跨游戏适配设计的通用接口；`tools/data_pipeline/` 提供了解析通用层。

### 真实缺口

| 缺口 | 严重程度 | 说明 |
|------|---------|------|
| 无对外公开 API 文档 | 🟡 中 | 框架模块无 Sphinx/ReadTheDocs 文档，使用者需读源码 |
| 无适配器示例/模板 | 🟡 中 | 没有「三步接入新游戏」的样板代码 |
| 无适配器注册/发现机制 | 🟢 低 | 目前硬引用 `EndfieldContextLoader`，无惰性注册 |

---

## 5. UI 渲染层

**用户评估：40%**  
**修正后：55%**

### 已完成（代码实况）

- `ComputeSheet`（`framework/src/calc_framework/ui/compute_sheet.py`）：**根据 layout.json + DAG variables 声明自动渲染输入控件**，非硬编码
- `infer_control()`（`controls.py`）：根据变量类型（float/int/bool/str）和 min/max 自动推断控件类型（slider/spinbox/switch/dropdown）
- `theme.json`（ADR-0006 §2.4）：可配置字体/色板/间距
- 框架内**零终末地素材引用**

### 用户误判说明

> 用户说「UI 控件硬编码（角色选择、技能面板写死结构）」「不支持根据配置自动渲染」

→ 这是**对终末地 GUI 和框架 ComputeSheet 的混淆**。终末地主 GUI（`gui_design/`）确实手写了角色/技能面板，但那属于**游戏业务层**。框架的 `ComputeSheet` **已经**支持根据配置自动渲染——这正是其设计目标。用户实际在使用终末地 GUI 而非 ComputeSheet。

### 真实缺口

| 缺口 | 严重程度 | 说明 |
|------|---------|------|
| ComputeSheet 未接入主线 GUI | 🔴 高 | Phase 2 待做任务 |
| 无响应式布局 | 🟡 中 | 当前使用固定 QGridLayout，不处理窗口缩放 |
| 无 `user_input` 控件的 widget 自定义映射表 | 🟢 低 | 当前通过 `ui_control` 字段透传，无全局注册表 |
| 无多主题实时切换 | 🟢 低 | theme.json 在加载时读取，运行时不可换肤 |

---

## 6. 扩展功能（OCR / 导入 / 多游戏）

**用户评估：0%**  
**修正后：0% — 完全属实**

### 真实缺口

| 缺口 | 严重程度 | 说明 |
|------|---------|------|
| 无 OCR / 截图识别 | 🔴 高 | 代码库中无任何 OCR 相关依赖或逻辑 |
| 无数据自动同步 | 🟡 中 | 无 BWIKI/PRTS 自动同步（`tools/bwiki_scout/` 是手动脚本，非自动） |
| 无多游戏切换 UI | 🟡 中 | 无游戏选择器、无适配包管理页面 |

---

## 7. 工程化 / 稳定性

**用户评估：10%**  
**修正后：40%**

### 已完成（代码实况）

- 参数校验：DAG schema 层有 `DAGCompileError`、`_validate_references`、拓扑排序检测循环依赖
- 运行时异常：`DAGRuntimeError`、`LayoutValidationError`、`AdapterError` 层次清晰
- 测试覆盖率：框架 206 测试 + 终末地包 553 测试
- **日志系统**：`calc_framework.logging` 已创建（2026-05-28），统一 `setup_logging()` + `get_logger()`，支持环境变量级别/文件配置、RotatingFileHandler。已集成到 engine/sandbox/subgraph/adapter/ComputeSheet 及部分 endfield 模块（data/loader, qt_app）

### 真实缺口

| 缺口 | 严重程度 | 说明 |
|------|---------|------|
| ~~无日志系统~~ | ✅ **已解决** | `calc_framework/logging.py` 已实现 |
| 无调试模式（分步/中间值可视化） | 🟡 中 | DAGResult 有 node_values 但无可视化展示 |
| 无框架使用文档 | 🟡 中 | ADR 作为架构文档存在，但无入门指南/API 参考 |
| 无版本兼容协议 | 🟢 低 | schema_version 声明了但无迁移代码 |

---

## 8. 修正总分汇总

| 模块 | 用户评分 | 修正评分 | 说明 |
|------|---------|---------|------|
| 核心计算引擎 | 60% | **75%** | 公式可配置 + 自定义函数注册接口已完成 |
| 数据配置层 | 30% | **65%** | 四层契约 + 适配包 + schema_check 已存在 |
| 接口/适配层 | 20% | **55%** | DataContextLoader + AdapterPackage + ETL 已存在 |
| UI 渲染层 | 40% | **55%** | ComputeSheet + infer_control + theme.json 已存在 |
| 扩展功能 | 0% | **0%** | 完全空白，属实 |
| 工程化/稳定性 | 10% | **40%** | 异常体系 + 测试 + 日志系统已存在，缺调试/文档 |

---

## 9. 后续开发优先级（基于真实缺口）

### ✅ 已完成（2026-05-28）

| 任务 | 关联缺口 | 说明 |
|------|---------|------|
| 日志系统 | 工程 #1 | `calc_framework/logging.py` — 统一 `setup_logging()` + `get_logger()`，环境变量配置，RotatingFileHandler |
| 自定义算法扩展 | 引擎 #1 | `sandbox.register_function()` + `AdapterPackage` 自动加载 + 终末地适配器注册示例 |
| 框架入门文档 | 工程 #4 | `framework/README.md` + `docs/quickstart.md` 已创建 |

### P0（阻碍依赖）

| 任务 | 关联缺口 | 预估 |
|------|---------|------|
| ~~ComputeSheet 接入主线 GUI~~ | UI #1 — Phase 2 | **已完成** |

### P1（核心能力）

| 任务 | 关联缺口 | 路径 |
|------|---------|------|
| 多游戏切换 UI | 扩展 #3 | `tools/designer/` 增加游戏选择器 |

### P2（体验完善）

| 任务 | 关联缺口 | 路径 |
|------|---------|------|
| DoT/异常伤害预置子图模板 | 引擎 #2 | `framework/src/calc_framework/dag/templates/` |
| 热加载适配包 | 数据 #1 | `framework/src/calc_framework/config/watcher.py` |
| 响应式布局 | UI #2 | `compute_sheet.py` 使用 QScrollArea + 比例布局 |
| DAG 分步调试视图 | 引擎 #3 | `framework/src/calc_framework/debug/` |

### P3（长期）

| 任务 | 关联缺口 |
|------|---------|
| OCR / 截图识别 | 扩展 #1 |
| 数据自动同步 | 扩展 #2 |
| Sphinx API 文档 | 适配 #1 |
| 版本迁移工具 | 数据 #2 |
| 多主题运行时切换 | UI #4 |
