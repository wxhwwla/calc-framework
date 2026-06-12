# 贡献指南

> 感谢你考虑为 Calc Framework 项目贡献代码！🎉
>
> [:us: English](CONTRIBUTING.md)

Calc Framework 是一个多游戏伤害计算框架，包含 PySide6 桌面 GUI、React + FastAPI Web 前端/后端、Python DAG 计算引擎、BWIKI 数据采集工具等。

项目概述：[`README_zh.md`](README_zh.md) | 术语：[`CONTEXT_zh.md`](CONTEXT_zh.md) | 命令：[`docs/操作指令集.md`](docs/操作指令集.md)

---

## 行为准则

**互相尊重，就事论事。**

- 讨论时保持友善和理性
- 承认不同水平——欢迎新贡献者，也尊重资深开发者
- 不接受人身攻击、歧视性言论或恶意挑衅

---

## 快速开始

### 环境要求

| 工具 | 版本要求 |
|------|----------|
| Python | 3.11+（推荐 3.12） |
| Node.js | 18+（仅 Web 前端开发需要） |
| Git | 最新稳定版 |

### 1. 克隆仓库

```bash
git clone git@github.com:wxhwwla/calc-framework.git
cd calc-framework
```

### 2. 创建虚拟环境（重要）

Windows 下**创建 venv 前必须先设置 UTF-8 编码**，否则 pip 安装含 Unicode 字符的包时可能损坏文件：

```powershell
# PowerShell
$env:PYTHONUTF8 = "1"
chcp 65001 > $null
python -m venv .venv
.venv\Scripts\activate
```

```bash
# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. 安装依赖

```powershell
# 安装通用计算框架（可编辑模式）
python -m pip install -e framework

# 安装游戏包（终末地）+ 开发依赖
cd games/endfield
pip install -e ".[dev]"

# 可选：打包依赖、OCR 依赖
pip install -e ".[build,ocr]"
cd ../..
```

| 选项 | 包含 | 用途 |
|------|------|------|
| `.[dev]` | pytest、pyyaml 等 | 日常开发 |
| `.[build]` | PyInstaller | 打包 exe |
| `.[ocr]` | TorchVision、EasyOCR | 截图识装功能 |

### 4. 安装前端依赖（仅 Web 开发）

```powershell
cd web/frontend
npm install
cd ../..
```

### 5. 验证安装

```powershell
# 框架测试
cd framework && pytest tests/ -q

# 终末地测试
cd games/endfield && pytest tests/calculation/ tests/data_loading/ -q

# Web 前端类型检查
cd web/frontend && npx tsc --noEmit
```

---

## 开发工作流

### 分支策略

- `main` — 稳定发布版
- `develop` — 开发分支
- `feature/xxx` — 新功能
- `fix/xxx` — Bug 修复

### 提交约定

```
v3.23.4: 更新 10 处文件
- 具体改动 1
- 具体改动 2
```

- 版本号由上传脚本自动递增
- 提交消息使用中文
- 建议配置 GPG/SSH 签名以显示 Verified 标记

### 提交 PR 前检查清单

- [ ] 测试通过：框架和游戏包均 `pytest` 通过
- [ ] Lint 通过：`ruff check` + `ruff format`
- [ ] 类型检查：`pyright`（或无新增诊断）
- [ ] 无新增警告
- [ ] 遵循代码结构规范（目录 ≤20 项，文件 ≤400 行）
- [ ] API 变更时同步更新文档

### 代码规范

- **注释**：中文
- **命名**：Python `snake_case`，TypeScript `camelCase`
- **类型**：公开 API 必须有类型注解
- **结构**：见 [ADR-0001](docs/adr/0001-code-layout-constraints.md) 和 [`docs/代码结构规范.md`](docs/代码结构规范.md)

---

## 项目架构

详见 [`ARCHITECTURE_zh.md`](ARCHITECTURE_zh.md)。关键概念：

| 层 | 说明 |
|----|------|
| `framework/` | 通用计算框架 — DAG 引擎、逆推引擎、数据、UI、搜索、插件 |
| `games/{game}/` | 游戏特定适配包 — 计算逻辑、GUI、数据加载器 |
| `web/` | React 前端 + FastAPI 后端 |
| `tools/` | 开发/维护工具 |
| `scripts/` | 入口脚本 |
| `utils/` | 共享工具库 |

### 新游戏可用的框架组件

| 组件 | 导入路径 | 用途 |
|------|----------|------|
| `JsonDataLoader[T]` | `calc_framework.data.json_loader` | JSON 懒加载缓存 |
| `GrowthParams` | `calc_framework.inverse.base` | 类型化公式参数 |
| `InverseEngine` | `calc_framework.inverse.engine` | `data_to_params()` / `params_to_curve()` |
| `GameInverseAdapter` | `calc_framework.inverse.schema` | 声明式逆推引擎接入 |
| `DataContextLoader` | `calc_framework.data.loader` | DAG 上下文构建 ABC |
| `ThemeManager` | `calc_framework.ui.theme` | 多主题 QSS 管理 |
| `CalcWorker` | `utils.gui.qt_worker` | 通用 QThread 后台线程 |
| `CalcFrameworkError` | `calc_framework.errors` | 框架异常基类 |

---

## 测试

```powershell
# 框架全量测试
cd framework && pytest tests/ -q

# 终末地测试
cd games/endfield && pytest tests/calculation/ tests/data_loading/ -q

# 快速冒烟测试（终末地，不含慢速/集成）
cd games/endfield && pytest -m "not integration and not real_data and not slow" -q

# Web E2E
cd web/frontend && npx cypress run

# 全部 lint
ruff check . && ruff format --check .
```

---

## 发布与上传

```powershell
# 推送 GitHub（版本号由脚本自动维护）
python scripts/tools/github_upload_module.py

# 选项：
python scripts/tools/github_upload_module.py --minor    # 第二位+1
python scripts/tools/github_upload_module.py --no-bump  # 不改版本号
```

**⚠️ 注意**：`github_download_module.py` 会覆盖本地，使用时请谨慎。

---

## 有问题？

- [GitHub Issues](https://github.com/wxhwwla/calc-framework/issues) — Bug 报告 / 功能建议
- [GitHub Discussions](https://github.com/wxhwwla/calc-framework/discussions) — 技术讨论
- 内部文档：[`docs/会话接续手册.md`](docs/会话接续手册.md)（AI Agent 与维护者用）
