# Desktop GUI i18n 多语言支持

> **阶段 3**: 桌面 PySide6 应用国际化  
> **状态**: 基础设施已完成（282 键 / 15 文件），待逐控件翻译 endfield_app / designer  
> **日期**: 2026-06-13

---

## 概述

桌面 i18n 系统采用基于 JSON 的翻译机制，与 Web 端共享键名结构。不使用 Qt Linguist (`.ts`/`.qm`)，以降低构建复杂度并保持与 Web 端的一致体验。

### 与 Web i18n 的对比

| 特性 | Web (i18next) | Desktop (本模块) |
|------|--------------|------------------|
| 翻译数据格式 | TypeScript 嵌套对象 | JSON 嵌套对象（同结构） |
| 键名规范 | `compute.title.advanced` | `compute.title`（扁平 dot-notation） |
| 加载方式 | `i18next` 异步 | 同步 JSON 文件 |
| 语言检测 | `i18next-browser-languagedetector` | `locale.getdefaultlocale()` |
| 切换语言 | `i18n.changeLanguage()` | `set_locale("en")` |
| 插值语法 | `{{n}}` | `{n}` (Python `str.format`) |

---

## 架构

```
calc_framework/ui/
├── i18n.py               # DesktopTranslator 单例 + tr() API
├── i18n_data/
│   ├── zh-CN.json        # 中文翻译（源语言，也是回退语言）
│   └── en.json           # 英文翻译
└── viewer.py             # 导入并使用 tr()
```

### DesktopTranslator 类

- **单例模式** — 模块级 `_instance`，通过 `tr()` 函数访问
- **缓存机制** — 首次 `tr()` 调用时从磁盘加载 JSON 并扁平化到内存字典
- **回退逻辑** — 当前 locale 查不到时回退到 `zh-CN`；再查不到返回键名本身
- **线程安全** — 使用 `threading.Lock` 保护缓存写入

---

## API 参考

### 核心函数

```python
from calc_framework.ui.i18n import tr, set_locale, current_locale, reload_translations

# 翻译字符串
label.setText(tr("desktop.viewer.windowTitle"))
# → "计算包查看器" (zh-CN) 或 "CalcPack Viewer" (en)

# 带插值
label.setText(tr("desktop.launcher.adapterCount", n=5))
# → "已发现 5 个游戏" 或 "5 game(s) found"

# 切换语言
set_locale("en")
# 之后需要手动刷新 UI（调用 setText / setWindowTitle）

# 查询当前语言
print(current_locale())  # → "zh-CN" or "en"

# 清空缓存重新加载（开发调试用）
reload_translations()
```

### 自动语言检测

模块导入时自动调用 `locale.getdefaultlocale()`：
- 系统语言以 `"zh"` 开头 → `"zh-CN"`
- 其他所有情况 → `"en"`

---

## 如何添加新的可翻译字符串

### 1. 在 JSON 文件中添加条目

`framework/src/calc_framework/ui/i18n_data/zh-CN.json`:

```json
{
  "desktop": {
    "viewer": {
      "myNewLabel": "我的新标签"
    }
  }
}
```

`en.json` (同路径):

```json
{
  "desktop": {
    "viewer": {
      "myNewLabel": "My New Label"
    }
  }
}
```

### 2. 在代码中使用

```python
from calc_framework.ui.i18n import tr

# 创建 widget 时
label = QLabel(tr("desktop.viewer.myNewLabel"))

# 动态更新已有 widget
self._some_label.setText(tr("desktop.viewer.myNewLabel"))
```

### 3. 键名规范

遵循 Web i18n 的命名习惯：
- **`common.*`** — 通用词汇（OK, Cancel, Save, …）
- **`app.*`** — 应用级标题
- **`desktop.viewer.*`** — CalcPackViewer 相关
- **`desktop.launcher.*`** — 启动器相关
- **`desktop.devToolkit.*`** — 开发者工具箱相关
- **`desktop.pluginManager.*`** — 插件管理器相关
- **`desktop.log.*`** — 日志面板相关
- **`desktop.themeNames.*`** — 主题名称

### 4. 注意事项

- **键名统一使用英文**，中文是值
- 新键名如果已有 Web 等价键，优先复用 Web 键名
- JSON 文件中的注释不合法，请勿添加注释
- 两个 locale 的 JSON 文件必须保持键结构对称

---

## 如何添加新 locale

1. 创建 `i18n_data/{locale}.json` (例如 `ja.json`)
2. 与 `zh-CN.json` 保持完全相同的键结构，翻译所有值
3. 在 `i18n.py` 的 `SUPPORTED_LOCALES` 元组中添加新 locale:

```python
SUPPORTED_LOCALES = ("zh-CN", "en", "ja")
```

