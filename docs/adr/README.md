# 架构决策记录（ADR）

> 本目录记录项目的关键架构决策。每个 ADR 编号唯一，按创建时间排序。

## 索引

<!-- ADR-INDEX:START -->
| 编号 | 状态 | 说明 |
|------|:----:|------|
| 0001 | ✅ | [代码目录与文件规模约束](0001-code-layout-constraints.md) |
| 0002 | ✅ | [可视化公式计算图编辑器](0002-formula-graph-editor.md) |
| 0003 | ✅ | [通用计算框架 — DAG 公式引擎与 AST 沙箱](0003-generic-calc-framework.md) |
| 0004 | ✅ | [项目统一蓝图 — 从计算器到平台的演进](0004-project-blueprint.md) |
| 0005 | ✅ | [标准数据录入规范 — 四层数据契约](0005-data-schema-design.md) |
| 0006 | ✅ | [.calcpack 打包格式与开发者工具](0006-calcpack-and-designer.md) |
| 0007 | ✅ | [终末地计算器→Calc Framework 迁移路线图](0007-endfield-migration-roadmap.md) |
| 0008 | ✅ | [框架差距分析 — 六大核心模块评估](0008-framework-gap-analysis.md) |
| 0009 | ✅ | [PySide6 GUI 迁移 — 完全依赖抽象框架](0009-pyside6-migration.md) |
| 0010 | — | [全品类通用游戏战斗数值仿真框架路线图](0010-universal-game-framework-roadmap.md) |
| 0011 | ✅ | [截图识装 — YOLO 目标检测 + OCR 数据提取 + 乘区块化](0011-ocr-data-extraction-and-zone-blocking.md) |
| 0012 | ✅ | [P3 多游戏启动器 + 应用商店 + 安装包](0012-p3-launcher-marketplace-installer.md) |
| 0013 | ✅ | [通用公式反推引擎 SPI](0013-generic-inverse-engine.md) |
| 0014 | ✅ | [GUI 框架从 CustomTkinter 迁移到 PySide6](0014-pyside6-migration.md) |
| 0015 | — | **空缺**（编号预留，未使用） |
| 0016 | ✅ | [重命名 adapters/endfield/ → calc_engine/endfield/](0016-refactor-rename-adapters-to-calc-engine.md) |
| 0017 | ✅ | [GUI 桥接层 — 消除三角依赖](0017-gui-bridge-layer.md) |
| 0018 | ✅ | [graph_editor ↔ dag 单向依赖重构](0018-graph-editor-dag-unidirectional.md) |
| 0019 | ✅ | [拆分 ui/viewer.py 职责](0019-split-viewer-py-responsibilities.md) |
| 0020 | ✅ | [multiplicative_zones 循环依赖解耦](0020-multiplicative-zones-decouple.md) |
| 0021 | ✅ | [移除 sys.path hack](0021-remove-sys-path-hacks.md) |
| 0022 | ✅ | [utils/ 职责归属清理](0022-utils-responsibility-cleanup.md) |
| 0023 | ✅ | [标准化游戏包架构](0023-standardized-game-package-architecture.md) |
| 0024 | ✅ | [通用逆推引擎完全抽象化 — GrowthFormula 双向公式系统](0024-universal-inverse-abstraction.md) |
| 0025 | ✅ | [框架接口一致性巩固 — 异常层次、DataContextLoader、主题、工具类统一](0025-framework-consolidation.md) |
| 0026 | ✅ | [多段等级曲线蓝图（CurveBlueprint）](0026-multi-segment-curve-blueprint.md) |
| 0027 | ✅ | [Web 浏览器计算（WASM）技术选型](0027-web-wasm-calc.md) |
| 0028 | ✅ | [MCP 计算器构建服务器](0028-mcp-builder-server.md) |

**注意**：`0002-migrate-to-pyside6.md` 为历史重复编号文件，已被 ADR-0014 取代，不列入索引。
<!-- ADR-INDEX:END -->
