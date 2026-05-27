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

## 4. 分步迁移计划（14 天）

### 阶段 0：基础设施（Day 1-2）

**目标**：搭建双后端骨架，确保切换机制可用

- [ ] **0.1** `pyproject.toml` 添加 `pyside6` optional dependency
  ```toml
  [project.optional-dependencies]
  qt = ["PySide6>=6.6"]
  ```
- [ ] **0.2** 创建 `gui_design/backends/` 目录
  - `ctk_factory.py` — CTk widget 的 thin adapter
  - `qt_factory.py` — PySide6 widget 的 thin adapter
  - `__init__.py` — 根据 `_BACKEND` 导出统一接口
- [ ] **0.3** 定义最小公共接口
  ```python
  # gui_design/backends/__init__.py
  class IFrame: ...
  class ILabel: ...
  class IButton: ...
  class IOptionMenu: ...
  class ISlider: ...
  ```
- [ ] **0.4** 创建 `gui_design/shell/qt_app.py` — 空 `QMainWindow` + `QApplication`
- [ ] **0.5** 切换测试：`ENDFIELD_UI_BACKEND=qt python main.py` 启动 Qt 空窗口
- [ ] **0.6** 更新 `docs/操作指令集.md` 添加 `--backend qt` 用法

### 阶段 1：高级页控制栏（Day 3-5）

**目标**：PySide6 第一个实际 widget，解决画面撕裂+文字截断

- [ ] **1.1** 分析 `app_control_dock.py`（~122 行，~12 控件）
  - CTkButton ×3、CTkLabel ×2、CTkFrame ×4、CTkSwitch ×1、CTkCheckBox ×1
  - grid 布局 + `grid_forget`/`grid_remove` 动态显隐
  - 无回调逻辑，纯 UI → 最安全的首迁移目标
- [ ] **1.2** 创建 `gui_design/shell/qt_control_dock.py`
  - `QWidget` + `QVBoxLayout` 替代 `ctk.CTkFrame` + `grid`
  - `QPushButton` / `QLabel` / `QCheckBox` 替代对应 CTk 控件
  - 用 `QSS` 模拟 CTk 深色蓝色主题的外观
  - 用 `QStackedWidget` 替代 `grid_forget`/`grid_remove` 的显隐切换
- [ ] **1.3** 在 `qt_app.py` 中将控制栏嵌入主窗口布局
- [ ] **1.4** 验证：控制栏可正常显示，所有按钮响应，显隐切换无撕裂
- [ ] **1.5** 冒烟测试：`python -c "from gui_design.shell.qt_control_dock import *"`

### 阶段 2：计算线程分离（Day 5-7）

**目标**：解决最大痛点 — 耗时计算不阻塞 GUI

- [ ] **2.1** 创建 `gui_design/backends/worker.py`
  ```python
  class CalcWorker(QObject):
      finished = Signal(object)
      progress = Signal(int, int)
      
      @Slot()
      def run_calculation(self, ...):
          # 跑计算逻辑
          self.finished.emit(result)
  ```
- [ ] **2.2** 在 `qt_app.py` 中集成 Worker 到 `QThread`
- [ ] **2.3** 原有 CTk 版保持同步计算不变（不动现有代码）
- [ ] **2.4** 验证：PySide6 版计算时 UI 不卡顿，可拖动/切换页面

### 阶段 3：属性显示三列（Day 7-9）

**目标**：PySide6 重写最频繁刷新的区域

- [ ] **3.1** 分析 `display_view/`（confirm.py、render.py、zone_panel.py、refresh.py，~580 行）
  - 文本渲染 + 15 乘区数据显示
  - 大量 `grid_forget` + 重绘 → 最佳 QTableView 改造候选
- [ ] **3.2** 创建 `gui_design/shared/display_view/qt_render.py`
  - `QTableWidget` 替代逐行 `CTkLabel` + `grid`
  - `QStyledItemDelegate` 控制颜色/字体
- [ ] **3.3** 接入 `qt_app.py`，与 Qt 版控制栏联动
- [ ] **3.4** 验证：频繁切换/刷新时无闪烁

### 阶段 4：角色/武器选择面板（Day 9-11）

**目标**：解决文字截断 + OptionMenu 字体

- [ ] **4.1** 分析 `panels/selection/`（panel.py + build.py，~230 行）
  - CTkOptionMenu ×3、CTkLabel ×4、CTkSlider ×1
  - 联动逻辑（类型→星级→名称→等级）
- [ ] **4.2** 创建 `gui_design/panels/selection/qt_panel.py`
  - `QComboBox` 替代 `CTkOptionMenu`（文字自动适配置，不再截断）
  - `QSlider` 替代 `CTkSlider`
- [ ] **4.3** 联动逻辑保持不变（`StringVar` → `QStringListModel` + signals）

### 阶段 5：剩余模块填充（Day 11-13）

**目标**：按优先级逐个迁移剩余模块

| 模块 | 文件名 | 行数 | 优先级 | 说明 |
|------|--------|------|--------|------|
| 技能等级 | `skill_level_panel.py` | ~274 | ★★★ | 3 个 QSlider + QLabel |
| 信赖 | `trust_panel.py` | ~81 | ★★☆ | 1 个 QSlider，简单 |
| 特殊能力 | `special_ability/` | ~360 | ★★★ | 复杂联动 |
| 固定配装 | `fixed_loadout.py` | ~200 | ★★☆ | QComboBox 为主 |
| 增强操作 | `enhancement/` | ~500 | ★★★ | 含 dialogs |
| 多技能 | `multi_skill/` | ~450 | ★★★ | 复杂计数逻辑 |
| 手动增益 | `manual_buff/window.py` | ~200 | ★★☆ | CTkToplevel → QDialog |
| 搜索 UI | `search_ui/` | ~200 | ★★☆ | 搜索结果显示 |
| 法律声明 | `legal/attribution.py` | ~50 | ★☆☆ | 纯文本，最低优先级 |

### 阶段 6：收尾与切换默认（Day 14）

- [ ] **6.1** 切换 `_BACKEND` 默认值为 `"qt"`
- [ ] **6.2** 运行全量回归测试
- [ ] **6.3** 删除已迁移的 CTk 文件（保留 git 历史回滚）
- [ ] **6.4** 删除 `gui_design/backends/ctk_factory.py`
- [ ] **6.5** 更新 `docs/操作指令集.md`、`docs/代码结构规范.md`
- [ ] **6.6** 更新 `docs/会话接续手册.md`
- [ ] **6.7** 更新 `pyproject.toml` 将 `PySide6` 移入运行时依赖
- [ ] **6.8** 构建 exe 测试打包流程

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
