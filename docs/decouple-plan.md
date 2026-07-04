# PySide6 解耦计划

> **目标**：将困在 PySide6 类中的业务逻辑（计算函数、数据定义、纯函数）提取为独立的纯 Python 模块，使这些逻辑可被 Web/CLI/测试复用，同时降低 GUI 层与业务逻辑的耦合度。

**创建日期**：2026-07-03
**最后更新**：2026-07-04（阶段 5 全部评估完毕，5.3/5.4 经评估决定不提取）
**状态**：✅ 全部完成（26/28 执行 + 2/2 评估后跳过）

---

## 0. 工作量评估摘要

### 总体工作量

| 维度 | 评估 |
|------|------|
| **总文件数** | 98 文件含 PySide6 import，其中 21 文件需解耦 |
| **阶段 1（已完成）** | 7 项提取，~7 个新模块，已验证 0 regression |
| **阶段 2（已完成）** | 7 项提取，~7 个新模块，中等复杂度 |
| **阶段 3（已完成）** | 5 项提取，5 个新模块（3.1–3.5 全部完成） |
| **阶段 4（已完成）** | 6 项验证+文档，CI 耦合检查已更新，回归保护扩展至 32 模块 |
| **阶段 5（完成）** | 2 项提取完成 + 2 项经评估决定不提取（纯逻辑 <18 行），~152 行 |
| **预计总轮次** | ~15 轮（阶段 1–5 主体完成） |
| **风险等级** | 低（提取模式已验证，26/28 项完成 0 regression） |

### 各阶段详细评估

| 阶段 | 任务数 | 新模块数 | 预计行数 | 复杂度 | 状态 |
|:----:|:------:|:--------:|:--------:|:------:|:----:|
| 1 | 7 | 7 | ~500 | ★☆☆ | ✅ 完成 |
| 2 | 7 | 7 | ~600 | ★★☆ | ✅ 完成 |
| 3 | 5 | 5 | ~470 | ★★☆ | ✅ 完成 |
| 4 | 5 | 1 | ~100 | ★☆☆ | ✅ 完成 |
| 5 | 4 | 2 | ~207 | ★☆☆ | 2/4 完成（边界项暂不执行） |
| **合计** | **28** | **22** | **~1877** | | **26/28 完成** |

### 阶段 2 各任务评估

| 任务 | 源文件 | 提取内容 | 新模块 | 预计行数 | 难度 |
|:----:|--------|----------|--------|:--------:|:----:|
| 2.1 | `qt_panel.py` (270行) | 四级级联过滤逻辑 | `selection_model.py` | ~80 | ★★☆ |
| 2.2 | `qt_control_dock.py` (400行) | 槽位映射+固定配装读取 | `fixed_loadout_slots.py` | ~60 | ★★☆ |
| 2.3 | `endfield_shell.py` (209行) | 武器过滤逻辑 | `weapon_filter.py` | ~40 | ★☆☆ |
| 2.4 | `qt_enemy_panel.py` (300行) | 敌方解析逻辑 | `enemy_panel_model.py` | ~50 | ★☆☆ |
| 2.5 | `qt_actions.py` (500行) | 搜索执行+数据转换 | `search_worker_logic.py` | ~120 | ★★☆ |
| 2.6 | `qt_dialogs.py` (600行) | 预设加载+对比逻辑 | `preset_compare_service.py` | ~80 | ★★☆ |
| 2.7 | `total_damage_panel.py` (200行) | 数据分组/排序/百分比 | `total_damage_display_data.py` | ~60 | ★☆☆ |

### 阶段 3 各任务评估

| 任务 | 源文件 | 提取内容 | 新模块 | 实际行数 | 难度 |
|:----:|--------|----------|--------|:--------:|:----:|
| 3.1 | `endfield_app.py` (200行) | 敌方参数状态 13 字段 | `enemy_params_state.py` | 84 | ★☆☆ |
| 3.2 | `endfield_actions.py` + `endfield_search.py` | 重复 loadout 读取模式 | `loadout_reader.py` | 126 | ★★☆ |
| 3.3 | `endfield_search.py` (300行) | 搜索编排逻辑 | `search_controller.py` | 72 | ★★☆ |
| 3.4 | `viewer_render.py` + `viewer_events.py` | context 构建+评估逻辑 | `viewer_evaluator.py` | 75 | ★★☆ |
| 3.5 | `dev_toolkit/pages.py` (500行) | 目录生成逻辑 | `adapter_creator.py` | 145 | ★☆☆ |

