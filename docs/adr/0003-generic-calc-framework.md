# ADR-0003：通用计算框架 — DAG 公式引擎与 AST 沙箱

**状态**：已批准  
**日期**：2026-05-27  
**决策者**：维护者（Grill 会话）  
**影响范围**：新建 `framework/` 独立包；后续逐步迁移 `endfield_damage_calculator/calculation/` 到 DAG 配置

---

## 1. 背景

当前项目是《终末地》专用伤害计算器，所有乘区逻辑、数据 Schema、GUI 布局均为硬编码。用户期望将项目演进为**可支持任意抽卡 RPG 的通用计算框架**，让用户可以通过配置文件定义公式、数据结构、UI 布局，并导出/分享。

经过多轮 Grill 设计讨论，确定了框架的顶层架构决策，本文档记录所有决策的详细方案。

---

## 2. 顶层架构决策汇总

| # | 决策 | 选择 | 说明 |
|---|------|------|------|
| 1 | 框架抽象层级 | C — 任意抽卡 RPG | 不局限于终末地或 Arknights 系列 |
| 2 | 公式结构模型 | B — DAG（未来 C 图灵完备） | 有向无环图，节点间有依赖边 |
| 3 | 配置打包方式 | B — 公式/Schema/UI 与数据分离，可选打包 | 公式核心不变时数据独立更新 |
| 4 | DAG 节点类型 | 条件进 DAG，列表聚合放搜索层 | `condition` 节点；`sum()` 归上层 |
| 5 | 公式执行引擎 | C — Python `ast` 沙箱 | 白名单节点放行，未来可扩展为图灵完备 |
| 6 | 配置文件格式 | JSON 运行时 + Python 脚本生成 | 保持现有 BWIKI 工具链兼容 |
| 7 | 数据 Schema | C — 完全自由变量绑定 | 按路径取 `角色.力量`，不预设数据结构 |
| 8 | UI 适配 | A — 声明式布局文件 + 可视化编辑器 | 编辑器与框架同期交付 |
| 9 | 编辑器交付时机 | MVP 必须同期交付 | 无编辑器用户无法手写 JSON 布局 |
| 10 | 模块架构路径 | 渐进式 C→B | 先 `framework/` 子目录，最终独立 pip 包 |
| 11 | 开发切入点 | A — DAG 公式引擎 + AST 沙箱 | 最底层核心，独立性强，可纯单元测试验证 |
| 12 | DAG 表达粒度 | 算子细粒度 + `expr` 语法糖 | 原子节点便于调试与展示；`expr` 装简单公式 |
| 13 | 节点类型清单 | `const`/`var`/`unary`/`binary`/`condition`/`expr`/`user_input`/`call`/`output` | 见 §3 详细定义 |
| 14 | 变量声明 | 独立 `variables` 区 | GUI 编辑器数据源 + 精确错误信息 |
| 15 | 输出定义 | 引用风格指向普通节点 | 一个节点可被多个输出复用 |
| 16 | 子图支持 | 第一版就做 | `call` 节点 + `subgraphs` 配置区 |
| 17 | AST 白名单 | `+ - * /`、`floor/ceil/abs/sqrt/min/max` | 拒绝比较/三目/`**`/函数调用/属性访问 |

---

## 3. DAG 公式图 JSON Schema

### 3.1 顶层结构

```json
{
  "schema_version": "dag-v1",
  "name": "终末地伤害公式",
  "description": "终末地 15 乘区链 DAG 表达",
  "variables": { ... },
  "subgraphs": { ... },
  "nodes": { ... },
  "outputs": { ... }
}
```

| 字段 | 必需 | 说明 |
|------|------|------|
| `schema_version` | 是 | 固定 `"dag-v1"`，用于未来版本兼容 |
| `name` | 是 | 公式图名称 |
| `description` | 否 | 描述文字 |
| `variables` | 是 | 所有外部变量声明（见 §3.2） |
| `subgraphs` | 否 | 子图定义（见 §3.7） |
| `nodes` | 是 | 所有节点的定义（见 §3.3–§3.6） |
| `outputs` | 是 | 输出节点的引用映射（见 §3.8） |

### 3.2 变量声明 `variables`

