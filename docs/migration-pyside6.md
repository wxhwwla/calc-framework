# PySide6 迁移方案

> 将 GUI 层从 CustomTkinter（CTk）逐步替换为 PySide6（Qt for Python）。
> 架构决策见 [`docs/adr/0002-migrate-to-pyside6.md`](adr/0002-migrate-to-pyside6.md)。

---

## 1. 迁移动机

| 痛点 | 根因 | PySide6 解决方案 |
|------|------|------------------|
| 主线程计算导致画面卡顿 | tkinter 无 QThread，耗时计算阻塞 `mainloop` | `QThread` + `signal`/`slot` 通知 GUI 更新 |
| 页面切换撕裂 | tkinter 无双缓冲，`grid_forget`/`pack_forget` 造成肉眼可见闪烁 | Qt 双缓冲渲染 + 垂直同步，`QStackedWidget` 无闪切换 |
| 控件文字截断 | CTk widget 使用像素固定宽，超出直接截断 | `QFontMetrics`、`sizeHint()`、`wordWrap` 自动适配内容 |
| 控件布局随意 | tkinter 布局管理弱，调试困难 | Qt `QHBoxLayout`/`QVBoxLayout`/`QGridLayout` 布局可预测 |

---

## 2. 架构总览

```
ENDFIELD_UI_BACKEND=ctk  (默认)     ENDFIELD_UI_BACKEND=qt
        │                                   │
        ▼                                   ▼
   gui_design/                          gui_design/
   ├── shell/app.py                     ├── shell/qt_app.py
   │    (CTk 根窗口)                    │    (QMainWindow 根窗口)
   ├── panels/                          ├── panels/
   │   ├── selection/panel.py           │   ├── selection/qt_panel.py
   │   ├── skill_level_panel.py         │   ├── qt_skill_level_panel.py
   │   └── ...                          │   └── ...
   ├── controls/                        ├── controls/
   │   ├── enhancement/section.py       │   ├── enhancement/qt_section.py
   │   └── ...                          │   └── ...
   └── shell/app_control_dock.py        └── shell/qt_control_dock.py
```

- 两套实现**平行共存**，Python 层面互不依赖
- 通过 `__init__.py` 根据环境变量 **编译期切换**导入
- CTk 版始终保持可用，逐步替换到 Qt 版文件删除为止

---

## 3. 切换机制

### 3.1 优先级

1. 环境变量：`ENDFIELD_UI_BACKEND=qt`
2. UI 偏好文件：`ui_preferences.json` 中 `"backend"` 字段
3. 默认值：`"ctk"`（最终阶段改为 `"qt"`）

### 3.2 模块分发层

每个包含双后端实现的模块，在其 `__init__.py` 中做运行时切换：

```python
# gui_design/shell/__init__.py
import os

def _detect_backend() -> str:
    env = os.environ.get("ENDFIELD_UI_BACKEND", "").strip().lower()
    if env in ("qt", "pyside6"):
        return "qt"
    # TODO: 后续从 ui_preferences.json 读取
    return "ctk"

_BACKEND = _detect_backend()
```

### 3.3 文件命名约定

| 后端 | 文件名模式 | 示例 |
|------|-----------|------|
| CTk | `*.py`（原样） | `app_control_dock.py`、`section.py` |
| PySide6 | `qt_*.py` | `qt_control_dock.py`、`qt_section.py` |

---

## 4. 分步迁移计划

### 阶段 0：基础设施（Day 1-2）✅ 已完成

- [x] **0.1** `pyproject.toml` 添加 `pyside6` optional dependency
- [x] **0.2** 创建 `gui_design/backends/` 目录
- [x] **0.3** 创建 `gui_design/shell/qt_app.py` — `QMainWindow` + `QApplication`
- [x] **0.4** 切换测试：`ENDFIELD_UI_BACKEND=qt python main.py` 启动 Qt 空窗口

### 阶段 1–9：Qt 控制栏 + 显示三列 + 选择面板 + 高级页连线 ✅ 已完成