---

## 1. 现状分析

### 1.1 PySide6 分布统计

| 层级 | 目录 | PySide6 文件数 | 需解耦 | 说明 |
|------|------|:--------------:|:------:|------|
| **框架层** | `framework/src/calc_framework/` | 28 | 5 | `ui/` 低耦合模块 + `dev_toolkit/pages.py` |
| **终末地 GUI** | `games/endfield/gui/` | 35 | 15 | 业务逻辑困在 QWidget 方法中 |
| 明日方舟 GUI | `games/arknights/gui/` | 4 | 1 | `arknights_compute_sheet.py` 数据混合 |
| 工具层 | `tools/` | 12 | 0 | 独立 GUI 应用，不解耦 |
| 测试 | `*/tests/` | 12 | 0 | 测试需要 GUI fixture |
| 共享工具 | `utils/gui/` | 3 | 0 | 已是纯 GUI 基础设施 |
| **总计** | | **93** | **21** | |

### 1.2 耦合分类

| 类别 | 文件数 | 说明 | 解耦难度 |
|------|:------:|------|:--------:|
| **业务逻辑困在 Qt 类中** | ~15 | 计算/数据处理写在 QWidget 方法内 | ★★☆ |
| **纯数据定义困在 Qt 模块中** | ~3 | 配置字典/常量在 import PySide6 的文件里 | ★☆☆ |
| **纯函数困在 Qt 模块中** | ~3 | 无 Qt 依赖的函数在 import PySide6 的文件里 | ★☆☆ |
| **纯 GUI（接受不解耦）** | ~40 | graph_editor、viewer、launcher 等本质是 Qt 程序 | — |
| **已解耦** | ~30 | calc/、data_loading/、presentation/ 等已无 PySide6 | ✅ |

### 1.3 不解耦的模块（接受为纯 GUI）

| 模块 | 文件数 | 原因 |
|------|:------:|------|
| `framework/graph_editor/` | 13 | 每个文件都继承 QGraphics 类，本质是 Qt 图形程序 |
| `framework/ui/viewer.py` + mixins | 4 | QMainWindow + 深度 Qt 事件循环集成 |
| `framework/ui/log_widget.py` | 1 | QMetaObject.invokeMethod 跨线程日志桥接 |
| `framework/ui/launcher/window.py` | 1 | QMainWindow + 跨线程下载 |
| `framework/ui/sheet_widgets.py` | 1 | 纯 Widget 工厂，无业务逻辑可提取 |
| `framework/dag/debugger_gui.py` | 1 | 已有 try/except ImportError 保护 |
| `framework/editor/gui.py` | 1 | 已委托 LayoutEditor 管理状态 |
| `tools/designer/` 面板 | 5 | 独立 GUI 应用，被 dev_toolkit 嵌入 |
| `tools/endfield_designer/` | 5 | 独立 GUI 应用，无外部消费者 |
| `tools/ocr/label.py` | 1 | 独立标注工具 |
| `games/endfield/gui/shell/qt_factory.py` | 1 | CTk→PySide6 别名层 |
| `games/endfield/gui/shell/qt_control_dock_builders.py` | 1 | 纯 UI 构建器 |
| `games/endfield/gui/shell/qt_control_dock_widgets.py` | 1 | 纯 UI 控件 |
| `games/arknights/gui/ArknightsDamageApp.py` | 1 | 独立游戏 GUI |
| `games/arknights/gui/ArknightsApp.py` | 1 | 独立游戏 GUI |

---

## 2. 解耦目标

### 2.1 设计原则

1. **提取而非重构**：将业务逻辑从 Qt 类中提取到独立模块，Qt 类变为纯渲染器
2. **向后兼容**：旧模块通过 re-export 保持 import 路径不变
3. **最小 diff**：只提取业务逻辑，不改变 GUI 布局和交互
4. **逐阶段验证**：每阶段完成后运行全量测试，确认 0 regression

### 2.2 验收标准

| 维度 | 标准 |
|------|------|
| 逻辑可复用 | 新提取的模块可被 Web 后端/CLI/测试直接 import，无需 PySide6 |
| GUI 不退化 | `pytest games/endfield/tests/ -x` 全绿 |
| 框架不受影响 | `pytest framework/tests/ -x` 全绿 |
| 文件规模 | 新模块 ≤ 200 行，不新增目录超过 20 子项 |

