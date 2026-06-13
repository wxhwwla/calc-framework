[![GitHub stars](https://img.shields.io/github/stars/wxhwwla/calc-framework?style=social)](https://github.com/wxhwwla/calc-framework)
[![AtomGit stars](https://atomgit.com/wxhwwla/calc-framework/star/badge.svg)](https://atomgit.com/wxhwwla/calc-framework)

# Calc Framework — Universal Game Damage Calculator

> A universal game calculation framework. Currently supports **Arknights: Endfield** and **Arknights**.
>
> **Web Demo**: [wxhwwla.pythonanywhere.com](https://wxhwwla.pythonanywhere.com)
>
> [:cn: 中文文档](README_zh.md)

---

## Documentation Map

| Document | Audience |
|----------|----------|
| **This page** | First-time visitors, GitHub homepage |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) ([中文](ARCHITECTURE_zh.md)) | System architecture overview |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) ([中文](CONTRIBUTING_zh.md)) | How to contribute |
| [`CONTEXT.md`](CONTEXT.md) ([中文](CONTEXT_zh.md)) | Domain terminology |
| [`docs/项目目标.md`](docs/项目目标.md) | Project vision & roadmap (ZH) |
| [`docs/操作指令集.md`](docs/操作指令集.md) | Command reference (ZH) |
| [`docs/数据来源与许可.md`](docs/数据来源与许可.md) | Licensing & data sources (ZH) |
| [`games/endfield/README.md`](games/endfield/README.md) | Endfield package details |

---

## Directory Overview

```
[repo root]/
├── framework/                    # calc-framework — generic pip package
│   ├── src/calc_framework/       #   DAG engine, inverse engine, data, UI, search, plugin
│   └── adapters/                 #   Game adapters (endfield, arknights, card_rpg, fps, moba)
├── web/                          # React + FastAPI full-stack web app
│   ├── backend/                  #   FastAPI backend (/api/*)
│   ├── frontend/                 #   React frontend (TypeScript + MUI + Vite)
│   └── hub/                      #   Calc Hub — static marketplace
├── games/                        # Game adapter packages
│   ├── endfield/                 #   Endfield damage calculator (calc + gui + data + tests)
│   └── arknights/                #   Arknights calculator (DAG + GUI + tests)
├── docs/                         # Project documentation
├── tools/                        # Dev tools (BWIKI scout, data pipeline, OCR, designer)
├── scripts/                      # Entry scripts (launcher, build, dev toolkit)
├── release_bundle/               # Release layout config
├── installer/                    # NSIS installer
├── .github/                      # CI workflows, issue templates
├── LICENSE · DATA_LICENSE · CONTEXT.md · CONTRIBUTING.md
└── NOTICES.md                    # Third-party notices
```

---

## Quick Start

### Recommended: Launcher

```powershell
# Auto-discovers installed game adapters
python scripts/main_launcher.py
```

### Direct Launch

```powershell
# Endfield Calculator
cd games/endfield
pip install -e ".[dev]"
python -m games.endfield.main
```

```powershell
# Developer Toolkit
python scripts/main_dev_toolkit.py
```

### Web Version

```powershell
# Backend
cd web/backend && pip install -r requirements.txt && uvicorn main:app --reload --port 8002

# Frontend (separate terminal)
cd web/frontend && npm install && npm run dev
```

---

## Features

### Endfield Damage Calculator

- Character / weapon / equipment selection with dual-tab GUI (Calculate + Advanced)
- 15-zone damage formula driven by DAG engine (framework `ComputeSheet`)
- Full-search enumeration with Top-N tracking, parallel execution, SQLite resume
- Multi-skill weighted total damage, fixed loadout (0–4 pieces)
- Equipment affix parsing, priority sorting, non-beneficial pruning
- OCR screenshot import → auto-fill calculator (TorchVision + EasyOCR)
- Formula inverse fitting: data → 4-parameter growth formula
- Preset JSON import/export, batch comparison, damage dashboard (matplotlib)
- Survival estimation, enemy parameter panel, manual buff controls

### Arknights Calculator

- Operator selection by star / profession / branch with skill parser
- Physical / Magic / True damage calculation via DAG engine
- BWIKI data crawling: 420+ operators with full stats
- 28 attributes + 5 custom functions + 51-node DAG

### Generic Framework

- **DAG Engine**: 9 node types, topological sort, AST sandbox, subgraph expansion, block-level caching
- **Inverse Engine**: `data_to_params()` / `params_to_curve()` — bidirectional formula fitting for any game
- **Search Engine**: Top-N enumeration, parallel execution, cancel tokens, SQLite persistence
- **ComputeSheet**: Declarative UI — consumes `layout.json` + DAG variables → auto-renders controls
- **Plugin System**: Registry pattern + 3 built-in plugins (crit/dodge/distance) + `.calcplugin` format
- **Cross-genre**: Verified with card_rpg (9 nodes), moba (7), fps (8) adapters
- **Theme Manager**: Dark / Light / High Contrast with dynamic QSS generation
- **i18n**: Web (react-i18next, ~500+ keys, 98 files) + Desktop (DesktopTranslator, 282 keys, 15 files, en/zh-CN)

### Web Version

| Web Page | Desktop Equivalent | Route |
|----------|-------------------|-------|
| Damage Calculator | `games/endfield/main.py` | `/` |
| Data Designer | Dev toolkit | `/designer` |
| Pack Designer | Dev toolkit | `/pack-designer` |
| Calc Hub Marketplace | — | `/marketplace` |

The Web version shares `layout.json` / `attr_schema.json` / DAG files / data JSON with the desktop version. One codebase, two rendering targets.

---

## Framework Quick API

```python
from calc_framework.inverse.engine import InverseEngine

engine = InverseEngine()

# Data → 4 params (any level count, any game)
params = engine.data_to_params([100, 105, 110, 115, 120])
# GrowthParams(base=100, growth=5, divisor=1, offset=0)

# 4 params + levels → curve
curve = engine.params_to_curve(params, num_levels=90)
# [100.0, 105.0, ..., 545.0]
```

```python
from calc_framework.inverse.schema import GameInverseAdapter, InverseSchema

# New game integration: declarative, zero dispatch code
class MyGame(GameInverseAdapter):
    @property
    def schemas(self):
        return [InverseSchema(length=60), InverseSchema(length=10)]
    def default_formula(self): return "floor_linear"

adapter = MyGame()
result = adapter.fit(data)  # auto-match by data length
```

---

## Testing

```powershell
# Framework tests
cd framework && pytest tests/ -q     # ~855 passed

# Endfield tests (full suite)
cd games/endfield && pytest tests/ -q  # ~1109 passed
```

[![CI](https://github.com/wxhwwla/calc-framework/actions/workflows/ci.yml/badge.svg)](https://github.com/wxhwwla/calc-framework/actions/workflows/ci.yml)

---

## Community

| Channel | Purpose |
|---------|---------|
| [GitHub Issues](https://github.com/wxhwwla/calc-framework/issues) | Bug reports / feature requests |
| [GitHub Discussions](https://github.com/wxhwwla/calc-framework/discussions) | Technical discussion / Q&A |
| QQ Group: `1040157567` | Chinese community |
| Discord | Invite link TBD |

---

## License & Data

| Content | License |
|---------|---------|
| **Software** | [AGPL-3.0](LICENSE) (default) or written commercial license |
| **Game Data** | [DATA_LICENSE](DATA_LICENSE) — non-commercial use only |
| **Full Details** | [`docs/数据来源与许可.md`](docs/数据来源与许可.md) |
| **Third-Party** | [`NOTICES.md`](NOTICES.md) |

Use or distribution constitutes acceptance of the applicable license.