- [x] **1** `qt_control_dock.py` — 高级页控制栏（三列布局、按钮、下拉、开关）
- [x] **2** `backends/qt_worker.py` — `CalcWorker`（QObject + QThread）
- [x] **3** `qt_columns.py` — 属性展示三列（QTableWidget 三列）
- [x] **4** `qt_panel.py` / `qt_subpanels.py` — 角色/武器选择面板（QComboBox + QSlider）
- [x] **5** `qt_app.py` — 双页签集成 + 面板联动
- [x] **6–9** 控制信号路由、确认刷新、高级页控件全连通

### 阶段 10：CalcWorker 异步确认实验 ✅ 已完成

- [x] **10.1** 审查同步确认流程 + CalcWorker 接口
- [x] **10.2** 尝试 `_on_confirm` 异步化（发现 QBasicTimer 跨线程限制）
- [x] **10.3** 结论：保持同步，未来需将 compute/render 解耦后再异步

### 阶段 11：高级页控件全连通 ✅ 已完成

- [x] **11.1** 敌人插件下拉（`list_plugin_enemy_choices` + `enemy_defense`）
- [x] **11.2** 手动 Buff 按钮 → 占位对话框
- [x] **11.3** 固定配装四槽（装备名下拉 + catalog 联动）
- [x] **11.4** 异常矩阵 / 伤害口径 / 暴击调整 → `_build_request`
- [x] **11.5** 运行时验证全部控件可读写

### 阶段 12：Qt 选择面板补全 + 阶段 15 特殊能力面板 ✅ 已完成

- [x] **12.1–12.2** 审查 `skill_level_panel.py` + `trust_panel.py`
- [x] **12.3** 清理 `qt_subpanels.py` 布局 bug，精简至 ~195 行
- [x] **12.4** 技能等级 + 信赖面板：重写 inline 布局，添加信号连线
- [x] **12.5** 拆分 `QtSpecialAbilityPanel` → `qt_ability_panel.py`（~230 行），添加滑块信号连线
- [x] **12.6** 运行时验证：面板创建、角色/武器选择后显隐、预设按钮、确认流程

─── 以下为剩余 CTk 模块的迁移阶段 ───

### 阶段 13：Qt 多技能次数 + 手动 Buff 编辑窗 ✅ 已完成

- [x] **13.1** 审查 CTk `place_multi_skill_section`、`rebuild_multi_skill_segment_rows`、`read_manual_multi_skill_counts`
- [x] **13.2** 在 `qt_control_dock.py` 的 `_build_col_multi()` 中集成全部控件：手动次数开关、动态段行、异常矩阵、暴击调整
- [x] **13.3** 创建 `gui_design/controls/manual_buff/qt_window.py`：`QtManualBuffDialog(QDialog)`，左侧 QListWidget 段/异常列表 + 右侧 ComboBox/DoubleSpinBox 编辑器
- [x] **13.4** `rebuild_segment_rows(char_data, s1, s2, s3)` 方法：按 `list_segment_count_specs` 动态重建输入行
- [x] **13.5** 接入 `qt_app.py`：`_on_char_name_change` + `_on_loadout_changed` 触发重建；`_on_manual_buff` 打开 QtManualBuffDialog
- [x] **13.6** 运行时验证：段行重建、读写回正确、Buff 对话框打开、确认流程正常

### 阶段 14：Qt 搜索 UI（全量遍历）✅ 已完成

- [x] **14.1** 审查 CTk 搜索 action 流：`build_search_job_inputs` → `prepare_search_job` → `run_exported_single_skill_search` → 结果弹窗
- [x] **14.2** `qt_control_dock.py` 第二列已有搜索控件：武器候选范围/装备范围 QComboBox、固定配装、MVP/全量/取消按钮
- [x] **14.3** 创建 `gui_design/controls/search/qt_actions.py`：`SearchWorker(QObject)` + `QtSearchResultsDialog(QDialog)`
- [x] **14.4** 添加搜索参数控件：并行线程 QComboBox + TopN QComboBox + 帮助提示标签
- [x] **14.5** `qt_app.py`：`_build_search_job_inputs()` 构建 SearchJobInputs；`_on_mvp_search`/`_on_full_search` 启动 QThread 搜索；`_start_search_thread` 管理 Worker 生命周期；进度/结果/错误信号处理
- [x] **14.6** 运行时验证：搜索控件存在、参数读取正确、JobInputs 构建成功、确认流程正常

