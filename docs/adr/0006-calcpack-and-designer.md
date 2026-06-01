# ADR-0006：.calcpack 打包格式与开发者工具

**状态**：已批准  
**日期**：2026-05-28  
**决策者**：维护者  
**影响范围**：`tools/designer/`、`framework/src/calc_framework/`、`compute_sheet` 用户 GUI

---

## 1. 概述

本文档定义两个紧密配合的模块：

- **`.calcpack` 打包格式**：将游戏适配包（DAG 公式、数据、UI 布局、主题）打包为单文件 ZIP 的标准。
- **开发者工具**：生成 `.calcpack` 的独立 GUI 应用，集成数据录入、布局编辑、主题编辑功能。

二者共同实现 ADR-0003 决策 #3（公式/Schema/UI 与数据分离）和 ADR-0004 阶段四（平台化）的基础设施。

---

## 2. .calcpack 打包格式

### 2.1 格式选择

| 方案 | 结论 |
|------|------|
| 裸目录 | 开发调试用，不适合分发 |
| 单 JSON 文件 | 全量加载慢，不支持按需读 |
| **ZIP 包 (.calcpack)** | ✅ Python `zipfile` 按路径读取，零解压开销，单文件分发 |

**决策**：ZIP 格式，扩展名 `.calcpack`。

### 2.2 目录结构（ZIP 内部路径）

```yaml
meta.json                       # [必填] 适配包元信息
dag/
  formula.dag.json              # [必填] 主公式 DAG 图
  subgraphs/                    # [可选] 子图文件夹
    *.dag.json
ui/
  layout.json                   # [必填] UI 布局定义
  theme.json                    # [可选] 主题配置
data/
  characters.json               # [可选] 角色数据
  weapons.json                  # [可选] 武器数据
  equipments.json               # [可选] 装备数据
  enemies.json                  # [可选] 敌方数据
  mounts.json                   # [可选] 坐骑/载具数据
  config.json                   # [可选] 适配器配置（默认值、索引规则等）
```

### 2.3 meta.json

继承 ADR-0003 §6.2，新增 `theme` 和 `entry` 字段：

```json
{
  "name": "终末地伤害计算",
  "game": "明日方舟：终末地",
  "version": "3.0.0",
  "schema_version": "dag-v1",
  "author": "",
  "description": "终末地 15 乘区伤害公式",
  "entry_dag": "dag/formula.dag.json",
  "ui_layout": "ui/layout.json",
  "ui_theme": "ui/theme.json",
  "entry_data": ["data/characters.json", "data/weapons.json", "data/equipments.json"]
}
```

### 2.4 theme.json

```json
{
  "schema_version": "theme-v1",
  "name": "终末地深色主题",
  "font": {
    "family": "Microsoft YaHei",
    "size": 12,
    "weight": "normal"
  },
  "colors": {
    "primary": "#0078D4",
    "background": "#1E1E1E",
    "surface": "#2D2D2D",
    "text": "#F0F0F0",
    "text_secondary": "#A0A0A0",
    "border": "#3D3D3D",
    "success": "#4ECDC4",
    "warning": "#FFD700",
    "error": "#E74C3C"
  },
  "spacing": {
    "padding": 8,
    "gap": 4
  }
}
```

---

## 3. 开发者工具架构

### 3.1 目录位置

```
tools/designer/               # 开发者工具，与 data_pipeline 同层级
├── __init__.py
├── __main__.py               # python -m tools.designer
├── app.py                    # MainWindow（三页签）
├── exporter.py               # .calcpack 导出器
├── data_editor/
│   ├── __init__.py
│   └── panel.py              # 数据录入面板（调用 data_pipeline）
├── layout_editor/
│   ├── __init__.py
│   ├── canvas.py             # QGraphicsView 画布 + 网格吸附
│   └── collision.py          # 碰撞检测
├── theme_editor/
│   ├── __init__.py
│   └── panel.py              # 主题编辑器
```

### 3.2 主窗口布局

```
┌─────────────────────────────────────────────────┐
│  [数据录入]  [布局编辑]  [主题/导出]    ← 页签栏 │
├─────────────────────────────────────────────────┤
│                                                   │
│  内容区域（按页签切换）                            │
│                                                   │
├─────────────────────────────────────────────────┤
│  导出 .calcpack →  状态栏                        │
└─────────────────────────────────────────────────┘
```

### 3.3 页面一：数据录入

功能：
- 加载现有 `.calcpack` 或 JSON 数据文件
- 用 `tools/data_pipeline/` 的标准四层 schema 编辑实体
- 导入 CSV / 拖拽 JSON
- 实时校验（调用 `schema_check`）
- 保存到内存中的适配包

### 3.4 页面二：布局编辑器

继承并升级现有的 `LayoutEditorWidget`：

| 现有 | 升级后 |
|------|--------|
| QListWidget + QCheckBox | QGraphicsView 画布 |
| 无坐标概念 | 网格吸附（控制间距） |
| 无碰撞检测 | 实时碰撞高亮 + 提示 |
| 固定主题 | 可选预览主题 |
| 导出 layout.json | 写入内存适配包 |

网格参数：
- 列数：用户自定义（默认 12）
- 间距（gutter）：用户自定义（默认 8px）
- 吸附开关
- 碰撞检测开关

### 3.5 页面三：主题/导出

左侧：
- 字体选择（族、大小、粗细）
- 色板编辑（primary/background/surface/text 等）
- 实时预览

右侧：
- 导出按钮 → `.calcpack`
- 可选包含哪些数据文件

---

## 4. 数据流

```
开发者工具
├── 页面一：data_editor
│   ├── 加载 → `tools.data_pipeline` schema
│   ├── 编辑 → 内存 dict 树
│   └── 校验 → `schema_check.validate_all`
├── 页面二：layout_editor
│   ├── 画布编辑 → `calc_framework.editor`
│   └── 碰撞检测 → `collision.py`
├── 页面三：theme_editor
│   └── 主题配置 → `theme.json`
└── 导出
    ├── `exporter.build_calcpack()` → ZIP
    └── 输出 → `xxx.calcpack`

                        ↓

用户 GUI (ComputeSheet)
├── `python -m calc_framework path/to/game.calcpack`
├── zipfile 读取内部 JSON
├── DAG engine 求值
└── 渲染计算表
```

---

## 5. 未决定事项

| 事项 | 说明 |
|------|------|
| 签名/校验 | 是否加入 SHA256 manifest 防止篡改，待分发需求明确 |
| 增量更新 | 能否只替换包内单文件，待多版本场景出现 |
| 市场/索引 | 中心化的 `.calcpack` 索引，待 Phase 4 |

---

## 6. 多游戏双轨说明（2026-06-02）

| 游戏 | 桌面入口 | `.calcpack` / CalcPackViewer |
|------|----------|------------------------------|
| 终末地 | `scripts/main.py`（完整 GUI） | 设计器导出 + Hub 上传 |
| 明日方舟 | `scripts/main_arknights.py`（独立 PySide6 计算器） | `framework/adapters/arknights/` 含 layout，可用 Viewer；**桌面暂不走 calcpack 启动** |
| fps / moba / card_rpg | 无独立桌面 exe | 仅 adapter + 示例 `.calcpack`（`web/hub/samples/`） |

配置包设计器「数据录入」按适配器分轨：终末地角色/武器/装备；明日方舟干员（`tools/arknights_scout/output/parsed/operators.json`）。