4. 重启应用，新 locale 即可通过 `set_locale("ja")` 使用

---

## 当前覆盖状态

### 已覆盖 (282 键)

| 命名空间 | 键数 | 说明 |
|----------|:----:|------|
| `app.*` | 4 | 应用标题 |
| `common.*` | 38 | 通用 UI 词汇 |
| `desktop.viewer.*` | 22 | CalcPackViewer 菜单、面板、状态栏 |
| `desktop.launcher.*` | 27 | 启动器窗口、更新对话框 |
| `desktop.devToolkit.*` | 39 | 开发者工具箱导航、页签（8）、分组（2）、AI生成器（14） |
| `desktop.pluginManager.*` | 8 | 插件管理器对话框 |
| `desktop.log.*` | 2 | 日志面板 |
| `desktop.themeNames.*` | 2 | 主题名称 |
| `desktop.graphEditor.*` | 83 | 图编辑器完整 UI（菜单、工具栏、属性面板、节点编辑、帮助对话） |
| `desktop.editor.*` | 30 | 布局编辑器（DAG加载、节管理、导出、预览） |
| `desktop.debugger.*` | 12 | DAG 分步调试器（步骤控制、进度显示、示例图） |
| `desktop.endfield.*` | 16 | 终末地计算页（shell 页签/确认按钮 + 总伤面板） |

### 已集成 GUI 文件 (17 个)

| 文件 | 所属模块 | 状态 |
|------|----------|:--:|
| `graph_editor/graph_editor_widget.py` | graphEditor | ✅ 已集成 |
| `graph_editor/node_panel.py` | graphEditor | ✅ 已集成 |
| `graph_editor/prop_panel.py` | graphEditor | ✅ 已集成 |
| `graph_editor/file_actions.py` | graphEditor | ✅ 已集成 |
| `graph_editor/file_io.py` | graphEditor | ✅ 已集成 |
| `graph_editor/ports_and_wire.py` | graphEditor | ✅ 已集成 |
| `graph_editor/node_operations.py` | graphEditor | ✅ 已集成 |
| `graph_editor/help_content.py` | graphEditor | ✅ 已集成 |
| `editor/gui.py` | editor | ✅ 已集成 |
| `dev_toolkit/pages.py` | devToolkit | ✅ 已集成 |
| `dag_debugger/dag_debugger.py` | debugger | ✅ 已集成 |
| `launcher/launcher_window.py` | launcher | ✅ 已集成 |
| `viewer.py` | viewer | ✅ 已集成 |
| `plugin_manager.py` | pluginManager | ✅ 已集成 |
| `theme.py` + `log_widget.py` | themeNames / log | ✅ 已集成 |
| `games/endfield/gui/endfield_shell.py` | endfield 计算页 | ✅ 已集成 |
| `games/endfield/gui/presentation/total_damage_panel.py` | endfield 总伤面板 | ✅ 已集成 |

### 待覆盖 (后续 PR)

以下文件仍包含硬编码中文字符串，将在后续 PR 中逐步迁移：

- `viewer_render.py` — QMessageBox 错误提示
- `controls.py` — 控件标签
- `compute_sheet.py` — 计算表标题/标签
- `sheet_widgets.py` — 表格列头
- `viewer_plugin_manager.py` — 插件详情面板
- `log_widget.py` — 日志控件标签
- `theme.py` — 主题切换消息
- `viewer_help_content.py` — 帮助文档内容（HTML 模板）
- `graph_editor/` — 图编辑器 UI
- `dev_toolkit/pages.py` — 工具页面内容

---

## 与 Web i18n 的差异

1. **插值语法**: Desktop 使用 Python `{name}`，Web 使用 `{{name}}`
2. **HTML 支持**: Desktop 不支持 Web 的 `dangerouslySetInnerHTML`，所有文本为纯文本
3. **嵌套深度**: Desktop 将嵌套 JSON 扁平化存储，键名使用 dot-notation
4. **回退链**: Desktop 固定回退到 `zh-CN`，Web 使用 i18next 的多级回退
5. **热重载**: Desktop 不支持运行时检测文件变化，需调用 `reload_translations()` 手动重载

---

## 测试

`i18n.py` 模块可独立测试，无需 PySide6 运行环境：

```python
from calc_framework.ui.i18n import DesktopTranslator

# 创建隔离实例（不污染全局单例）
t = DesktopTranslator()

# 测试支持的语言
assert t.tr("common.ok") in ("确定", "OK")

# 测试回退
t.set_locale("en")
# 如果英文翻译存在，返回英文；否则回退到中文

# 测试插值
result = t.tr("desktop.launcher.adapterCount", n=3)
assert "3" in result

# 测试不存在的键
assert t.tr("nonexistent.key") == "nonexistent.key"
```