### 阶段 16：Qt 增强工具（更多设置折叠区完整功能）✅ 已完成

- [x] **16.1** 预设导出：`_on_export_preset` 已实现 `QFileDialog` + `export_preset_json`
- [x] **16.2** 预设导入：`_on_import_preset` 已实现 + `_apply_preset_to_qt_app` 写入 Qt 面板控件
- [x] **16.3** 多方案对比弹窗：`QtComparePresetsDialog` — `QFileDialog` 选择 JSON → `compare_presets_parallel` 评估 → 排名文案
- [x] **16.4** 伤害仪表盘弹窗：`QtDamageDashboardDialog` — `FigureCanvasQTAgg` 嵌入饼图 + 柱状图
- [x] **16.5** 计算历史弹窗：`QtCalcHistoryDialog` — 最近 10 条 +「恢复此配置」按钮回调 `_apply_preset_to_qt_app`
- [x] **16.6** 操作日志导出：`_on_export_log` — `QFileDialog.getSaveFileName` + `export_to_file`
- [x] **16.7** `_on_confirm` 自动记录计算历史 + 刷新伤害快照
- [x] **16.8** 运行时验证：全部弹窗构造、历史记录、快照、预设往返

### 阶段 17：收尾与切换默认 ✅ 已完成

- [x] **17.1** 切换 `_BACKEND` 默认值为 `"qt"`（`gui_design/backends/__init__.py`）；`ENDFIELD_UI_BACKEND=ctk` 仍可切回 CTk
- [x] **17.2** 运行时验证：不设环境变量时 Qt 默认启动；设 `ctk` 时仍可切回 CTk
- [ ] **17.2** 运行全量回归测试
- [ ] **17.3** 逐一删除已迁移的 CTk 文件（保留 git 历史回滚）：
  - `panels/skill_level_panel.py`
  - `panels/trust_panel.py`
  - `panels/special_ability/` 全部 4 文件
  - `controls/multi_skill/` 全部 3 文件
  - `controls/manual_buff/` 全部 2 文件
  - `controls/search/` 全部 3 文件
  - `controls/enhancement/` 全部 4 文件
  - `controls/fixed_loadout.py`
  - `search_ui/search_results_view.py`
- [ ] **17.4** 清理 `gui_design/backends/ctk_factory.py`
- [ ] **17.5** 更新 `docs/操作指令集.md`、`docs/代码结构规范.md`
- [ ] **17.6** 更新 `docs/会话接续手册.md` 将 `last_updated` 日期改为最终切换日
- [ ] **17.7** 更新 `pyproject.toml` 将 `PySide6` 移入运行时依赖
- [ ] **17.8** 构建 exe 测试打包流程

---

## 5. 迁移顺序依赖图

```mermaid
flowchart LR
    subgraph 已完成
        P0[阶段0 骨架]
        P1[阶段1-9 控制栏/三列/面板]
        P10[阶段10 异步实验]
        P11[阶段11 高级页全连通]
        P12[阶段12+15 选择面板+特殊能力]
        P13[阶段13 多技能+Buff]
        P14[阶段14 搜索UI]
        P16[阶段16 增强工具]
        P17[阶段17 默认切换]
    end
```

- 阶段 12 和 13 可以**并行推进**（技能等级面板 vs 多技能次数）
- 阶段 15（特殊能力面板）依赖阶段 12 中 qt_panel 的嵌入接口
- 阶段 14（搜索 UI）依赖阶段 13 的固定配装 QComboBox 驱动
- 阶段 16（增强工具）依赖阶段 13–14 完成后验证
- 阶段 17 是所有阶段完成后的一步收尾

---

## 5. 测试策略

### 5.1 CTk 测试（CI 主力）

- 保持现有 `test_*.py` 套件不变（对应 CTk 实现）
- CI 仍跑全量 CTk 测试确保现有功能不被破坏

### 5.2 PySide6 冒烟测试（CI 新增）

```python
# tests/test_qt_imports.py
def test_qt_control_dock_imports():
    from gui_design.shell.qt_control_dock import build_control_dock
    assert callable(build_control_dock)
```

