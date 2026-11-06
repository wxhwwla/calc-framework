[![GitHub stars](https://img.shields.io/github/stars/wxhwwla/calc-framework?style=social)](https://github.com/wxhwwla/calc-framework)
[![AtomGit stars](https://atomgit.com/wxhwwla/calc-framework/star/badge.svg)](https://atomgit.com/wxhwwla/calc-framework)
[![Game CI](https://github.com/wxhwwla/calc-framework/actions/workflows/ci.yml/badge.svg?branch=develop)](https://github.com/wxhwwla/calc-framework/actions/workflows/ci.yml)
[![Framework CI](https://github.com/wxhwwla/calc-framework/actions/workflows/framework-ci.yml/badge.svg?branch=develop)](https://github.com/wxhwwla/calc-framework/actions/workflows/framework-ci.yml)
[![Web CI](https://github.com/wxhwwla/calc-framework/actions/workflows/web-ci.yml/badge.svg?branch=develop)](https://github.com/wxhwwla/calc-framework/actions/workflows/web-ci.yml)
[![Security Audit](https://github.com/wxhwwla/calc-framework/actions/workflows/security-audit.yml/badge.svg?branch=develop)](https://github.com/wxhwwla/calc-framework/actions/workflows/security-audit.yml)

# Calc Framework — Universal Game Damage Calculator

> A universal game calculation framework. Currently supports **Arknights: Endfield**, **Arknights**, and **Infinite Lagrange**.
>
> [:cn: 中文文档](README_zh.md)

---

## 🚀 Get Started

<table>
<tr>
<td align="center" width="50%">

### 🎮 I'm a Player

**Use the calculator right now — no install needed.**

[**Open Web App →**](https://dove-magnitude-runner.ngrok-free.dev)

*or* [Download Desktop App](https://github.com/wxhwwla/calc-framework/releases)

> 📖 [Player Guide](docs/player-guide.md)

</td>
<td align="center" width="50%">

### 🔧 I'm a Developer

**Build a calculator for my game, or contribute.**

```bash
git clone https://github.com/wxhwwla/calc-framework
cd calc-framework
python scripts/main_launcher.py
# Windows, no console window: pythonw scripts/main_launcher.py
```

**Or let your AI build the calculator:** the repo ships a Model Context Protocol server that exposes the DAG generator, scaffolder, validator, and `.calcpack` packer as deterministic tools.

```bash
pip install -r requirements-mcp.txt
python -m tools.calc_mcp --project-dir .
```

Point your MCP client (Claude Code / Cursor / VS Code) at that command — see [操作指令集 §2.4](docs/操作指令集.md) and [ADR-0028](docs/adr/0028-mcp-builder-server.md).

> 🏗 [Quick Start ↓](#quick-start) · [Create a Calculator](docs/制造游戏计算器完整流程.md)

</td>
</tr>
</table>

---

## Documentation Map

| Document | Audience |
|----------|----------|
| **This page** | First-time visitors, GitHub homepage |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) ([中文](ARCHITECTURE_zh.md)) | System architecture overview |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) ([中文](CONTRIBUTING_zh.md)) | How to contribute |
| [`docs/contributor-pathways.md`](docs/contributor-pathways.md) | Player → Contributor pathways |
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
│   └── adapters/                 #   Game adapters (endfield, arknights, card_rpg, fps, moba, wjdlglr)
├── web/                          # React + FastAPI full-stack web app
│   ├── backend/                  #   FastAPI backend (/api/*)
│   │   └── api/                  #     routes + internal/ entity/ search_lib/ … (see docs §4.188)
│   ├── frontend/                 #   React frontend (TypeScript + MUI + Vite)
│   └── hub/                      #   Calc Hub — static marketplace
├── games/                        # Game adapter packages
│   ├── endfield/                 #   Endfield damage calculator (calc + gui + data + tests)
│   ├── arknights/                #   Arknights calculator (DAG + GUI + tests)
│   └── wjdlglr/                  #   Infinite Lagrange entry (generic CalcPackViewer)
├── docs/                         # Project documentation
├── tools/                        # Dev tools (BWIKI/wiki_scout, data pipeline, OCR, designer, calc_mcp)
├── scripts/                      # Entry scripts (launcher, build, dev toolkit)
├── release_bundle/               # Release layout config
├── installer/                    # NSIS installer
├── .github/                      # CI workflows, issue templates
├── LICENSE · DATA_LICENSE · CONTEXT.md · CONTRIBUTING.md
└── NOTICES.md                    # Third-party notices
```

---

## Quick Start

### Option 1: Web Demo (No Install)

→ **[dove-magnitude-runner.ngrok-free.dev](https://dove-magnitude-runner.ngrok-free.dev)**

> Hosted on the maintainer's PC via ngrok; the free ngrok plan may show a one-time "Visit Site" interstitial per browser per week.

### Option 2: Desktop App

Download the installer from [Releases](https://github.com/wxhwwla/calc-framework/releases).

### Option 3: Run from Source (Developers)

```powershell
# 1. Clone
git clone https://github.com/wxhwwla/calc-framework
cd calc-framework

# 2. Install framework core
cd framework
pip install -e ".[dev]"
cd ..

# 3. Install game adapter
cd games/endfield
pip install -e ".[dev]"
cd ../..

# 4. Launch from the repository root
python -m games.endfield.main
```

> Wheel install: install this repository's framework first (local wheel or editable, ≥ 0.3.1), then the `games/endfield` wheel. Older PyPI framework builds lack `calc_framework.ui.i18n`.

<details>
<summary>Troubleshooting</summary>

- **`pip install -e ".[dev]"` fails**: Ensure Python ≥ 3.11. Try `pip install -e .` (without dev deps) first, then install dev tools separately.
- **`No module named 'calc_framework'`**: Install the framework first: `cd framework && pip install -e .`
- **OCR not working**: Install optional OCR deps: `pip install -e ".[ocr]"` (requires ~2 GB for TorchVision).

</details>

### Option 4: Web Version (Local)

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
- BWIKI data crawling: 440 operators with full stats
- 28 attributes + 5 custom functions + 51-node DAG

### Infinite Lagrange Calculator

- Ship category → ship → weapon cascade; stats from the game wiki (571 ship/weapon records)
- Eight damage zones plus a dedicated hit-rate zone: `(target evasion + hit bonus) × (1 + base hit)`, clamped to 5%–95%, then ±N(0, 0.03) fluctuation
- 42 outputs across two tabs (calculation / zone breakdown); energy vs. kinetic armor selected automatically from the weapon
- Same adapter serves desktop (`--game wjdlglr`) and Web (`/wjdlglr`)

### Generic Framework

- **Visual DAG Editor**: Drag-and-drop node editor (Web: ReactFlow, Desktop: PySide6) — build damage formulas visually, no code required
- **DAG Engine**: 8 node types (const/var/unary/binary/condition/expr/user-input/subgraph-call), topological sort, AST sandbox, subgraph expansion, block-level caching, incremental evaluation
- **Inverse Engine**: `data_to_params()` / `params_to_curve()` — bidirectional formula fitting for any game
- **Search Engine**: Top-N enumeration, parallel execution, cancel tokens, SQLite persistence
- **ComputeSheet**: Declarative UI — consumes `layout.json` + DAG variables → auto-renders controls
- **Plugin System**: Registry pattern + 3 built-in plugins (crit/dodge/distance) + `.calcplugin` format
- **Cross-genre**: Verified with card_rpg (9 nodes), moba (7), fps (8) adapters, plus a wjdlglr eight-zone adapter (104 nodes, 16 target DPM outputs with a dedicated hit-rate zone, three-level ship/weapon cascade, weapon detail panel, energy/kinetic armor selection)
- **Theme Manager**: Dark / Light / High Contrast with dynamic QSS generation
- **i18n**: Web (react-i18next, ~890 entries per language) + Desktop (DesktopTranslator, 1046 keys per language, en/zh-CN)
- **AI Build Recommendation**: Natural language → optimal loadout, multi-turn chat, semantic search, AI formula parsing
- **MCP Builder Server**: `tools/calc_mcp/` exposes 13 deterministic tools (templates, schemas, guides, generate, scaffold, validate, smoke-test, pack/import) so a host AI can build a new game calculator end-to-end from a cloned repo
- **SaaS API**: API Key management + rate limiting + usage statistics

### Web Version

| Web Page | Desktop Equivalent | Route |
|----------|-------------------|-------|
| Damage Calculator | `main.py` (desktop) / FastAPI+React (web) | `/` |
| Infinite Lagrange Calculator | `games/wjdlglr/main.py` / generic `AdapterGamePage` | `/wjdlglr` |
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
cd framework && pytest tests/ -q

# Endfield tests (full suite)
cd games/endfield && pytest tests/ -q
```

[![CI](https://github.com/wxhwwla/calc-framework/actions/workflows/ci.yml/badge.svg?branch=develop)](https://github.com/wxhwwla/calc-framework/actions/workflows/ci.yml)

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

---

## Project Info

| Resource | Link |
|----------|------|
| **Changelog** | [`CHANGELOG.md`](CHANGELOG.md) |
| **Security Policy** | [`SECURITY.md`](SECURITY.md) |
| **Contributing** | [`CONTRIBUTING.md`](CONTRIBUTING.md) |
| **Code of Conduct** | [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) |
| **Architecture** | [`ARCHITECTURE.md`](ARCHITECTURE.md) / [`ARCHITECTURE_zh.md`](ARCHITECTURE_zh.md) |