---

## 3. 实施阶段

### 阶段 1：提取纯函数与数据定义 ✅ 完成

> 目标：将无 Qt 依赖的函数和数据定义从 Qt 模块中移出

- [x] **1.1** `framework/ui/sheet_evaluator.py` — 提取 `build_context()` 和 `render_html()` 到 `sheet_evaluator_core.py` ✅ 2026-07-03
- [x] **1.2** `framework/ui/theme.py` — `ThemeManager` 已是纯 Python 类，`apply_font()` 已移至 `_qt_backend.py` ✅ 2026-07-03
- [x] **1.3** `games/endfield/gui/controls/search/qt_search_browser.py` — 提取搜索历史数据层到 `search_history_data.py` ✅ 已完成
- [x] **1.4** `games/endfield/gui/endfield_actions.py` — 提取 user_input 变量定义到 `compute_sheet_variables.py` ✅ 已完成
- [x] **1.5** `games/arknights/gui/arknights_compute_sheet.py` — 提取 AK 变量定义到 `games/arknights/gui/arknights_sheet_config.py` ✅ 已完成
- [x] **1.6** `games/endfield/gui/controls/survival/qt_survival_dialog.py` — 提取生存估算逻辑到 `survival_estimator.py` ✅ 已完成
- [x] **1.7** `games/endfield/gui/shared/display_view/qt_columns.py` — 提取乘区行构建到 `zone_display_builder.py` ✅ 2026-07-03

**验收**：新模块可 `import` 成功且无 PySide6 依赖 ✅

---

### 阶段 2：提取选择与过滤模型（预计 3 轮）

> 目标：将数据级联过滤、配装映射等逻辑提取为纯 Python 模型

- [x] **2.1** `games/endfield/gui/panels/selection/qt_panel.py` — 提取四级级联过滤到 `selection_model.py` ✅ 已完成
- [x] **2.2** `games/endfield/gui/shell/qt_control_dock.py` — 提取槽位映射逻辑到 `fixed_loadout_slots.py` ✅ 已完成
- [x] **2.3** `games/endfield/gui/endfield_shell.py` — 提取武器过滤逻辑到 `weapon_filter.py` ✅ 已完成
- [x] **2.4** `games/endfield/gui/controls/enemy/qt_enemy_panel.py` — 提取敌方解析逻辑到 `enemy_panel_model.py` ✅ 已完成

- [x] **2.5** `games/endfield/gui/controls/search/qt_actions.py` — 提取搜索结果数据转换到 `search_worker_logic.py` ✅ 已完成
- [x] **2.6** `games/endfield/gui/controls/enhancement/qt_dialogs.py` — 提取预设加载+对比逻辑到 `preset_compare_service.py` ✅ 已完成
- [x] **2.7** `games/endfield/gui/presentation/total_damage_panel.py` — 已有 `total_damage_display_data.py`（预存完成）✅ 已完成

**验收**：
- 新模块可 `import` 成功且无 PySide6 依赖
- `pytest games/endfield/tests/ -x` 全绿

---

### 阶段 3：提取控制器与状态管理（预计 5 轮）

> 目标：将 GUI mixin 中的业务编排逻辑提取为可复用的控制器

- [x] **3.1** `games/endfield/gui/endfield_app.py` — 提取敌方参数状态到 `EnemyParamsState` dataclass ✅ 已完成（`gui/app/enemy_params_state.py`，84 行）
- [x] **3.2** `games/endfield/gui/endfield_actions.py` + `endfield_search.py` — 统一 loadout 读取模式 ✅ 已完成（`gui/app/loadout_reader.py`，110 行：`read_common_loadout()` + `read_dock_enemy_params()`）
- [x] **3.3** `games/endfield/gui/endfield_search.py` — 提取搜索编排逻辑到 `search_controller.py` ✅ 已完成（`gui/app/search_controller.py`，65 行：`format_search_duration()` + `should_warn_search_combinations()` + `SearchEstimateDisplay`）
- [x] **3.4** `framework/ui/viewer_render.py` + `viewer_events.py` — 提取 context 构建到 `viewer_evaluator.py` ✅ 已完成（`framework/ui/viewer_evaluator.py`，70 行：`build_viewer_context()` + `build_entity_status_text()`）
- [x] **3.5** `framework/dev_toolkit/pages.py` — 提取目录生成到 `adapter_creator.py` ✅ 已完成（`framework/dev_toolkit/adapter_creator.py`，140 行：`AdapterScaffoldConfig` + `scaffold_adapter_directory()` + `ScaffoldResult`）

