# Contributing Guide / 贡献指南

> Thank you for considering contributing to Calc Framework! 🎉 / 感谢你考虑为 Calc Framework 贡献代码！

Calc Framework is a multi-game damage calculation framework with PySide6 desktop GUI, React + FastAPI web frontend/backend, Python DAG compute engine, BWIKI data collection tools, AI calculator generator, and Docker deployment.

Project overview: [`README.md`](README.md) | Terminology: [`CONTEXT.md`](CONTEXT.md) | Commands: [`docs/操作指令集.md`](docs/操作指令集.md)

---

## Code of Conduct / 行为准则

**Be respectful, stay on topic.** / 互相尊重，就事论事。

- Be kind and rational in discussions / 讨论时保持友善和理性
- Welcome newcomers, respect experienced developers / 欢迎新贡献者，尊重资深开发者
- No personal attacks, discrimination, or trolling / 不接受人身攻击、歧视性言论或恶意挑衅

---

## Quick Start / 快速开始

### Requirements / 环境要求

| Tool | Version |
|------|---------|
| Python | 3.11+ (3.12+ recommended) |
| Node.js | 18+ (web frontend only) |
| Git | Latest stable |

### 1. Clone / 克隆

```bash
git clone git@github.com:wxhwwla/calc-framework.git
cd calc-framework
```

### 2. Create venv / 创建虚拟环境

**Windows: Set UTF-8 encoding BEFORE creating venv** to prevent file corruption from Unicode characters in pip packages.

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

### 3. Install dependencies / 安装依赖

```powershell
# Framework (editable mode)
python -m pip install -e framework

# Endfield game package + dev deps
cd games/endfield
pip install -e ".[dev]"

# Optional: build deps, OCR deps
pip install -e ".[build,ocr]"
cd ../..
```

| Option | Includes | Purpose |
|--------|----------|---------|
| `.[dev]` | pytest, pyyaml | Daily development |
| `.[build]` | PyInstaller | Build exe |
| `.[ocr]` | TorchVision, EasyOCR | Screenshot OCR |

### 4. Frontend deps / 前端依赖（web dev only）

```powershell
cd web/frontend
npm install
cd ../..
```

### 5. Verify / 验证安装

```powershell
# Framework tests
cd framework && pytest tests/ -q

# Endfield tests
cd games/endfield && pytest tests/calculation/ tests/data_loading/ -q

# Web frontend type-check
cd web/frontend && npx tsc --noEmit
```

---

## Development Workflow / 开发工作流

### Branch Strategy / 分支策略

- `main` — stable releases / 稳定发布版
- `develop` — active development / 开发分支
- Feature branches: `feature/xxx` — new features / 新功能
- Fix branches: `fix/xxx` — bug fixes / 修复

### Commit Conventions / 提交约定

```
v3.23.4: 更新 10 处文件
- 具体改动 1
- 具体改动 2
```

- Version bump is automatic (upload script) / 版本号由上传脚本自动递增
- Commits should be in Chinese (matching existing convention) / 提交消息使用中文
- GPG/SSH signing recommended for Verified badge / 建议配置签名以显示 Verified

### Before Submitting PR / 提交 PR 前

- [ ] Tests pass: `pytest` in both framework and relevant game package
- [ ] Lint passes: `ruff check` + `ruff format`
- [ ] Type check: `pyright` (or verify no new diagnostics)
- [ ] No new warnings in existing modules
- [ ] New code follows project structure conventions (dir ≤20 items, file ≤400 lines)
- [ ] Related docs updated if API changed

### Code Conventions / 代码规范

- **Comments**: Chinese / 注释使用中文
- **Naming**: `snake_case` for Python, `camelCase` for TypeScript
- **Types**: Type annotations required for public API
- **Structure**: See [ADR-0001](docs/adr/0001-code-layout-constraints.md) and [`docs/代码结构规范.md`](docs/代码结构规范.md)

---

## Project Architecture / 项目架构

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for full details. Key concepts:

| Layer | Description |
|-------|-------------|
| `framework/` | Generic calc framework — DAG engine, inverse engine, data, UI, search, plugin |
| `games/{game}/` | Game-specific adapter packages — calc logic, GUI, data loaders |
| `web/` | React frontend + FastAPI backend |
| `tools/` | Dev/maintenance tools |
| `scripts/` | Entry scripts |
| `utils/` | Shared utilities |

### Framework Abstractions for New Games / 新游戏可用的框架抽象

| Component | Import | Purpose |
|-----------|--------|---------|
| `JsonDataLoader[T]` | `calc_framework.data.json_loader` | Lazy-load JSON with cache |
| `GrowthParams` | `calc_framework.inverse.base` | Typed formula parameters |
| `InverseEngine` | `calc_framework.inverse.engine` | `data_to_params()` / `params_to_curve()` |
| `GameInverseAdapter` | `calc_framework.inverse.schema` | Declarative inverse engine integration |
| `DataContextLoader` | `calc_framework.data.loader` | ABC for DAG context building |
| `ThemeManager` | `calc_framework.ui.theme` | Multi-theme QSS management |
| `CalcWorker` | `utils.gui.qt_worker` | Generic QThread background worker |
| `CalcFrameworkError` | `calc_framework.errors` | Base exception for framework errors |

---

## Testing / 测试

```powershell
# All framework tests
cd framework && pytest tests/ -q

# Endfield tests
cd games/endfield && pytest tests/calculation/ tests/data_loading/ -q

# Quick smoke test (Endfield, no slow/integration)
cd games/endfield && pytest -m "not integration and not real_data and not slow" -q

# Web E2E
cd web/frontend && npx cypress run

# All lint
ruff check . && ruff format --check .
```

---

## Release & Upload / 发布与上传

```powershell
# Push to GitHub (version bump auto-handled by script)
python scripts/tools/github_upload_module.py

# Options:
python scripts/tools/github_upload_module.py --minor    # bump minor version
python scripts/tools/github_upload_module.py --no-bump  # push without version change
```

**⚠️ Warning**: `github_download_module.py` force-overwrites local with remote. Use with caution.

---

## Questions? / 有问题？

- [GitHub Issues](https://github.com/wxhwwla/calc-framework/issues) — Bug reports, feature requests
- [GitHub Discussions](https://github.com/wxhwwla/calc-framework/discussions) — Technical discussion
- Internal docs: [`docs/会话接续手册.md`](docs/会话接续手册.md) (for AI agents & maintainers)