变量声明描述了 DAG 需要哪些外部数据输入。每个变量的 key 即为数据路径（如 `角色.基础攻击`），值包含类型、来源、描述和默认值：

```json
{
  "variables": {
    "角色.基础攻击": {
      "type": "float",
      "source": "character",
      "description": "角色基础攻击力（来自等级曲线）",
      "default": 0
    },
    "角色.力量": {
      "type": "float",
      "source": "character",
      "description": "角色力量属性（来自等级曲线）"
    },
    "武器.基础攻击": {
      "type": "float",
      "source": "weapon",
      "description": "武器基础攻击力"
    },
    "enemy.防御": {
      "type": "float",
      "source": "enemy",
      "description": "敌方防御力",
      "default": 100
    },
    "user.暴击率": {
      "type": "float",
      "source": "user_input",
      "description": "用户配置的暴击率加成",
      "default": 0,
      "min": 0,
      "max": 100
    }
  }
}
```

| 变量字段 | 必需 | 说明 |
|----------|------|------|
| `type` | 是 | `"float"` / `"int"` / `"bool"` / `"str"` |
| `source` | 是 | `"character"` / `"weapon"` / `"equipment"` / `"enemy"` / `"user_input"` / `"computed"` |
| `description` | 否 | 供 GUI 工具提示 |
| `default` | 否 | 数据缺失时的回退值 |
| `min` / `max` | 否 | 仅 `user_input` 类变量的值域约束 |

`source` 语义：
- `character` / `weapon` / `equipment` / `enemy`：从对应数据 JSON 中按路径取值
- `user_input`：由用户通过 GUI 滑块/开关设置
- `computed`：由框架内部计算注入（不来自外部数据）

### 3.3 节点通用字段

所有节点共享以下字段：

| 字段 | 必需 | 说明 |
|------|------|------|
| `type` | 是 | 节点类型标识 |
| `label` | 否 | 供 GUI 乘区展示的可读名称 |
| `description` | 否 | 节点用途说明 |

### 3.4 `const` — 常量节点

```json
{
  "const_100": {
    "type": "const",
    "label": "常数 100",
    "value": 100
  }
}
```

| 字段 | 必需 | 类型 | 说明 |
|------|------|------|------|
| `value` | 是 | `number` | 常数值 |

### 3.5 `var` — 变量引用节点

```json
{
  "base_atk_node": {
    "type": "var",
    "label": "基础攻击力",
    "path": "角色.基础攻击"
  }
}
```

| 字段 | 必需 | 类型 | 说明 |
|------|------|------|------|
| `path` | 是 | `string` | 变量路径，必须在 `variables` 中声明 |

### 3.6 `unary` — 一元运算节点

```json
{
  "floor_atk": {
    "type": "unary",
    "label": "floor(攻击力)",
    "op": "floor",
    "input": "raw_atk"
  }
}
```

| 字段 | 必需 | 类型 | 说明 |
|------|------|------|------|
| `op` | 是 | `string` | `"neg"` / `"floor"` / `"ceil"` / `"abs"` / `"sqrt"` |
| `input` | 是 | `string` | 输入节点 ID |

### 3.7 `binary` — 二元运算节点

```json
{
  "atk_sum": {
    "type": "binary",
    "label": "总基础攻击",
    "op": "+",
    "lhs": "base_atk_node",
    "rhs": "weapon_atk_node"
  },
  "atk_cap": {
    "type": "binary",
    "label": "攻击力上限",
    "op": "min",
    "lhs": "atk_sum",
    "rhs": "atk_cap_value"
  },
  "pow_result": {
    "type": "binary",
    "label": "指数衰减",
    "op": "^",
    "lhs": "base_value",
    "rhs": "exponent"
  }
}
```

| 字段 | 必需 | 类型 | 说明 |
|------|------|------|------|
| `op` | 是 | `string` | `"+"` / `"-"` / `"*"` / `"/"` / `"^"` / `"min"` / `"max"` |
| `lhs` | 是 | `string` | 左操作数节点 ID |
| `rhs` | 是 | `string` | 右操作数节点 ID |

### 3.8 `condition` — 条件分支节点

```json
{
  "crit_damage": {
    "type": "condition",
    "label": "暴击时最终伤害",
    "cond": "is_crit_node",
    "true_val": "crit_damage_node",
    "false_val": "normal_damage_node"
  }
}
```