**验收**：
- 新模块可 `import` 成功且无 PySide6 依赖
- `pytest games/endfield/tests/ -x` 全绿
- `pytest framework/tests/ -x` 全绿

**验收**：
- 新模块可 `import` 成功且无 PySide6 依赖
- `pytest games/endfield/tests/ -x` 全绿
- `pytest framework/tests/ -x` 全绿

---

### 阶段 4：验证与文档（预计 2 轮）

> 目标：确保解耦后所有路径正常工作

- [x] **4.1** 运行全量测试，确认 0 regression ✅ 2026-07-03（2739 passed，仅预存失败）
- [x] **4.2** 更新 `docs/会话接续手册.md` §3–§4 ✅ 2026-07-03
- [x] **4.3** 更新 `docs/decouple-plan.md` 标记完成状态 ✅ 2026-07-03
- [x] **4.4** 检查 Web 后端是否可复用新提取的模块 ✅ 2026-07-03（Web 后端暂未集成，但模块已可被 Web/CLI 直接 import）
- [x] **4.5** 编写 `tools/check_pyside6_coupling.py` ✅ 2026-07-03
- [x] **4.6** 扩展 `DECOUPLED_MODULES` 回归保护：新增 10 个已有 PySide6-free 业务逻辑模块 ✅ 2026-07-04（22→32 模块）

---

### 阶段 5：剩余可提取项清理（预计 2 轮）

> 目标：清理阶段 1–4 遗漏的可提取业务逻辑

**全量评估结果**（2026-07-04 对 26 个 PySide6 文件逐一审查）：

| 文件 | 行数 | 可提取？ | 估计行数 | 说明 |
|------|:----:|:--------:|:--------:|------|
| `qt_ability_panel.py` | 396 | ✅ 明确 | ~57 | `_extract_bonus_attributes` + `_read_special_slots` 静态方法无 Qt 依赖 |
| `detection_dialog.py` | 384 | ✅ 明确 | ~95 | `run_ocr_detection` 已是纯函数；`_run_detection` 重复逻辑需合并 |
| `qt_control_dock.py` | 403 | ⚠️ 边界 | ~25 | `populate_fixed_loadout_slots` 数据转换，略低于 30 行阈值 |
| `qt_dialogs.py` | 497 | ⚠️ 边界 | ~30 | 预设加载管道混合 Qt 文件对话框 |
| 其余 22 文件 | — | ❌ | 0 | 已委托已提取模块 / 纯 Qt 布局 / 过小 |

- [x] **5.1** `qt_ability_panel.py` — 提取 `_extract_bonus_attributes` + `_read_special_slots` 到 `weapon_data_model.py` ✅ 2026-07-04（~57 行，纯数据解析函数）
- [x] **5.2** `detection_dialog.py` — 合并 `run_ocr_detection` + `_run_detection` 为统一的 `ocr_pipeline.py` 纯函数模块 ✅ 2026-07-04（~95 行，消除重复检测调用）
- [x] **5.3** `qt_control_dock.py` — 评估结论：不提取。`populate_fixed_loadout_slots` 纯逻辑仅 ~8 行（catalog 查找 + 名称解析），其余 ~26 行为 QComboBox 操作（blockSignals/clear/addItem），提取后收益极低 ✅ 2026-07-04 评估
- [x] **5.4** `qt_dialogs.py` — 评估结论：不提取。预设加载管道 ~10 行纯逻辑（文件读取 + JSON 解析），~20 行为 QFileDialog/QMessageBox 操作，且 `compare_presets_parallel` 已是独立模块 ✅ 2026-07-04 评估

**验收**：
- 新模块可 `import` 成功且无 PySide6 依赖
- `check_pyside6_coupling.py` 通过
- 更新 `DECOUPLED_MODULES` 列表

---

## 4. 解耦模式参考

