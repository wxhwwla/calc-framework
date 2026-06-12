# 架构概述

> 本文档是项目架构的根级入口。
> 架构决策记录：[`docs/adr/`](docs/adr/)。
>
> [:us: English](ARCHITECTURE.md)

---

## 技术栈

| 组件 | 技术选型 |
|------|----------|
| 计算引擎 | Python 3.12+（DAG + 逆推引擎 + 全量搜索） |
| 桌面 GUI | PySide6（Qt 6） |
| Web 前端 | React + TypeScript + Vite + MUI v6 |
| Web 后端 | FastAPI + Uvicorn |
| 数据层 | JSON 文件 + Pydantic 校验 |
| 测试框架 | pytest + pytest-cov |
| 代码检查 | ruff（lint + format）+ pyright |
| 打包 | PyInstaller（onedir）+ NSIS 安装器 |
| 容器 | Docker + docker-compose |
| 部署 | PythonAnywhere（Web 版） |

---

## 系统分层

```
GUI Layer (PySide6 / React → FastAPI)
    ↓ framework_bridge.py
DAG Engine (calc_framework.dag)
    ↓           ↓
Data Layer    Search Engine
(JSON/Pydantic)  (枚举/并行)
    ↓
Adapter Layer (framework/adapters/{game}/)
    ↓
Inverse Engine (calc_framework.inverse)
    — 任意游戏双向公式拟合
```

---

## 目录结构

```
framework/          ← 通用计算框架（pip 包 calc-framework）
  adapters/         ← 各游戏适配包（endfield/arknights/moba/fps/card_rpg/...）
  src/calc_framework/
    dag/            ← DAG 引擎：图编译/执行/调试/模板
    data/           ← 属性 Schema + DataContext + JsonDataLoader[T]
    search/         ← 全量搜索：枚举/并行/持久化
    inverse/        ← 逆推引擎：FormulaFitter SPI + GrowthParams + GameInverseAdapter
    editor/         ← 图编辑器（PySide6 可视化 DAG）
    ui/             ← ComputeSheet（布局声明式面板）+ ThemeManager
    plugin/         ← 插件系统（注册表 + 内置插件）
    config/         ← 适配器发现/缓存/热重载
    publish/        ← 适配包校验 + 目录生成
    semver.py       ← 语义化版本工具

games/endfield/     ← 终末地游戏包
  calc/             ← 计算逻辑（乘区/技能/装备/搜索适配器）
  data/             ← 角色/武器/装备 JSON
  gui/              ← PySide6 GUI（app/controls/designer/shell/...）
  data_loading/     ← 数据加载器 + facade + Web 桥接
  tests/            ← pytest 测试套件

web/                ← Web 版
  frontend/         ← React + TypeScript
  backend/          ← FastAPI API

tools/              ← 工具集（BWIKI 侦察/数据管线/OCR/设计器）
scripts/            ← 入口脚本（启动器/打包/上传/部署）
utils/              ← 共享工具库（gui/paths/updater）
```

---

## 核心设计决策（ADR）

| ADR | 主题 |
|-----|------|
| [ADR-0001](docs/adr/0001-code-layout-constraints.md) | 目录与文件规模约束 |
| [ADR-0003](docs/adr/0003-generic-calc-framework.md) | 通用计算框架设计 |
| [ADR-0005](docs/adr/0005-data-schema-design.md) | 四层数据 Schema |
| [ADR-0006](docs/adr/0006-calcpack-and-designer.md) | 配置包与设计器 |
| [ADR-0013](docs/adr/0013-generic-inverse-engine.md) | 通用反推引擎 SPI |
| [ADR-0020](docs/adr/0020-multiplicative-zones-decouple.md) | 乘区解耦 |
| [ADR-0023](docs/adr/0023-standardized-game-package-architecture.md) | 标准游戏包架构 |
| [ADR-0024](docs/adr/0024-universal-inverse-abstraction.md) | 逆推引擎完全抽象化 — GrowthParams + GameInverseAdapter |
| [ADR-0025](docs/adr/0025-framework-consolidation.md) | 框架接口一致性巩固 — 异常、主题、CalcWorker |

完整 ADR 列表：[`docs/adr/`](docs/adr/)。

---

## 关键抽象

| 组件 | 路径 | 说明 |
|------|------|------|
| `FormulaFitter` | `calc_framework.inverse.base` | 公式拟合 SPI 基类 |
| `GrowthParams` | `calc_framework.inverse.base` | 类型化成长公式参数容器 |
| `InverseEngine` | `calc_framework.inverse.engine` | 统一入口：`data_to_params()` / `params_to_curve()` |
| `GameInverseAdapter` | `calc_framework.inverse.schema` | 游戏逆推适配器 ABC — 声明 schemas，自动拟合 |
| `JsonDataLoader[T]` | `calc_framework.data.json_loader` | 通用懒加载缓存 — 消除 get/reload 重复 |
| `DataContextLoader` | `calc_framework.data.loader` | DAG 求值上下文构建 ABC |
| `ThemeManager` | `calc_framework.ui.theme` | 多主题 QSS 管理（暗色/亮色/高对比度） |
| `CalcWorker` | `utils.gui.qt_worker` | 通用 QThread+QObject 后台线程 |

---

## 贡献

见 [`CONTRIBUTING_zh.md`](CONTRIBUTING_zh.md)。