- 仅验证模块可导入、函数签名正确
- 不依赖 `QApplication` 实例（不启动 Qt 事件循环）
- 作为 CI 快速检查，不运行 GUI 集成测试

### 5.3 Qt GUI 集成测试（本地手动运行）

- 用 `pytest-qt` 或自定义 fixture
- 仅本地运行，不在 CI 中启用（需要 display server）

---

## 6. 回滚策略

### 阶段内回滚

```
ENDFIELD_UI_BACKEND=ctk python main.py
```
切换回环境变量即可，不修改任何代码。

### 完全回滚

```bash
git checkout -- gui_design/   # 放弃所有 qt_*.py 新建文件
git checkout -- pyproject.toml
```

### 增量回滚

删掉有问题的 `qt_*.py` 文件，修改对应 `__init__.py` 只保留 CTk 分支。

---

## 7. CTk ↔ PySide6 API 对照表

| CTk | PySide6 | 注意点 |
|-----|---------|--------|
| `ctk.CTk()` | `QMainWindow()` | Qt 需要先 `QApplication([])` |
| `ctk.CTkFrame` | `QWidget` / `QFrame` | Qt 容器自带 layout |
| `ctk.CTkLabel` | `QLabel` | Qt 支持 rich text |
| `ctk.CTkButton` | `QPushButton` | Qt 通过 `clicked.connect()` 绑定 |
| `ctk.CTkEntry` | `QLineEdit` | 几乎一对一 |
| `ctk.CTkOptionMenu` | `QComboBox` | 文字自动适配，不再截断 |
| `ctk.CTkComboBox` | `QComboBox` | 同上 |
| `ctk.CTkSlider` | `QSlider` | 范围需 Qt 风格 `setRange()` |
| `ctk.CTkCheckBox` | `QCheckBox` | 一对一 |
| `ctk.CTkSwitch` | `QCheckBox` | Qt 无原生 Switch，用 `setStyleSheet` 模拟 |
| `ctk.CTkTabview` | `QTabWidget` | 一对一，更稳定 |
| `ctk.CTkScrollableFrame` | `QScrollArea` | 需要内部再嵌一个 `QWidget` |
| `ctk.CTkTextbox` | `QTextEdit` / `QPlainTextEdit` | 一对一 |
| `ctk.CTkToplevel` | `QDialog` / `QMainWindow` | Qt modal 体系不同 |
| `ctk.CTkFont` | `QFont()` | 无缩放问题，直接设像素尺寸 |
| `.grid(row=, column=)` | `QGridLayout` | 概念一致，不需 `forget` 重排 |
| `.pack()` | `QVBoxLayout` / `QHBoxLayout` | 更强，支持 `addStretch()` |
| `.winfo_children()` | `.findChildren()` | API 不同 |
| `set_appearance_mode()` | `QStyle` / QSS | Qt 用 `setStyleSheet` 实现深色主题 |
| `TkDefaultFont` | `QApplication.font()` | 系统字体从 Qt 自动继承 |

---

## 8. QSS 深色主题速查

```qss
/* gui_design/backends/qt_dark_style.qss */
QMainWindow {
    background-color: #1A1A1A;
}
QLabel {
    color: #D1D1D1;
    font-size: 12px;
}
QPushButton {
    background-color: #2B6CB6;
    color: white;
    border-radius: 6px;
    padding: 4px 12px;
}
QPushButton:hover {
    background-color: #3182CE;
}
QComboBox {
    background-color: #2B2B2B;
    color: #D1D1D1;
    border: 1px solid #464646;
    border-radius: 4px;
    padding: 2px 6px;
}
QSlider::groove:horizontal {
    height: 6px;
    background: #464646;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #2B6CB6;
    width: 14px;
    margin: -4px 0;
    border-radius: 7px;
}
QCheckBox {
    color: #D1D1D1;
}
QTabWidget::pane {
    border: 1px solid #464646;
    background-color: #1A1A1A;
}
QTabBar::tab {
    background-color: #2B2B2B;
    color: #D1D1D1;
    padding: 6px 12px;
}
QTabBar::tab:selected {
    background-color: #2B6CB6;
}
```
