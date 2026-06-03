# ADR-0002：可视化公式计算图编辑器

**状态**：已实现（2026-05-30）  
**日期**：2026-05-29  
**决策者**：维护者

---

## 背景

现有 DAG formula 框架（`calc_framework.dag`）已支持声明式的计算图定义（常量、变量引用、一元/二元运算、条件分支等），但缺少可视化的编辑界面。用户需要手动维护 `endfield_full.dag.json` 和 `layout.json`，门槛高、不直观。

需要一套**可视化节点编辑器**，让用户通过拖拽连线的方式构建计算图，同时内嵌排版映射功能，最终导出一个文件供计算器使用。

## 决策

### 1. 整体方案

构建一个**蓝图/节点图风格**的 PySide6 GUI 编辑器，定位为 `calc_framework` 框架的一级子包：

```
framework/src/calc_framework/
  graph_editor/              ← 新增
    __init__.py
    graph_editor_widget.py   # 主画布组件
    nodes.py                 # 节点定义（UI 渲染 + 数据模型）
    ports.py                 # 输入/输出端口定义
    wire.py                  # 连线渲染与管理
    schema.py                # 导出 JSON 格式规范
    serializer.py            # 读写 graph JSON
    registry.py              # 节点类型注册表
    __main__.py              # CLI 入口
```

**入口文件**：`games/endfield/graph_editor_main.py`（与 `designer_main.py` 同级）

### 2. 导出文件格式

**单个 `.json` 文件**，同时包含计算图逻辑和显示排版信息：

```json
{
  "schema_version": "calc-graph-v1",
  "name": "公式名称",
  "description": "描述",

  "external_variables": {
    "character.基础攻击": {
      "type": "float",
      "source": "character",
      "description": "角色基础攻击力"
    }
  },

  "nodes": [
    {
      "id": "n1",
      "type": "const",
      "op": null,
      "label": "基础值",
      "config": { "value": 1000.0 },
      "position": { "x": 100, "y": 200 }
    },
    {
      "id": "n2",
      "type": "var",
      "op": null,
      "label": "攻击力",
      "config": { "path": "character.基础攻击" },
      "position": { "x": 100, "y": 350 }
    },
    {
      "id": "n3",
      "type": "binary",
      "op": "+",
      "label": "总和",
      "config": {},
      "position": { "x": 400, "y": 275 }
    }
  ],

  "edges": [
    { "from_node": "n1", "from_port": 0, "to_node": "n3", "to_port": 0 },
    { "from_node": "n2", "from_port": 0, "to_node": "n3", "to_port": 1 }
  ],

  "layout": {
    "sections": [
      {
        "id": "s1",
        "title": "攻击力链",
        "output_nodes": ["n3"],
        "columns": 2
      },
      {
        "id": "s2",
        "title": "最终结果",
        "output_nodes": ["n5"],
        "columns": 1
      }
    ]
  }
}
```

使用 `"output_nodes"` 替代旧的 `"outputs"`（字符串列表），因为现在输出是图节点而非固定路径变量。向后兼容通过 `serializer` 层处理。

### 3. 节点架构

每个节点包含：
- **标题**：用户自定义的可读名称
- **类型标识**：`const` / `var` / `unary` / `binary` / `condition` / `user_input` / `output`
- **运算子类型**：`op` 字段（如 `+`、`floor`、`sqrt`）
- **输入端口**：有序列表，每个端口有标签和类型
- **输出端口**：有序列表（通常 1 个）
- **配置参数**：类型相关的额外设置（默认值、路径、范围等）
- **画布位置**：`{x, y}` 坐标

#### 基础包节点

| 节点 | 类型标识 | 运算子类型 | 输入 | 输出 | 配置 |
|------|----------|-----------|------|------|------|
| 常量 | `const` | — | — | value | value |
| 变量引用 | `var` | — | — | value | path |
| 用户输入 | `user_input` | — | — | value | default, min, max, step |
| 加法 | `binary` | `+` | lhs, rhs | result | — |
| 减法 | `binary` | `-` | lhs, rhs | result | — |
| 乘法 | `binary` | `*` | lhs, rhs | result | — |
| 除法 | `binary` | `/` | lhs, rhs | result | — |
| 乘方 | `binary` | `^` | base, exp | result | — |
| 取模 | `binary` | `mod` | lhs, rhs | result | — |
| 最大值 | `binary` | `max` | a, b | result | — |
| 最小值 | `binary` | `min` | a, b | result | — |
| 向下取整 | `unary` | `floor` | value | result | — |
| 向上取整 | `unary` | `ceil` | value | result | — |
| 绝对值 | `unary` | `abs` | value | result | — |
| 平方根 | `unary` | `sqrt` | value | result | — |
| 取反 | `unary` | `neg` | value | result | — |
| 条件分支 | `condition` | — | cond, true_val, false_val | result | — |
| 输出标记 | `output` | — | value | — | section_id |

#### 扩展包节点（阶段 2）

| 节点 | 类型标识 | 运算子类型 |
|------|----------|-----------|
| 自然对数 | `unary` | `ln` |
| 常用对数 | `unary` | `log10` |
| 正弦 | `unary` | `sin` |
| 余弦 | `unary` | `cos` |
| 正切 | `unary` | `tan` |
| 定积分 | `call` | `integral` |
| 求和 | `call` | `sum` |
| 平均值 | `call` | `avg` |

