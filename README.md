[![GitHub stars](https://img.shields.io/github/stars/wxhwwla/calc-framework?style=social)](https://github.com/wxhwwla/calc-framework)
[![AtomGit stars](https://atomgit.com/wxhwwla/calc-framework/star/badge.svg)](https://atomgit.com/wxhwwla/calc-framework)

# Calc Framework — Universal Game Damage Calculator / 通用游戏计算框架

> A universal game calculation framework. Currently supports **Arknights: Endfield** and **Arknights**.
>
> **Web Demo（在线版）**: [wxhwwla.pythonanywhere.com](https://wxhwwla.pythonanywhere.com)
>
> 通用游戏计算框架 · 目前支持《明日方舟：终末地》与《明日方舟》

---

## Documentation Map / 文档导航

| Document | Audience / 适合谁 |
|----------|------|
| **This page（本页）** | First-time visitors, GitHub homepage / 首次访问、GitHub 首页 |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | System architecture overview / 系统架构概览 |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | How to contribute / 如何贡献 |
| [`CONTEXT.md`](CONTEXT.md) | Domain terminology / 领域术语表 |
| [`docs/项目目标.md`](docs/项目目标.md) | Project vision & roadmap (ZH) / 项目愿景与路线图 |
| [`docs/操作指令集.md`](docs/操作指令集.md) | Command reference (ZH) / 操作命令速查 |
| [`docs/算法与架构.md`](docs/算法与架构.md) | Algorithm details (ZH, partially outdated) / 算法与架构细节 |
| [`docs/数据来源与许可.md`](docs/数据来源与许可.md) | Licensing & data sources (ZH) / 许可与数据来源 |
| [`games/endfield/README.md`](games/endfield/README.md) | Endfield package details / 终末地包详细说明 |

---

## Directory Overview / 目录一览

```
[repo root]/
├── framework/                    # [Framework] calc-framework — generic pip package
│   ├── src/calc_framework/       #   DAG engine, inverse engine, data, UI, search, plugin
│   └── adapters/                 #   Game adapters (endfield, arknights, card_rpg, fps, moba)
├── web/                          # [Web] React + FastAPI full-stack web app
│   ├── backend/                  #   FastAPI backend (/api/*)
│   ├── frontend/                 #   React frontend (TypeScript + MUI + Vite)
│   └── hub/                      #   Calc Hub — static marketplace
├── games/                        # [Games] Game adapter packages
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

## Quick Start / 快速开始

### Recommended: Launcher / 推荐：启动器

```powershell
# Launcher — auto-discovers installed game adapters
# 自动发现已安装的游戏适配包
python scripts/main_launcher.py
```

### Direct Launch / 直接启动

```powershell
# Endfield Calculator / 终末地计算器
cd games/endfield
pip install -e ".[dev]"
python -m games.endfield.main
```

```powershell
# Developer Toolkit / 开发者工具箱
python scripts/main_dev_toolkit.py
```

### Web Version / Web 版

```powershell
# Backend / 后端
cd web/backend && pip install -r requirements.txt && uvicorn main:app --reload --port 8002

# Frontend / 前端 (separate terminal / 新终端)
cd web/frontend && npm install && npm run dev
```

---

## Features / 功能概览

### Endfield Damage Calculator / 终末地伤害计算器

- Character / weapon / equipment selection with dual-tab GUI (Calculate + Advanced)
- 15-zone damage formula driven by DAG engine (framework `ComputeSheet`)
- Full-search enumeration with Top-N tracking, parallel execution, SQLite resume
- Multi-skill weighted total damage, fixed loadout (0–4 pieces)
- Equipment affix parsing, priority sorting, non-beneficial pruning
- OCR screenshot import → auto-fill calculator (TorchVision + EasyOCR)
- Formula inverse fitting: data → 4-parameter growth formula
- Preset JSON import/export, batch comparison, damage dashboard (matplotlib)
- Survival estimation, enemy parameter panel, manual buff controls

### Arknights Calculator / 明日方舟计算器

- Operator selection by star / profession / branch with skill parser
- Physical / Magic / True damage calculation via DAG engine
- BWIKI data crawling: 420+ operators with full stats
- 28 attributes + 5 custom functions + 51-node DAG

### Generic Framework / 通用框架

- **DAG Engine**: 9 node types, topological sort, AST sandbox, subgraph expansion, block-level caching
- **Inverse Engine**: `data_to_params()` / `params_to_curve()` — bidirectional formula fitting for any game
- **Search Engine**: Top-N enumeration, parallel execution, cancel tokens, SQLite persistence
- **ComputeSheet**: Declarative UI — consumes `layout.json` + DAG variables → auto-renders controls
- **Plugin System**: Registry pattern + 3 built-in plugins (crit/dodge/distance) + `.calcplugin` format
- **Cross-genre**: Verified with card_rpg (9 nodes), moba (7), fps (8) adapters
- **Theme Manager**: Dark / Light / High Contrast with dynamic QSS generation

### Web Version / Web 版

| Web Page | Desktop Equivalent | Route |
|----------|-------------------|-------|
| Damage Calculator | `games/endfield/main.py` | `/` |
| Data Designer | Dev toolkit | `/designer` |
| Pack Designer | Dev toolkit | `/pack-designer` |
| Calc Hub Marketplace | — | `/marketplace` |

The Web version shares `layout.json` / `attr_schema.json` / DAG files / data JSON with the desktop version.
Both render the same declarations — one codebase, two rendering targets.

---

## Framework Quick API / 框架速览

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

## Testing / 测试

```powershell
# Framework tests / 框架测试
cd framework && pytest tests/ -q     # 1019 passed

# Endfield tests / 终末地测试
cd games/endfield && pytest tests/calculation/ tests/data_loading/ -q  # 693 passed
```

[![CI](https://github.com/wxhwwla/calc-framework/actions/workflows/ci.yml/badge.svg)](https://github.com/wxhwwla/calc-framework/actions/workflows/ci.yml)

---

## Community / 社区与交流

| Channel | Purpose |
|---------|---------|
| [GitHub Issues](https://github.com/wxhwwla/calc-framework/issues) | Bug reports / feature requests（推荐） |
| [GitHub Discussions](https://github.com/wxhwwla/calc-framework/discussions) | Technical discussion / Q&A |
| QQ Group: `1040157567` | Chinese community（建设中） |
| Discord | Invite link TBD |

---

## License & Data / 许可证与数据来源

| Content | License |
|---------|---------|
| **Software** | [AGPL-3.0](LICENSE) (default) or written commercial license |
| **Game Data** | [DATA_LICENSE](DATA_LICENSE) — non-commercial use only |
| **Full Details** | [`docs/数据来源与许可.md`](docs/数据来源与许可.md) |
| **Third-Party** | [`NOTICES.md`](NOTICES.md) |

Use or distribution constitutes acceptance of the applicable license.