| 字段 | 必需 | 类型 | 说明 |
|------|------|------|------|
| `cond` | 是 | `string` | 条件节点 ID（期望为 0=False, ≠0=True） |
| `true_val` | 是 | `string` | 条件为真时的输出节点 ID |
| `false_val` | 是 | `string` | 条件为假时的输出节点 ID |

### 3.9 `expr` — 内联表达式节点

```json
{
  "atk_zone": {
    "type": "expr",
    "label": "攻击力加成乘区",
    "expr": "1 + bonus / 100",
    "inputs": {
      "bonus": "atk_bonus_node"
    }
  }
}
```

| 字段 | 必需 | 类型 | 说明 |
|------|------|------|------|
| `expr` | 是 | `string` | Python 数学表达式，经 AST 沙箱求值 |
| `inputs` | 是 | `object` | 表达式中的变量名 → 节点 ID 映射 |

表达式中的变量名通过 `inputs` 映射到其他节点。求值时，沙箱的作用域只包含 `inputs` 中声明的变量和 §6 中定义的白名单函数，不暴露任何 Python 内置或全局对象。

### 3.10 `user_input` — GUI 输入节点

```json
{
  "crit_rate_user": {
    "type": "user_input",
    "label": "额外暴击率",
    "default": 0,
    "min": 0,
    "max": 100,
    "step": 1
  }
}
```

| 字段 | 必需 | 类型 | 说明 |
|------|------|------|------|
| `default` | 是 | `number` | 默认值 |
| `min` | 否 | `number` | 最小值（默认 0） |
| `max` | 否 | `number` | 最大值（默认 100） |
| `step` | 否 | `number` | 步长（默认 1） |

这类节点在 GUI 中渲染为滑块或数字输入框，用户在布局编辑器中可选择控件样式（滑块/下拉框/开关）。

### 3.11 `call` — 子图调用节点

```json
{
  "calc_ability": {
    "type": "call",
    "label": "能力值加成计算",
    "subgraph": "ability_bonus",
    "bindings": {
      "character_data": "char_data_node",
      "level": "char_level_node",
      "trust": "trust_level_node"
    }
  }
}
```

| 字段 | 必需 | 类型 | 说明 |
|------|------|------|------|
| `subgraph` | 是 | `string` | 被调用的子图 ID（须在 `subgraphs` 中定义） |
| `bindings` | 是 | `object` | 子图形参名 → 当前图节点 ID 的绑定映射 |

`call` 节点的输出是子图**所有** `output` 节点的值，可通过 `call_node_id.output_name` 的语法引用子图中的特定输出（见 §3.12 和 §3.14）。

### 3.12 `output` — 输出标记节点

并非独立节点类型，而是对已存在节点的"命名标记"。定义在顶层 `outputs` 区：

```json
{
  "outputs": {
    "final_damage": {
      "node": "final_damage_node",
      "label": "最终伤害",
      "is_primary": true
    },
    "final_attack": {
      "node": "final_atk_node",
      "label": "最终攻击力"
    },
    "crit_damage": {
      "node": "crit_damage_node",
      "label": "暴击伤害"
    }
  }
}
```

| 字段 | 必需 | 类型 | 说明 |
|------|------|------|------|
| `node` | 是 | `string` | 被引用的节点 ID |
| `label` | 是 | `string` | 输出名称（供 GUI 表格显示） |
| `is_primary` | 否 | `bool` | 是否为核心/主输出（默认 `false`） |

输出节点引用子图内节点时的语法：

```json
{
  "sub_attack": {
    "node": "calc_ability.final_attack",
    "label": "能力值加成后的攻击力"
  }
}
```

其中 `calc_ability` 是 `call` 节点的 ID，`final_attack` 是该子图内的输出名。

### 3.13 `subgraphs` — 子图定义区

