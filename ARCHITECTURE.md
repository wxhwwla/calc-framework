# 架构概述（ARCHITECTURE）

> 本文档是项目架构的根级入口。详细设计见 [`docs/算法与架构.md`](docs/算法与架构.md)。
> 架构决策记录见 [`docs/adr/`](docs/adr/)。

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

## 系统分层

```
GUI Layer (PySide6 / React → FastAPI)
    ↓ framework_bridge.py
DAG Engine (calc_framework.dag)
    ↓           ↓
Data Layer    Search Engine
(JSON/Pydantic)  (全量枚举/并行)
    ↓
Adapter Layer (framework/adapters/{game}/)
```

## 目录结构

```
framework/          ← 通用计算框架（pip 包 calc-framework）
  adapters/         ← 各游戏适配包（endfield/arknights/moba/fps...）
  src/calc_framework/
    dag/            ← DAG 引擎：图编译/执行/调试/模板
    data/           ← 属性 Schema + DataContext
    search/         ← 全量搜索：枚举/并行/持久化
    inverse/        ← 逆推引擎：给定输出反推输入
    editor/         ← 图编辑器（PySide6 可视化 DAG）
    ui/             ← ComputeSheet（布局声明式面板）
    plugin/         ← 插件系统
    config/         ← 适配器发现/缓存/热重载
    publish/        ← 适配包校验 + 目录生成

games/endfield/     ← 终末地游戏包
  calc/             ← 计算逻辑（乘区/技能/装备/全量搜索适配）
  data/             ← 角色/武器/装备 JSON
  gui/              ← PySide6 GUI
  tests/            ← pytest 测试

web/                ← Web 版
  frontend/         ← React + TypeScript
  backend/          ← FastAPI API

tools/              ← 工具集（BWIKI 侦察/数据管线/OCR/设计器）
scripts/            ← 入口脚本（启动器/打包/上传/部署）
```

## 核心设计决策

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
| [ADR-0025](docs/adr/0025-framework-consolidation.md) | 框架接口一致性巩固 |

完整 ADR 列表见 [`docs/adr/`](docs/adr/)。

## 贡献

见 [`CONTRIBUTING.md`](CONTRIBUTING.md)。
