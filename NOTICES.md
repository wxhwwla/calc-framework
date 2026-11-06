# 第三方声明与署名（NOTICES）

本文件列明本仓库常见第三方组件与素材来源，**不**构成对游戏官方内容的授权。  
完整许可见 [`LICENSE`](LICENSE)、[`DATA_LICENSE`](DATA_LICENSE)、[`docs/数据来源与许可.md`](docs/数据来源与许可.md)。

## 软件依赖（含运行时与可选）

> 下表覆盖**直接依赖**与代表性传递依赖；完整版本与传递依赖以各 `requirements*.txt`、`pyproject.toml`、`package-lock.json`、`Cargo.lock` 为准。

### Python / 桌面 / 构建

| 组件 | 许可 | 说明 |
|------|------|------|
| Python | PSF License | https://www.python.org/psf-license/ |
| PySide6 | LGPL-3.0-only | GUI 框架（Qt 的 Python 绑定）；详见 https://www.qt.io/licensing/ |
| matplotlib | matplotlib License (BSD-compatible) | 伤害仪表盘 / 图表渲染 |
| numpy | BSD-3-Clause | 科学计算（OCR 可选依赖 `[ocr]` 传递依赖；tools/ocr/ 直接使用） |
| EasyOCR | Apache 2.0 | OCR 截图识装（可选依赖 `[ocr]`） |
| torchvision | BSD-3-Clause | TorchVision 目标检测（可选依赖 `[ocr]`）；替代 AGPL-3.0 的 ultralytics |
| pillow | HPND (Historical) | 图像处理（可选依赖 `[ocr]` 传递依赖） |
| pyyaml | MIT | 插件 YAML 配置（可选依赖 `[plugins]`） |
| PyInstaller | GPL-2.0（含例外） | 仅打包时使用，不随分发物提供；https://pyinstaller.org/ |
| pytest / pytest-cov | MIT | 仅开发/测试使用 |
| PyO3 | Apache-2.0 OR MIT | Rust 加速扩展（`extensions/rust_search/`）的 Python 绑定 |
| maturin | MIT OR Apache-2.0 | 构建 Rust 扩展（CI/wheel） |
| Rust toolchain / std | MIT OR Apache-2.0 | `extensions/rust_search/` |

### Web 后端

| 组件 | 许可 | 说明 |
|------|------|------|
| fastapi | MIT | Web 版后端（web/backend/）；仅在 web 部署时使用 |
| pydantic | MIT | Web 版后端数据校验（web/backend/）；仅在 web 部署时使用 |
| uvicorn | BSD-3-Clause | Web 版后端 ASGI 服务器（web/backend/）；仅在 web 部署时使用 |
| httpx | BSD-3-Clause | 出站 HTTP 客户端（AI 转发 / Hub 拉取） |
| httpcore | BSD-3-Clause | httpx 传输层；提供 `sni_hostname` 扩展 |
| python-multipart | Apache-2.0 | 表单与文件上传解析 |
| a2wsgi | Apache-2.0 | WSGI 适配层（历史 PythonAnywhere 兼容，仍在依赖中） |
| mcp | MIT | MCP 计算器构建服务器（`tools/calc_mcp/`，可选） |

### Web 前端

| 组件 | 许可 | 说明 |
|------|------|------|
| React / React DOM | MIT | Web 前端框架 |
| MUI（`@mui/material`、`@mui/icons-material`） | MIT | 组件库与图标 |
| Emotion（`@emotion/react`、`@emotion/styled`） | MIT | MUI 样式引擎 |
| React Router | MIT | 前端路由 |
| Zustand | MIT | 状态管理 |
| i18next / react-i18next | MIT | 国际化 |
| @xyflow/react（React Flow） | MIT | DAG 公式图编辑器 |
| ECharts / echarts-for-react | Apache-2.0 | 图表渲染 |
| sql.js | MIT | 浏览器端 SQLite（历史/搜索） |
| TypeScript | Apache-2.0 | 类型检查（构建期） |
| Vite | MIT | 前端构建与开发服务器 |
| Vitest | MIT | 前端单元测试 |
| Cypress | MIT | Web E2E 测试 |
| ESLint 及其插件 | MIT | 前端 lint |

## 游戏与 Wiki 内容

| 来源 | 权利方 | 本仓库中的使用 |
|------|--------|----------------|
| 《明日方舟：终末地》游戏内名称、数值、机制描述等 | 上海鹰角网络科技有限公司及相关权利人 | 仅作非商业计算器参考；版权归权利方 |
| 终末地 BWIKI | 玩家共建 / 哔哩哔哩游戏 Wiki 平台 | 校对参考；须遵守站点条款与 CC BY-SA 4.0 等 |
| MediaWiki API（`tools/bwiki_scout/`） | BWIKI 运营方 | 只读侦察；遵守访问频率与 robots/服务条款 |

**商标：**「明日方舟」「终末地」及相关标识为权利人商标。本工具为爱好者项目，**未经权利人书面许可，不得暗示官方背书或商业合作**。

## 关于捐赠

本项目在 GUI 中提供「自愿捐赠」入口，**捐赠系对开发者个人的无偿支持，不构成购买软件或获得商业许可的对价**（见 LICENSE §4.「创作者支持」）。捐赠者**不**因此获得：

- 本仓库游戏数据的商业使用授权（见 DATA_LICENSE）；
- 游戏官方内容的任何授权；
- 与鹰角网络等游戏权利方的合作或背书关系。

嵌入 .calcpack 配置包的捐赠 widget 所含文字和图片由配置包创建者自行定义，版权人对其内容不作认可或担保。

## 本项目著作权

- 软件源代码：Copyright (C) 2024–2026 wxhwwla Calc Framework（通用游戏计算框架）— 见 [`LICENSE`](LICENSE)
- 数据整理与编排：Copyright (C) 2024–2026 wxhwwla Calc Framework（通用游戏计算框架）— 见 [`DATA_LICENSE`](DATA_LICENSE)

如有遗漏或署名错误，请通过 Issue 或 wxhwwla@gmail.com 联系更正。
