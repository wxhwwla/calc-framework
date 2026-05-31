# ADR-0022：utils/ 职责归属清理

## 状态

已采纳

## 上下文

`utils/` 目前包含 16 个文件，混合了两类不同职责的代码：

### A. 纯工具函数（8 个文件）— 无 GUI 依赖

| 文件 | 职责 | 被调用方 |
|------|------|---------|
| `path_utils.py` | 统一路径处理（开发/打包模式） | data_loading、GUI、测试 |
| `app_paths.py` | search_output 目录分配 | qt_app_search_mixin 等 |
| `operation_log.py` | 分级操作日志 + JSON 导出 | qt_app_dialog_mixin 等 |
| `optional_deps.py` | 运行时/可选/开发依赖探测 | main.py、damage_visualization 等 |
| `platform_win32_patch.py` | 避免 WMI 查询卡死 | main.py、build.py |
| `updater.py` | 自动更新：GitHub Release → 下载 → 替换 | main_launcher.py |
| `search_format.py` | 搜索预估时长/工作量文案格式化 | search engine、GUI |
| `__init__.py` | 包初始化，重导出 | 全局 |

### B. GUI 相关代码（8 个文件）— 含 GUI 框架依赖或为 GUI 服务

| 文件 | 职责 | GUI 依赖 | 被调用方 |
|------|------|----------|---------|
| `donation.py` | 捐赠弹窗 + 嵌入组件 | **PySide6** | framework viewer、tools designer、legal |
| `gui_help_dialog.py` | 结构化帮助对话框（左树右内容） | **PySide6** | framework viewer、tools、GUI mixin |
| `gui_fonts.py` | matplotlib 中文字体 + 系统 UI 字体 | **tkinter** | gui_chart_theme、测试 |
| `gui_chart_theme.py` | matplotlib 暗色图表主题配色 | 间接（惰性导入 gui_fonts） | damage_visualization、测试 |
| `gui_window.py` | 主窗口启动时最大化适配 | 无 | 测试 |
| `gui_help_calculator.py` | 计算器帮助文档内容 | 无（仅导入 HelpSection 数据类） | qt_app_dialog_mixin |
| `gui_help_designer.py` | 设计器帮助文档内容 | 同上 | designer_main |
| `gui_help_launcher.py` | 启动器帮助文档内容 | 同上 | main_launcher |

### 问题

1. **目录扁平化**：16 个文件平铺在 `utils/` 下，GUI 和非 GUI 代码混在一起，违背"按职责拆目录"的原则（代码结构规范 §3.1）。
2. **命名不一致**：`gui_*` 前缀表明属于 GUI 领域，但与非 GUI 文件（`path_utils.py`、`operation_log.py`）混在同一目录。
3. **可发现性差**：新开发者想找"窗口最大化"相关代码，需要在 16 个文件中扫描；若放在 `utils/gui/window.py` 则一目了然。
4. **gui_ 前缀耦合**：文件以 `gui_` 前缀标识领域，但如果它们被放在 `gui/` 子包中，前缀变为冗余。

这些文件被三端共享（`framework/`、`games/endfield/`、`tools/`），因此不能移动到任意一层——必须保留在 `utils/` 命名空间下。

## 决策

在 `utils/` 内创建 `gui/` 子包，将 8 个 GUI 相关文件迁入，并去除 `gui_` 文件名前缀：

```
重构前：                         重构后：
utils/                           utils/
├── __init__.py                  ├── __init__.py          ← 保留纯工具重导出
├── path_utils.py                ├── path_utils.py        ← 不变
├── app_paths.py                 ├── app_paths.py         ← 不变
├── operation_log.py             ├── operation_log.py     ← 不变
├── optional_deps.py             ├── optional_deps.py     ← 不变
├── platform_win32_patch.py      ├── platform_win32_patch.py ← 不变
├── updater.py                   ├── updater.py           ← 不变
├── search_format.py             ├── search_format.py     ← 不变
├── donation.py                  ├── gui/                 ← 新建子包
├── gui_chart_theme.py           │   ├── __init__.py
├── gui_fonts.py                 │   ├── donation.py      ← 从 donation.py 迁入
├── gui_window.py                │   ├── chart_theme.py   ← 从 gui_chart_theme.py 迁入
├── gui_help_dialog.py           │   ├── fonts.py         ← 从 gui_fonts.py 迁入
├── gui_help_calculator.py       │   ├── window.py        ← 从 gui_window.py 迁入
├── gui_help_designer.py         │   ├── help_dialog.py   ← 从 gui_help_dialog.py 迁入
└── gui_help_launcher.py         │   ├── help_calculator.py  ← 从 gui_help_calculator.py 迁入
                                 │   ├── help_designer.py    ← 从 gui_help_designer.py 迁入
                                 │   └── help_launcher.py    ← 从 gui_help_launcher.py 迁入
                                 └── search_format.py
```