```json
{
  "subgraphs": {
    "ability_bonus": {
      "description": "计算角色的能力值加成",
      "parameters": {
        "character_data": { "type": "float" },
        "level": { "type": "int", "default": 1 },
        "trust": { "type": "int", "default": 0 }
      },
      "nodes": {
        "attr_str": { "type": "var", "path": "角色.力量" },
        "attr_agi": { "type": "var", "path": "角色.敏捷" },
        "attr_int": { "type": "var", "path": "角色.智识" },
        "attr_wil": { "type": "var", "path": "角色.意志" },
        "sum_attrs": {
          "type": "binary", "op": "+", "lhs": "attr_str", "rhs": "attr_agi"
        },
        "ability_ratio": {
          "type": "expr",
          "expr": "(total_attrs - 4 * 10) / 100 + 1",
          "inputs": { "total_attrs": "sum_attrs" }
        }
      },
      "outputs": {
        "ability_multiplier": { "node": "ability_ratio", "label": "能力乘数" }
      }
    }
  }
}
```

| 子图字段 | 必需 | 说明 |
|----------|------|------|
| `description` | 否 | 子图用途说明 |
| `parameters` | 是 | 形参声明（参数名 → 类型与默认值） |
| `nodes` | 是 | 子图内部的节点定义（语法与主图完全相同） |
| `outputs` | 是 | 子图输出引用（语法与主图相同） |

子图可以嵌套调用其他子图，但引擎会检测循环引用并拒绝加载。

### 3.14 节点 ID 命名规范

- 主图节点 ID：任意非空字符串，只能包含 `[a-zA-Z0-9_-]`
- 子图内节点 ID：同上，作用域隔离，可与其他子图同名
- 跨图引用语法：`call_node_id.output_name`（用于 `outputs` 和 `inputs` 绑定）
- 保留前缀：`$` 开头的 ID 为框架内部保留

### 3.15 DAG 完整性约束

1. **无循环依赖**：拓扑排序时必须找到合法执行顺序，否则拒绝加载
2. **所有边指向已存在节点**：引用的 `lhs`/`rhs`/`input`/`cond`/`true_val`/`false_val` 必须在 `nodes` 中定义
3. **所有变量在 `variables` 中声明**：`var` 节点的 `path` 字段必须在 `variables` 区有对应条目
4. **所有 `expr` 中的输入变量在 `inputs` 中声明**：沙箱求值时不会注入未声明的变量
5. **子图被调用前已定义**：`call` 节点的 `subgraph` 字段必须在 `subgraphs` 中有对应条目

---

## 4. AST 沙箱设计

### 4.1 安全模型

AST 沙箱使用 Python 内置的 `ast` 模块将用户提供的表达式字符串解析为抽象语法树，然后通过白名单机制遍历节点树并求值。核心安全原则：

1. **只放行白名单中的节点类型**
2. **拒绝所有 `import` / `exec` / `eval` / `getattr` 等危险操作**
3. **拒绝属性访问（`.`）、下标访问（`[]`）、函数调用（除白名单函数外）**
4. **变量作用域由调用方注入**（来自 `expr` 节点的 `inputs` 绑定），表达式不直接访问全局或闭包变量

### 4.2 白名单

| 类别 | 放行 | 拒绝 |
|------|------|------|
| 数字 | `Num` / `Constant`（整数、浮点数） | — |
| 变量 | `Name`（由 `inputs` 映射注入值） | — |
| 二元运算 | `Add` `Sub` `Mult` `Div` | `Pow`（使用 `binary` 节点的 `"^"` 代替） |
| 比较 | — | `Compare` `Eq` `NotEq` `Lt` `Gt` `LtE` `GtE` `Is` `IsNot` `In` `NotIn` |
| 布尔/条件 | — | `BoolOp` `IfExp` `And` `Or` `Not` |
| 一元运算 | `USub`（负号） | `UAdd` `Not` `Invert` |
| 内置函数调用 | `floor` `ceil` `abs` `sqrt` `min` `max` | 其他所有（含 `open` `exec` `eval` `getattr` `setattr` `__import__` `type` `isinstance` 等） |
| 属性访问 | — | `Attribute` |
| 下标/切片 | — | `Subscript` `Slice` |
| 容器 | — | `List` `Tuple` `Set` `Dict` `ListComp` `DictComp` `SetComp` `GeneratorExp` |
| 函数定义 | — | `Lambda` `FunctionDef` `AsyncFunctionDef` |
| 类定义 | — | `ClassDef` |
| 导入 | — | `Import` `ImportFrom` |
| 其他 | — | `Yield` `YieldFrom` `Await` `Starred` `NamedExpr` `FormattedValue` `JoinedStr` |

