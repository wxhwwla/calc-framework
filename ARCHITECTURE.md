# Architecture Overview / 架构概述

> This document is the root-level entry point for project architecture.
> Detailed design: [`docs/算法与架构.md`](docs/算法与架构.md) (ZH, partially outdated).
> Architecture Decision Records: [`docs/adr/`](docs/adr/).
>
> 本文档是项目架构的根级入口。详细设计见算法与架构.md，架构决策记录见 adr/。

---

## Tech Stack / 技术栈

| Component | Technology |
|-----------|------------|
| Compute Engine | Python 3.12+ (DAG + inverse engine + full search) |
| Desktop GUI | PySide6 (Qt 6) |
| Web Frontend | React + TypeScript + Vite + MUI v6 |
| Web Backend | FastAPI + Uvicorn |
| Data Layer | JSON files + Pydantic validation |
| Testing | pytest + pytest-cov |
| Linting | ruff (lint + format) + pyright |
| Packaging | PyInstaller (onedir) + NSIS installer |
| Container | Docker + docker-compose |
| Deployment | PythonAnywhere (Web version) |

---

## System Layers / 系统分层

```
GUI Layer (PySide6 / React → FastAPI)
    ↓ framework_bridge.py
DAG Engine (calc_framework.dag)
    ↓           ↓
Data Layer    Search Engine
(JSON/Pydantic)  (enumeration/parallel)
    ↓
Adapter Layer (framework/adapters/{game}/)
    ↓
Inverse Engine (calc_framework.inverse)
    — bidirectional formula fitting for any game
```

---

## Directory Structure / 目录结构

```
framework/          ← Generic calc framework (pip package calc-framework)
  adapters/         ← Game adapter packages (endfield/arknights/moba/fps/card_rpg/...)
  src/calc_framework/
    dag/            ← DAG engine: graph compilation/execution/debug/templates
    data/           ← Attribute schema + DataContext + JsonDataLoader[T]
    search/         ← Full enumeration: search/parallel/persistence
    inverse/        ← Inverse engine: FormulaFitter SPI + GrowthParams + GameInverseAdapter
    editor/         ← Graph editor (PySide6 visual DAG)
    ui/             ← ComputeSheet (declarative layout panel) + ThemeManager
    plugin/         ← Plugin system (registry + builtins)
    config/         ← Adapter discovery/cache/hot-reload
    publish/        ← Adapter package validation + catalog generation
    semver.py       ← Semantic versioning utilities

games/endfield/     ← Endfield game package
  calc/             ← Calculation logic (zones/skills/equipment/search adapter)
  data/             ← Character/weapon/equipment JSON
  gui/              ← PySide6 GUI (app/controls/designer/shell/...)
  data_loading/     ← Data loaders + facades + web bridges
  tests/            ← pytest suite

web/                ← Web version
  frontend/         ← React + TypeScript
  backend/          ← FastAPI API

tools/              ← Dev tools (BWIKI scout/data pipeline/OCR/designer)
scripts/            ← Entry scripts (launcher/build/upload/deploy)
utils/              ← Shared utilities (gui/paths/updater)
```

---

## Core Design Decisions / 核心设计决策

| ADR | Topic / 主题 |
|-----|------|
| [ADR-0001](docs/adr/0001-code-layout-constraints.md) | Directory & file size constraints / 目录与文件规模约束 |
| [ADR-0003](docs/adr/0003-generic-calc-framework.md) | Generic calc framework design / 通用计算框架设计 |
| [ADR-0005](docs/adr/0005-data-schema-design.md) | Four-layer data schema / 四层数据 Schema |
| [ADR-0006](docs/adr/0006-calcpack-and-designer.md) | CalcPack & designer / 配置包与设计器 |
| [ADR-0013](docs/adr/0013-generic-inverse-engine.md) | Generic inverse engine SPI / 通用反推引擎 |
| [ADR-0020](docs/adr/0020-multiplicative-zones-decouple.md) | Multiplicative zone decoupling / 乘区解耦 |
| [ADR-0023](docs/adr/0023-standardized-game-package-architecture.md) | Standard game package architecture / 标准游戏包架构 |
| [ADR-0024](docs/adr/0024-universal-inverse-abstraction.md) | Inverse engine full abstraction — GrowthParams + GameInverseAdapter |
| [ADR-0025](docs/adr/0025-framework-consolidation.md) | Framework interface consistency — errors, themes, CalcWorker |

Full ADR list: [`docs/adr/`](docs/adr/).

---

## Key Abstractions / 关键抽象

| Component | Path | Description |
|-----------|------|-------------|
| `FormulaFitter` | `calc_framework.inverse.base` | SPI base class for formula fitting |
| `GrowthParams` | `calc_framework.inverse.base` | Typed container for growth formula params |
| `InverseEngine` | `calc_framework.inverse.engine` | Unified entry: `data_to_params()` / `params_to_curve()` |
| `GameInverseAdapter` | `calc_framework.inverse.schema` | ABC for game-specific inverse — declare schemas, auto-fit |
| `JsonDataLoader[T]` | `calc_framework.data.json_loader` | Generic lazy-load cache — eliminates get/reload boilerplate |
| `DataContextLoader` | `calc_framework.data.loader` | ABC for building DAG evaluation context |
| `ThemeManager` | `calc_framework.ui.theme` | Multi-theme QSS management (dark/light/high_contrast) |
| `CalcWorker` | `utils.gui.qt_worker` | Generic QThread+QObject background worker |

---

## Contributing / 贡献

See [`CONTRIBUTING.md`](CONTRIBUTING.md) / 见贡献指南。