### 模式 A：纯函数提取
```python
# BEFORE: qt_survival_dialog.py
class QtSurvivalDialog(QDialog):
    def _refresh_execute(self):
        result = calculate_final_attack_with_details(...)
        self._execute_label.setText(f"处决伤害: {result}")

# AFTER: survival_estimator.py（纯 Python，无 PySide6）
@dataclass
class ExecuteResult:
    damage: float
    sp_restore: float

def estimate_execute(char_data, weapon_data, ...) -> ExecuteResult:
    result = calculate_final_attack_with_details(...)
    return ExecuteResult(damage=result, sp_restore=...)

# AFTER: qt_survival_dialog.py（纯渲染）
from .survival_estimator import estimate_execute
class QtSurvivalDialog(QDialog):
    def _refresh_execute(self):
        result = estimate_execute(self._char_data, self._weapon_data, ...)
        self._execute_label.setText(f"处决伤害: {result.damage}")
```

### 模式 B：数据定义提取
```python
# BEFORE: endfield_actions.py（import PySide6）
USER_INPUT_VARIABLES = {"user_input.敌人防御": {...}, ...}

# AFTER: compute_sheet_variables.py（纯 Python，无 PySide6）
USER_INPUT_VARIABLES = {"user_input.敌人防御": {...}, ...}

# AFTER: endfield_actions.py
from .compute_sheet_variables import USER_INPUT_VARIABLES
```

### 模式 C：选择模型提取
```python
# BEFORE: qt_panel.py
class QtSelectionPanel(QWidget):
    def _on_type_changed(self):
        filtered = [e for e in self.data_list if e["类型"] == selected_type]
        stars = sorted(set(e["星级"] for e in filtered))

# AFTER: selection_model.py（纯 Python，无 PySide6）
def filter_by_type(data_list: list[dict], type_name: str) -> list[dict]:
    return [e for e in data_list if e["类型"] == type_name]

def extract_stars(filtered: list[dict]) -> list[int]:
    return sorted(set(e["星级"] for e in filtered))

# AFTER: qt_panel.py（纯渲染）
from .selection_model import filter_by_type, extract_stars
class QtSelectionPanel(QWidget):
    def _on_type_changed(self):
        filtered = filter_by_type(self.data_list, selected_type)
        stars = extract_stars(filtered)
```

---

## 5. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|:----:|----------|
| 提取后 import 路径变化 | 中 | 旧模块通过 re-export 保持兼容 |
| 计算逻辑提取后行为变化 | 高 | 提取前后运行相同测试用例对比 |
| 循环导入 | 中 | 新模块放在 `gui/shared/` 或 `gui/app/`，不导入 Qt |
| 文件行数超限 | 低 | 新模块控制在 200 行以内 |
| 目录宽度超限 | 低 | 新模块放入已有子目录，不新增顶层目录 |
| Graph Editor 拆分引入回归 | — | 不拆分（接受为纯 GUI） |

---

## 6. 时间线总览

```
阶段 1：纯函数与数据定义    ████░░░░░░░░░░░░░░░░  ~3 轮  ✅ 完成
阶段 2：选择与过滤模型      ████████░░░░░░░░░░░░  ~3 轮  ✅ 完成
阶段 3：控制器与状态管理    ████████████░░░░░░░░  ~3 轮  ✅ 完成
阶段 4：验证与文档          ████████████████░░░░  ~2 轮  ✅ 完成
阶段 5：剩余可提取项清理    ████████████████░░░░  ~1 轮  ✅ 完成（2 提取 + 2 评估跳过）
                                                  ────────
                                                  总计 ~12 轮（28/28 完成）
```

---

## 7. 禁止事项

- **禁止删除** `framework/src/calc_framework/ui/` 或 `graph_editor/` 目录
- **禁止修改** `games/endfield/gui/` 中非必要的文件（最小 diff 原则）
- **禁止** 在阶段 1-3 期间修改 DAG 引擎核心（`dag/engine.py`、`dag/schema.py`）
- **禁止** 裸 `git push`，所有提交通过 `python scripts/github_upload_module.py`
- **禁止** 在无测试验证的情况下推进下一阶段

---

## 8. 相关文档

- [ADR-0001](adr/0001-code-layout-constraints.md) — 代码目录与文件规模约束
- [ADR-0025](adr/0025-framework-consolidation.md) — 框架接口一致性巩固
- [代码结构规范](代码结构规范.md) — 命名、拆分、导入规范
- [会话接续手册](会话接续手册.md) — 项目状态、架构接缝