### 4.3 实现架构

```
framework/src/calc_framework/dag/sandbox.py
├── _WHITELISTED_NODE_TYPES   # 放行的 AST 节点类型集合
├── _SAFE_BUILTINS            # 放行的内置函数映射（floor→math.floor 等）
├── parse_expr(expr_str)      # 解析表达式字符串 → AST 树 + 白名单校验
├── evaluate_expr(ast_tree, scope)  # 在白名单 scope 中递归求值 AST
└── validate_expr(expr_str)   # 仅校验不执行（供编辑器即时反馈）
```

### 4.4 错误处理

- **解析错误**：表达式语法不合法 → 抛出 `DAGCompileError`，包含行号和错误的 token
- **白名单违规**：表达式使用了未放行的语法 → 抛出 `DAGSecurityError`，指明违规的节点类型
- **运行时错误**：除零、溢出等 → 抛出 `DAGRuntimeError`，包含节点 ID 和表达式

---

## 5. DAG 执行引擎

### 5.1 执行流程

```
1. 解析 JSON → DAG 对象
2. 展开所有 call 节点（内联子图）
3. 拓扑排序所有节点
4. 按拓扑序依次求值
5. 收集 output 节点的值
6. 返回 {output_name: value} 结果字典
```

### 5.2 子图展开

`call` 节点在求值前先展开——将子图的节点和边复制到当前图的命名空间下，用 `bindings` 替换形参引用：

1. 复制子图的所有节点，加前缀 `call_node_id.` 避免同名冲突
2. 将子图内 `var` 节点按 `parameters` 中的形参名替换为 `bindings` 中的实际节点引用
3. 子图的 `outputs` 中每个输出映射为 `call_node_id.output_name` 对外暴露
4. 递归展开子图内的 `call` 节点（检测并拒绝循环）

### 5.3 拓扑排序

使用 Kahn 算法（基于入度）：

```
入度 = 每个节点被其他节点引用的次数（按边计算）
初始队列 = 入度为 0 的节点（const / var / user_input / 已解析参数的 call）
依次: 出队 → 求值 → 更新下游入度 → 入度为 0 则入队
```

若存在循环依赖，算法结束时剩余入度 > 0 的节点 → 抛出 `DAGCycleError`。

### 5.4 求值调度

按节点类型分发：

| 节点类型 | 求值逻辑 |
|----------|----------|
| `const` | 直接返回 `value` |
| `var` | 从数据上下文中按 `path` 取变量值 |
| `unary` | 取 `input` 的值，应用一元运算 |
| `binary` | 取 `lhs` 和 `rhs` 的值，应用二元运算 |
| `condition` | 取 `cond` 的值（0→False, ≠0→True），返回对应分支值 |
| `expr` | 将 `inputs` 映射值注入沙箱，执行表达式 |
| `user_input` | 返回当前 GUI 绑定的值（或 `default`） |
| `call`（展开后） | 对展开后的子图执行拓扑求值，收集其 outputs |

### 5.5 数据上下文

数据上下文是一个嵌套字典，按 `source` 分类，由框架的数据引擎提供：

```python
DataContext = {
    "character": {...},   # 当前角色完整数据
    "weapon": {...},      # 当前武器完整数据
    "equipment": {...},   # 当前装备数据
    "enemy": {...},       # 敌方参数
    "computed": {...}     # 框架内部计算值（由上层注入）
}
```

`var` 节点的 `path` 格式为 `source.field.subfield`（如 `角色.基础攻击`），引擎按 `.` 分割后在 `DataContext` 中逐级索引。

### 5.6 执行结果

```python
@dataclass
class DAGResult:
    outputs: dict[str, float]                 # 所有 output 的值
    node_values: dict[str, float]             # 每个中间节点的求值结果（调试用）
    execution_order: list[str]                # 拓扑排序的节点 ID 序列
```

---

## 6. 配置文件组织

### 6.1 游戏适配包的目录结构

