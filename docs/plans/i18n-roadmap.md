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

### 阶段 3：桌面 GUI i18n（~1-2 周）

| 任务 | 技术方案 |
|------|----------|
| 提取 PySide6 控件文本 | Qt Linguist (`.ts` 文件) |
| 翻译为英文 | Qt Linguist 或人工 |
| 编译为 `.qm` | `lrelease` |
| 启动时加载翻译 | `QTranslator` |
| GUI 语言切换菜单 | QMenu + 动态重载 |

**交付标准**：exe 打包版支持中/英切换。

### 阶段 4：代码与数据渐进英文化（持续）

| 任务 | 说明 |
|------|------|
| 公开 API docstring 英文化 | `framework/src/calc_framework/` 优先 |
| 游戏数据 JSON 加 `name_en` 字段 | 角色/武器英文名 |
| 日志/错误消息英文化 | 框架级日志优先 |

---

## 当前状态

| 阶段 | 状态 | 开始日期 |
|------|:--:|:--:|
| 阶段 1：GitHub 门面 | ✅ 已完成 | 2026-06-13 |
| 阶段 2：Web 前端 | 🟡 基础设施 + 主要组件翻译（~130 条，覆盖导航/计算器/方舟/敌参/模式选择，tsc 零错误） | 2026-06-13 |
| 阶段 3：桌面 GUI | ⬜ 未开始 | — |
| 阶段 4：渐进英文化 | ⬜ 未开始 | — |
