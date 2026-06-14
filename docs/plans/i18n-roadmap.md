# i18n 多语言支持路线图

> **目标**：让 GitHub 上的国际开发者能够理解项目、参与贡献。中文内容保留，英文作为第二语言共存。

---

## 阶段规划

### 阶段 1：GitHub 门面英文化（1-2 天）

面向 GitHub 访客的门面文档双语化。

| 文件 | 方式 | 说明 |
|------|------|------|
| `README.md` + `README_zh.md` | 中英分离 | 顶部互链 `[:cn:]` / `[:us:]` |
| `ARCHITECTURE.md` + `ARCHITECTURE_zh.md` | 中英分离 | 顶部互链 |
| `CONTRIBUTING.md` + `CONTRIBUTING_zh.md` | 中英分离 | 顶部互链 |
| `CONTEXT.md` + `CONTEXT_zh.md` | 中英分离 | 顶部互链；EN 版为英文术语表，ZH 版为完整中文术语 |
| `CODE_OF_CONDUCT.md` | 英文 | 已有英文版 |
| `NOTICES.md` | 英文 | 已有英文版 |

**交付标准**：GitHub 首页 README 全英文可读，贡献者知道如何参与。

### 阶段 2：Web 前端 i18n（~1 周）

| 任务 | 技术方案 |
|------|----------|
| 安装 `react-i18next` + `i18next` | npm 依赖 |
| 提取所有中文字符串到 `zh-CN.json` | 自动化扫描 |
| 翻译为 `en.json` | 人工翻译 ~500 条 |
| 添加语言切换按钮 | MUI Button + i18n.changeLanguage |
| 浏览器语言自动检测 | i18next-browser-languagedetector |

**交付标准**：wxhwwla.pythonanywhere.com 支持中/英切换。

### 阶段 3：桌面 GUI i18n（进行中 — 基础设施已完成）

| 任务 | 技术方案 | 状态 |
|------|----------|:--:|
| 创建 `i18n.py` 翻译引擎 | `DesktopTranslator` 单例 + JSON 扁平化 + 回退逻辑 | ✅ |
| 提取 PySide6 控件文本 | JSON dot-notation 键名（与 Web 端共享结构） | ✅ |
| 翻译为英文 | `zh-CN.json`（源语言）+ `en.json`（282 键） | ✅ |
| 15 个 GUI 文件集成 | graph_editor / editor / dev_toolkit / dag_debugger / launcher / viewer / pluginManager | ✅ |
| endfield_app / designer 逐控件翻译 | 将剩余硬编码中文字符串替换为 `tr()` 调用 | 🟡 |
| GUI 语言切换菜单 | QMenu + 动态重载 + `set_locale()` | 🟡 |
| 编译为 `.qm` | 已弃用 Qt Linguist 方案，改用 JSON（降低构建复杂度） | — |

**交付标准**：exe 打包版支持中/英切换。

### 阶段 4：代码与数据渐进英文化（持续）

| 任务 | 说明 |
|------|------|
| 公开 API docstring 英文化 | `framework/src/calc_framework/` 优先 |
| 游戏数据 JSON 加 `name_en` 字段 | 角色/武器英文名 |
| 日志/错误消息英文化 | 框架级日志优先 |

---

## 当前状态

| 阶段 | 状态 | 开始日期 | 完成日期 |
|------|:--:|:--:|:--:|
| 阶段 1：GitHub 门面 | ✅ 已完成 | 2026-06-13 | 2026-06-13 |
| 阶段 2：Web 前端 | ✅ 已完成 | 2026-06-13 | 2026-06-13 |
| 阶段 3：桌面 GUI | 🟡 进行中 | 2026-06-13 | — |
| 阶段 4：渐进英文化 | ⬜ 未开始 | — | — |

### 阶段 2 完成详情

- **翻译键数**：~500+ 键（zh-CN.json + en.json）
- **覆盖范围**：81 个 React 组件 + 17 个 API 文件全部转换
- **构建验证**：tsc --noEmit 零类型错误
- **交付功能**：语言切换按钮（MUI Button + i18n.changeLanguage）+ 浏览器语言自动检测（i18next-browser-languagedetector）
- **交付标准达成**：wxhwwla.pythonanywhere.com 已支持中/英切换

### 阶段 3 当前进展

- **基础设施**：`DesktopTranslator` 类（单例模式、缓存机制、回退逻辑、线程安全）
- **翻译数据**：282 个翻译键（zh-CN.json + en.json），覆盖 15 个 GUI 文件
- **已覆盖模块**：graph_editor（83键）、editor（30键）、dev_toolkit（39键）、debugger（12键）、launcher（27键）、viewer（22键）、pluginManager（8键）、common（38键）、app（4键）、themeNames（2键）、log（2键）
- **待完成**：endfield_app、designer 等逐控件翻译