```yaml
adapters/
  endfield/                         # 终末地适配包
    dag/
      formula.dag.json              # 主公式 DAG 图
      ability_bonus.dag.json        # 能力值加成子图（被主图 call）
      attribute_zone.dag.json       # 属性乘区子图
      final_attack.dag.json         # 最终攻击力子图
    schema/
      data_schema.json              # 变量声明与数据源映射
    ui/
      layout.json                   # UI 布局定义（声明式）
    data/
      characters.json               # 角色数据
      weapons.json                  # 武器数据
      equipments.json               # 装备数据
      enemies.json                  # 敌方数据
    meta.json                       # 适配包元信息（名称/版本/作者）
```

### 6.2 `meta.json` — 适配包元信息

```json
{
  "name": "终末地伤害计算",
  "game": "明日方舟：终末地",
  "version": "3.0.0",
  "author": "...",
  "description": "终末地 15 乘区伤害公式",
  "schema_version": "dag-v1",
  "entry_dag": "dag/formula.dag.json",
  "data_schema": "schema/data_schema.json",
  "ui_layout": "ui/layout.json"
}
```

---

## 7. 代码结构（`framework/` 包）

### 7.1 目录布局

```
framework/
├── pyproject.toml
├── README.md
├── src/
│   └── calc_framework/
│       ├── __init__.py
│       ├── dag/
│       │   ├── __init__.py
│       │   ├── schema.py        # DAG JSON schema 定义（Pydantic/dataclass）
│       │   ├── engine.py        # 拓扑排序 + 求值引擎
│       │   ├── sandbox.py       # AST 沙箱（解析 + 白名单执行）
│       │   ├── subgraph.py      # 子图展开器
│       │   ├── serializer.py    # JSON ↔ DAG 对象互转
│       │   └── errors.py        # 自定义异常（DAGCycleError 等）
│       ├── data/
│       │   ├── __init__.py
│       │   ├── context.py       # DataContext 定义与构建
│       │   ├── loader.py        # 数据加载器接口（适配器需实现）
│       │   └── schema.py        # 变量 Schema 校验
│       └── config/
│           ├── __init__.py
│           └── adapter.py       # 适配包加载器（读 meta.json + 组装）
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── dag/
    │   ├── test_sandbox.py      # AST 沙箱单元测试
    │   ├── test_schema.py       # Schema 校验测试
    │   ├── test_engine.py       # 求值引擎测试
    │   ├── test_subgraph.py     # 子图展开测试
    │   └── test_serializer.py   # 序列化测试
    ├── data/
    │   └── test_context.py
    └── fixtures/
        ├── simple_linear.dag.json
        ├── condition_branch.dag.json
        ├── subgraph_call.dag.json
        └── endfield_15_zones.dag.json
```

### 7.2 目录与文件约束

遵循 ADR-0001：
- `framework/src/calc_framework/` 根 `__init__.py` + 三个子包 = 4 项（≤10）
- `dag/` 6 个 `.py` 文件（≤10）
- `data/` 3 个 `.py` 文件（≤10）
- `config/` 1 个 `.py` 文件（≤10）
- 每个 `.py` ≤ 400 行

### 7.3 `pyproject.toml`

```toml
[project]
name = "calc-framework"
version = "0.1.0"
description = "通用游戏数值计算框架 — DAG 公式引擎"
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = ["pytest>=8"]

[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"
```

框架本身零外部依赖（`ast`、`math`、`json` 为标准库）。`pytest` 仅开发时使用。

---

## 8. 迁移路径

### 8.1 第一阶段：DAG 引擎 + 终末地适配器（当前目标）

1. 实现 `framework/` 包的所有核心模块
2. 用 DAG 引擎重新表达终末地 15 乘区链
3. 编写对比测试：`新 DAG 引擎输出 == 现有 compute_multiplicative_zone_snapshot 输出`
4. 现有 `calculation/` 模块**不受影响**，新旧引擎并行运行

验收标准：
- `tests/fixtures/endfield_15_zones.dag.json` 能成功加载并求值
- 与现有的 `zone_snapshot.py` + `final_attack_zone.py` + `attribute_zone.py` + `ability_bonus_details.py` 计算结果**完全一致**（误差 < 1e-9）

### 8.2 第二阶段：通用数据引擎

1. 实现 `framework/src/calc_framework/data/` — DataContext、变量绑定、加载器接口
2. 终末地数据适配器实现加载器接口
3. GUI 右侧乘区展示改为使用 DAG 引擎的输出（不再调用 `zone_snapshot.py`）