### 变更规则

| 规则 | 说明 |
|------|------|
| 文件名 | 去除 `gui_` 前缀（如 `gui_chart_theme.py` → `chart_theme.py`） |
| 内部导入 | 更新为 `utils.gui.xxx` 形式 |
| 包内符号名 | **不改变**（函数名、类名不变） |
| 外部导入 | 全部更新：`from utils.gui_chart_theme import X` → `from utils.gui.chart_theme import X` |
| 后向兼容 | 不在原位置保留存根（与候选5风格一致） |

## 详细方案

### 步骤

#### 1. 创建 `utils/gui/` 子包

新建 `utils/gui/__init__.py`，内容为空：

```python
# utils/gui/__init__.py
"""GUI 相关的工具函数与组件。"""
```

#### 2. 移动并重命名文件

| 源文件 | 目标文件 |
|--------|---------|
| `utils/donation.py` | `utils/gui/donation.py` |
| `utils/gui_chart_theme.py` | `utils/gui/chart_theme.py` |
| `utils/gui_fonts.py` | `utils/gui/fonts.py` |
| `utils/gui_window.py` | `utils/gui/window.py` |
| `utils/gui_help_dialog.py` | `utils/gui/help_dialog.py` |
| `utils/gui_help_calculator.py` | `utils/gui/help_calculator.py` |
| `utils/gui_help_designer.py` | `utils/gui/help_designer.py` |
| `utils/gui_help_launcher.py` | `utils/gui/help_launcher.py` |

#### 3. 更新已移动文件中的内部导入

移动后的文件若引用了其他 `utils` 模块，需要更新导入路径：

| 文件 | 旧导入 | 新导入 |
|------|--------|--------|
| `gui/help_launcher.py` | `from utils.gui_help_dialog import HelpSection` | `from utils.gui.help_dialog import HelpSection` |
| `gui/help_calculator.py` | 同上 | 同上 |
| `gui/help_designer.py` | 同上 | 同上 |
| `gui/chart_theme.py` | `from utils.gui_fonts import ...` | `from utils.gui.fonts import ...` |
| `gui/donation.py` | `from utils.path_utils import get_resource_path` | 不变（path_utils 仍在 utils/） |

#### 4. 更新外部导入（14 个文件）

| 文件 | 旧导入 | 新导入 |
|------|--------|--------|
| `main_launcher.py` | `from utils.gui_help_dialog import HelpDialog` | `from utils.gui.help_dialog import HelpDialog` |
| `main_launcher.py` | `from utils.gui_help_launcher import build_launcher_help` | `from utils.gui.help_launcher import build_launcher_help` |
| `tools/endfield_designer/designer_main.py` | `from utils.donation import open_donation_dialog` | `from utils.gui.donation import open_donation_dialog` |
| `tools/designer/app.py` | `from utils.gui_help_dialog import HelpSection, HelpDialog` | `from utils.gui.help_dialog import HelpSection, HelpDialog` |
| `tools/designer/app.py` | `from utils.donation import open_donation_dialog` | `from utils.gui.donation import open_donation_dialog` |
| `games/endfield/gui_design/shell/qt_app_dialog_mixin.py` | `from utils.gui_help_dialog import HelpDialog` | `from utils.gui.help_dialog import HelpDialog` |
| `games/endfield/gui_design/shell/qt_app_dialog_mixin.py` | `from utils.gui_help_calculator import build_calculator_help` | `from utils.gui.help_calculator import build_calculator_help` |
| `games/endfield/gui_design/shared/damage_visualization.py` | `from utils.gui_chart_theme import ...` | `from utils.gui.chart_theme import ...` |
| `games/endfield/gui_design/legal/donation_qt.py` | `from utils.donation import open_donation_dialog` | `from utils.gui.donation import open_donation_dialog` |
| `games/endfield/gui_design/designer/designer_main.py` | `from utils.gui_help_dialog import HelpDialog` | `from utils.gui.help_dialog import HelpDialog` |
| `games/endfield/gui_design/designer/designer_main.py` | `from utils.gui_help_designer import build_designer_help` | `from utils.gui.help_designer import build_designer_help` |
| `framework/src/calc_framework/ui/viewer.py` | `from utils.gui_help_dialog import HelpDialog` | `from utils.gui.help_dialog import HelpDialog` |
| `framework/src/calc_framework/ui/compute_sheet.py` | `from utils.donation import DonationWidget, DONATION_IMAGE_PATH` | `from utils.gui.donation import DonationWidget, DONATION_IMAGE_PATH` |
| `calc_engine/endfield/tests/utils/test_remaining_coverage.py` | 多个 `from utils.gui_*` 导入 | `from utils.gui.*` |
| `calc_engine/endfield/tests/utils/test_gui_window.py` | `from utils.gui_window import ...` | `from utils.gui.window import ...` |
| `calc_engine/endfield/tests/utils/test_extra_coverage.py` | `from utils.gui_window import ...` | `from utils.gui.window import ...` |