扩展包通过 `registry.py` 中的插件机制注册，不侵入核心节点系统。

### 4. 编辑器交互设计

**主界面布局**：

```
┌─────────────────────────────────────────────────────────────┐
│ [文件] [编辑] [视图]         工具栏                           │
├──────────┬──────────────────────────────────────────────────┤
│          │                                                  │
│ 节点面板  │              节 点 画 布                          │
│ (拖拽添加) │     (拖拽节点 / 连线 / 缩放 / 平移)               │
│          │                                                  │
│ • 常量    │     [n1 常量]───→[n3 加法]───→[n5 输出]          │
│ • 变量    │         ↑           ↑                            │
│ • 加法    │     [n2 变量]───┘                                │
│ • 减法    │                                                  │
│ • ...     │                                                  │
├──────────┴──────────────────────────────────────────────────┤
│ 属性面板 (选中节点后显示配置项)                   状态栏       │
└─────────────────────────────────────────────────────────────┘
```

**交互**：
- **节点操作**：从左侧面板拖入画布、画布内拖拽移动、右键菜单删除
- **连线操作**：从输出端口拖拽到输入端口创建连线；右键删除连线
- **画布操作**：滚轮缩放、中键平移、框选多节点
- **节点配置**：点击节点 → 底部属性面板显示对应配置项
- **排版管理**：底部面板添加/编辑/删除 Section，将输出节点分配到 Section

### 5. 与计算器的集成

计算器加载 `graph.json` 的流程：

1. **加载阶段**：`GraphSerializer.load(path)` → 解析 JSON 为 `GraphDocument`
2. **编译阶段**：`GraphCompiler.compile(graph_doc)` → 生成 `DAGGraph` + `Layout`
3. **求值阶段**：使用现有 `DAGService` + `ComputeSheet` 渲染和计算

编译器的职责是把可视化编辑器的图结构转换为现有框架的 DAG 格式（拓扑排序、节点引用解析、变量声明提取）。

### 6. 实施计划

#### 阶段 1 — 框架核心（预期约 5 个 tracer bullet）

| 步骤 | 内容 | 产出 |
|------|------|------|
| 1.1 | 定义 JSON schema + 序列化层 | `schema.py` / `serializer.py` |
| 1.2 | 节点画布（pan/zoom + 节点渲染） | `graph_editor_widget.py` |
| 1.3 | 端口渲染 + 连线绘制（贝塞尔曲线） | `ports.py` / `wire.py` |
| 1.4 | 拖拽连线交互 | 连通节点 |
| 1.5 | 节点拖拽移动 + 添加/删除 | 基本编辑器可用 |

#### 阶段 2 — 节点类型

| 步骤 | 内容 | 产出 |
|------|------|------|
| 2.1 | 节点类型注册表 | `registry.py` |
| 2.2 | 左侧节点面板（拖入画布） | 添加所有基础节点 |
| 2.3 | 底部属性面板（点击节点配置） | 编辑常量值、变量路径等 |
| 2.4 | 实时预览（显示节点计算值） | 调试辅助 |

#### 阶段 3 — 排版集成

| 步骤 | 内容 | 产出 |
|------|------|------|
| 3.1 | 输出标记节点 + section 管理 | 布局面板 |
| 3.2 | 导出 `graph.json` | 完整的导出功能 |
| 3.3 | 导入已有 `graph.json` | 加载/编辑已有文件 |

#### 阶段 4 — 计算器集成

| 步骤 | 内容 | 产出 |
|------|------|------|
| 4.1 | `GraphCompiler`（图→DAG） | 编译器 |
| 4.2 | ComputeSheet 支持 graph JSON 格式 | 计算器可加载 |
| 4.3 | 用终末地实际 DAG 验证 | 完整端到端 |

#### 阶段 5 — 扩展包

| 步骤 | 内容 | 产出 |
|------|------|------|
| 5.1 | 三角函数节点注册 | sin/cos/tan/asin/acos/atan |
| 5.2 | 对数节点注册 | ln/log10 |
| 5.3 | 统计节点注册 | sum/avg/count |
| 5.4 | 定积分节点 | 数值积分 |

## 后果

### 正面
- 可视化编辑大大降低公式维护门槛
- 单个文件同时包含逻辑和排版，简化分发
- 完整利用已有的 DAG 求值引擎
- 可扩展的节点体系支持多种游戏

### 负面
- 蓝图编辑器开发工作量大（canvas 绘制、连线交互、undo/redo）
- 需要维护 `GraphCompiler` 到现有 DAG 格式的转换
- 画布交互可能受 PySide6 原生控件性能限制（大规模图）

### 兼容性
- 旧的 `endfield_full.dag.json` + `layout.json` 继续受支持
- graph.json 通过编译器转换为现有格式，不破坏现有系统

## 相关文档
- [ADR-0001：代码目录与文件规模约束](0001-code-layout-constraints.md)
- [CONTEXT.md](../../CONTEXT.md) — 术语表
- [代码结构规范](../代码结构规范.md)
- 现有 DAG schema：`framework/src/calc_framework/dag/schema.py`
- 现有 DAG 引擎：`framework/src/calc_framework/dag/engine.py`
- 现有布局系统：`framework/src/calc_framework/ui/layout.py`