### 8.3 第三阶段：声明式 UI + 布局编辑器

1. 实现 UI 渲染引擎（`framework/src/calc_framework/ui/`）
2. 实现可视化布局编辑器（`framework/src/calc_framework/editor/`）
3. 终末地 UI 布局由 JSON 描述

### 8.4 第四阶段：框架独立包 + 社区

1. `framework/` 独立 pip 包，终末地通过 `pip install` 引用
2. 社区适配器生态

---

## 9. 验收测试设计

### 9.1 单元测试覆盖

| 模块 | 测试重点 |
|------|----------|
| `sandbox.py` | 合法/非法表达式、白名单边界、错误类型 |
| `schema.py` | 合法/非法 DAG JSON、缺失字段、类型错误 |
| `engine.py` | 线性图、分支图、condition 节点、拓扑排序正确性 |
| `subgraph.py` | 子图展开、命名空间隔离、循环引用检测 |
| `serializer.py` | JSON 往返一致性 |

### 9.2 集成测试（终末地 15 乘区）

创建 `tests/fixtures/endfield_15_zones.dag.json`，用 DAG 完整表达：

1. 属性四维（力量/敏捷/智识/意志）— 来自角色等级曲线
2. 武器附加属性加成（如 `力量+`）
3. 能力值加成 — `(总属性 - 4*10)/100 + 1`
4. 最终攻击力 = `(角色基础攻击 + 武器基础攻击 + 附加攻击力+) × 能力值加成`
5. 15 乘区连乘链

===

**对比测试脚本**（伪代码）：

```python
def test_endfield_dag_equals_legacy():
    dag = load_dag("endfield_15_zones.dag.json")
    ctx = build_endfield_context(char="安洁莉娜", weapon="xxx", level=90, trust=0)
    dag_result = dag.evaluate(ctx)
    legacy_result = compute_multiplicative_zone_snapshot(selection)
    for zone_name in legacy_result.zone_values:
        assert abs(dag_result.outputs[zone_name] - legacy_result.zone_values[zone_name]) < 1e-9
```

---

## 10. 后果

### 10.1 正面

- **可扩展性**：支持新游戏只需编写一个 DAG JSON + 数据适配器，而非重写引擎
- **可分享性**：公式/布局/数据包可独立分发，社区可协作维护
- **安全性**：AST 沙箱严格白名单，用户提供的公式无法执行危险操作
- **调试性**：DAG 引擎支持逐节点求值和中间值查看（未来可做"公式可视化调试器"）
- **渐进性**：现有终末地代码不破坏，新旧引擎并行验证后逐步切换

### 10.2 负面

- **初始工作量**：DAG 引擎 + 子图 + AST 沙箱 + 终末地适配 ≈ 首版工作量较大
- **学习曲线**：用户理解 DAG 节点图 vs 直接阅读 Python 代码
- **性能开销**：DAG 引擎比手写 Python 慢（但对 GUI 计算器可忽略——单次求值远 < 1ms）
- **抽象泄露**：当公式极度非标时，DAG 节点可能不够表达（由 `expr` 节点兜底，未来升级图灵完备）

### 10.3 风险与缓解

| 风险 | 缓解 |
|------|------|
| DAG 终末地结果与旧引擎不一致 | 严格的对比测试 + TDD 流程 |
| AST 沙箱遗漏危险操作 | 白名单测试覆盖所有 Python 3.11 节点类型 |
| 子图嵌套导致性能问题 | 子图展开一次 + 缓存展开结果 |
| `framework/` 与现有代码重复 | 明确划分"框架"与"适配器"边界，框架不引用 `endfield_damage_calculator` |

---

## 11. 相关文档

- [ADR-0001：代码目录与文件规模约束](0001-code-layout-constraints.md)
- [ADR-0002：GUI 框架从 CustomTkinter 迁移到 PySide6](0002-migrate-to-pyside6.md)
- [CONTEXT.md](../../CONTEXT.md) — 领域术语表
- [docs/会话接续手册.md](../会话接续手册.md) — 项目接缝与当前进度
- [docs/代码结构规范.md](../代码结构规范.md) — 目录与文件约束