#### 5. 删除原文件

确认所有引用更新后，删除 `utils/` 下的 8 个源文件：
- `utils/donation.py`
- `utils/gui_chart_theme.py`
- `utils/gui_fonts.py`
- `utils/gui_window.py`
- `utils/gui_help_dialog.py`
- `utils/gui_help_calculator.py`
- `utils/gui_help_designer.py`
- `utils/gui_help_launcher.py`

## 影响范围

| 文件 | 操作 | 风险 |
|------|------|------|
| `utils/gui/__init__.py` | **新建** | 低 |
| `utils/gui/donation.py` | **新建**（从 utils/donation.py 迁入） | 低 — 内容不变 |
| `utils/gui/chart_theme.py` | **新建**（从 utils/gui_chart_theme.py 迁入+重命名） | 低 |
| `utils/gui/fonts.py` | **新建**（从 utils/gui_fonts.py 迁入+重命名） | 低 |
| `utils/gui/window.py` | **新建**（从 utils/gui_window.py 迁入+重命名） | 低 |
| `utils/gui/help_dialog.py` | **新建**（从 utils/gui_help_dialog.py 迁入+重命名） | 低 |
| `utils/gui/help_calculator.py` | **新建**（从 utils/gui_help_calculator.py 迁入+重命名） | 低 |
| `utils/gui/help_designer.py` | **新建**（从 utils/gui_help_designer.py 迁入+重命名） | 低 |
| `utils/gui/help_launcher.py` | **新建**（从 utils/gui_help_launcher.py 迁入+重命名） | 低 |
| 原 8 个文件 | **删除** | 中 — 需确保无遗漏引用 |
| 14 个外部导入文件 | **更新导入路径** | 低 — 纯字符串替换 |

**不涉及**：`utils/` 下的 8 个纯工具文件（path_utils、app_paths 等）。

## 验证标准

1. [ ] `from utils.gui.help_dialog import HelpSection, HelpDialog` 可导入
2. [ ] `from utils.gui.donation import open_donation_dialog, DonationWidget` 可导入
3. [ ] `from utils.gui.chart_theme import configure_matplotlib_gui_style` 可导入
4. [ ] `from utils.gui.fonts import configure_matplotlib_font` 可导入
5. [ ] `from utils.gui.window import apply_startup_maximized` 可导入
6. [ ] 原路径 `from utils.donation import X` 不再可用（确认无遗漏引用）
7. [ ] ruff check 无新增错误

## 考虑过的替代方案

### 方案 A：保持现状

放弃——16 个文件平铺在 `utils/` 目录下，GUI 和非 GUI 混合，违背代码结构规范。

### 方案 B：保留 gui_ 前缀 + 子包

将文件原样（保留 `gui_` 文件名）移入 `utils/gui/`。但这样文件名变成 `utils/gui/gui_chart_theme.py`，`gui_` 前缀在 `gui/` 子包内是冗余的。

### 方案 C：移到 framework 层

将 GUI 工具移到 `framework/src/calc_framework/ui/utils/`。但 `donation.py` 包含 Endfield 特定的捐赠二维码路径，不属于框架。

## 时间线

- 实施：与候选7（本 ADR）同步
- 预计测试回退率：0%（纯移动逻辑，不改变行为）

## 术语表

- **gui_ 前缀**：`utils/` 目录中以 `gui_` 开头的文件名，表明其属于 GUI 领域
- **子包（Sub-package）**：包含 `__init__.py` 的子目录，在 Python 中形成包层级
