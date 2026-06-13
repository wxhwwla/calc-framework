# Architecture Overview

> This document is the root-level entry point for project architecture.
> Architecture Decision Records: [`docs/adr/`](docs/adr/).
>
> [:cn: 中文版](ARCHITECTURE_zh.md)

---

## Tech Stack

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
| i18n | react-i18next (Web) + DesktopTranslator/JSON (Desktop) |
| Deployment | PythonAnywhere (Web version) |

---

## System Layers

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

## Directory Structure

```
framework/          ← Generic calc framework (pip package calc-framework)
  adapters/         ← Game adapter packages (endfield/arknights/moba/fps/card_rpg/...)
  src/calc_framework/
    dag/            ← DAG engine: graph compilation/execution/debug/templates
    data/           ← Attribute schema + DataContext + JsonDataLoader[T]
    search/         ← Full enumeration: search/parallel/persistence
    inverse/        ← Inverse engine: FormulaFitter SPI + GrowthParams + GameInverseAdapter
    editor/         ← Graph editor (PySide6 visual DAG)
    ui/             ← ComputeSheet (declarative layout panel) + ThemeManager + DesktopTranslator (i18n)
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

## Core Design Decisions (ADRs)

| ADR | Topic |
|-----|-------|
| [ADR-0001](docs/adr/0001-code-layout-constraints.md) | Directory & file size constraints |
| [ADR-0003](docs/adr/0003-generic-calc-framework.md) | Generic calc framework design |
| [ADR-0005](docs/adr/0005-data-schema-design.md) | Four-layer data schema |
| [ADR-0006](docs/adr/0006-calcpack-and-designer.md) | CalcPack & designer |
| [ADR-0013](docs/adr/0013-generic-inverse-engine.md) | Generic inverse engine SPI |
| [ADR-0020](docs/adr/0020-multiplicative-zones-decouple.md) | Multiplicative zone decoupling |
| [ADR-0023](docs/adr/0023-standardized-game-package-architecture.md) | Standard game package architecture |
| [ADR-0024](docs/adr/0024-universal-inverse-abstraction.md) | Inverse engine full abstraction — GrowthParams + GameInverseAdapter |
| [ADR-0025](docs/adr/0025-framework-consolidation.md) | Framework interface consistency — errors, themes, CalcWorker |

Full ADR list: [`docs/adr/`](docs/adr/).

---

## Key Abstractions

| Component | Path | Description |
|-----------|------|-------------|
| `FormulaFitter` | `calc_framework.inverse.base` | SPI base class for formula fitting |
| `GrowthParams` | `calc_framework.inverse.base` | Typed container for growth formula params |
| `InverseEngine` | `calc_framework.inverse.engine` | Unified entry: `data_to_params()` / `params_to_curve()` |
| `GameInverseAdapter` | `calc_framework.inverse.schema` | ABC for game-specific inverse — declare schemas, auto-fit |
| `JsonDataLoader[T]` | `calc_framework.data.json_loader` | Generic lazy-load cache — eliminates get/reload boilerplate |
| `DataContextLoader` | `calc_framework.data.loader` | ABC for building DAG evaluation context |
| `ThemeManager` | `calc_framework.ui.theme` | Multi-theme QSS management (dark/light/high_contrast) |
| `DesktopTranslator` | `calc_framework.ui.i18n` | Desktop GUI i18n singleton — JSON-based translations with fallback, interpolation, thread-safe |
| `CalcWorker` | `utils.gui.qt_worker` | Generic QThread+QObject background worker |

---

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md).
