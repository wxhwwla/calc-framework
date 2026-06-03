# AI 计算器生成指南

> **面向对象**：AI Agent（Trae Agent、Cursor、ChatGPT、Claude 等）
> **目的**：让 AI 能从用户描述出发，自动生成完整可用的游戏计算器适配包
> **关联文档**：[框架适配新游戏指南](./框架适配新游戏指南.md)（面向人类开发者的完整参考）

---

## 一、框架架构速览（AI 上下文）

### 1.1 仓库布局

```
endfield_damage_calculator/
├── framework/                    # 计算框架核心
│   ├── src/calc_framework/       #   DAG 引擎、UI 框架、编辑器、搜索、逆推
│   ├── adapters/                 #   所有游戏适配器（自动发现）
│   │   ├── _template/            #   → 模板基底（从这里复制）
│   │   ├── fps/                  #   FPS 品类模板
│   │   ├── moba/                 #   MOBA 品类模板
│   │   ├── card_rpg/             #   卡牌 RPG 品类模板
│   │   ├── endfield/             #   终末地（多乘区 RPG 参考）
│   │   └── arknights/            #   明日方舟（持续技能 RPG 参考）
│   └── tests/                    # 框架测试
├── games/                        # 游戏包（桌面 GUI + 数据加载）
│   ├── endfield/                 #   终末地桌面计算器
│   └── arknights/                #   明日方舟桌面计算器
├── web/                          # Web 前后端
│   ├── frontend/                 #   React + MUI 前端
│   └── backend/                  #   FastAPI 后端
├── scripts/                      # 入口脚本
└── tools/                        # 开发工具
```

### 1.2 适配器 = 核心产出

**一个适配器 = 一个目录 `framework/adapters/{game}/`**，包含：

| 文件 | 必填 | 作用 | 谁来填 |
|------|------|------|--------|
| `meta.json` | ✅ | 元数据（名称、版本、函数注册） | AI |
| `{game}.dag.json` | ✅ | DAG 计算图（公式逻辑） | **AI**（最核心） |
| `attr_schema.json` | ✅ | 变量属性定义 | AI |
| `functions.py` | ❌ | DAG 中调用的纯函数 | AI（有自定义公式时） |
| `ui/layout.json` | ✅ | UI 布局（输入面板 + 输出面板） | AI |
| `loader.py` | ❌ | 数据上下文加载器 | 简化场景可不写 |
| `data/*.json` | ❌ | 游戏数据（角色、武器数值表） | 用户 / 爬虫 |

### 1.3 DAG 引擎核心概念

DAG = **有向无环图**，由节点（nodes）和变量（variables）组成。

**variables** — 输入数据的声明（来源可以是 character / weapon / enemy / user_input）：
```json
"character.ATK": {
  "type": "float",
  "source": "character",
  "default": 100,
  "description": "角色攻击力"
}
```

**nodes** — 计算步骤，节点类型有：

| 类型 | 作用 | 示例 |
|------|------|------|
| `const` | 常量值 | `{ "type": "const", "value": 1.5 }` |
| `var` | 读取变量 | `{ "type": "var", "path": "character.ATK" }` |
| `binary` | 二元运算 | `{ "type": "binary", "op": "+", "lhs": "a", "rhs": "b" }` |
| `unary` | 一元运算 | `{ "type": "unary", "op": "negate", "input": "a" }` |
| `condition` | 条件分支 | `{ "type": "condition", "cond": "is_crit", "true_val": "x", "false_val": "y" }` |
| `expr` | 调用函数 | `{ "type": "expr", "expr": "clamp(x, 0, 999)", "inputs": {"x": "node_id"} }` |
| `call` | 调用子图 | `{ "type": "call", "subgraph": "sub_id", "inputs": {...} }` |
| `output` | 声明输出 | 也可以用顶层 `outputs` 字段 |

**outputs** — 计算结果输出声明：
```json
"outputs": {
  "最终伤害": { "node": "final_node_id", "label": "最终伤害", "format": "", "is_primary": true }
}
```

---

## 二、模板选择决策树

AI 收到用户的需求后，先判断用户想要的计算器属于哪类游戏，选对应模板：

```
用户描述游戏类型
│
├─ 射击类（CS、COD、Valorant、吃鸡）
│   └─ 选 FPS 模板
│       ├─ 特点：距离衰减、部位倍率、穿透、弹匣/DPS
│       └─ 参考：framework/adapters/fps/
│
├─ MOBA/ARTS（LOL、Dota2、风暴英雄）
│   └─ 选 MOBA 模板
│       ├─ 特点：技能加成(AD/AP)、双抗减伤、穿甲、CDR
│       └─ 参考：framework/adapters/moba/
│
├─ 卡牌RPG / 回合制（原神、星穹铁道、传统JRPG）
│   └─ 选 card_rpg 模板
│       ├─ 特点：ATK×倍率 - DEF、暴击分支、元素反应（可选）
│       └─ 参考：framework/adapters/card_rpg/
│
├─ 多乘区 RPG（终末地、明日方舟、多数国产手游）
│   └─ 选 multi-zone 模板（待创建）
│       ├─ 特点：攻击力→多个独立乘区叠乘→最终伤害
│       └─ 参考：framework/adapters/endfield/
│
└─ 其他/不确定
    └─ 用 _template 基底模板
        ├─ 最简单的单公式：乘法/减法
        └─ 参考：framework/adapters/_template/
```

---

## 三、分步生成流程

### Step 1: 创建适配器目录

从 `_template` 复制：`framework/adapters/{game}/`，将 `{game}` 替换为游戏的英文 ID（小写+下划线）。

如果用户说的游戏已有品类模板，直接从品类模板复制更省力。

### Step 2: 编写 `meta.json`

```json
{
  "name": "用户游戏的中文名",
  "game": "用户游戏的显示名",
  "description": "简短描述（1-2句）",
  "version": "0.1.0",
  "schema_version": "dag-v1",
  "entry_dag": "{game}.dag.json",
  "ui_layout": "ui/layout.json",
  "attr_schema": "attr_schema.json",
  "functions": {
    "clamp": "functions.py",
    "lerp": "functions.py"
    // 用户有自定义公式时在这里注册更多函数
  }
}
```

注意：
- `entry_dag` 的文件名必须和 `meta.json` 所在目录名一致（除了适配器目录名是 `{game}`，DAG 文件名是 `{game}.dag.json`）
- 不要求 `ui_layout` 字段（部分适配器没有），但推荐加上

### Step 3: 编写 `attr_schema.json`

定义所有输入变量的属性信息。AI 应根据用户描述的属性来生成：

```json
{
  "attributes": [
    { "name": "ATK", "type": "float", "source": "character", "default": 100, "description": "攻击力" },
    { "name": "DEF", "type": "float", "source": "character", "default": 50, "description": "防御力" },
    { "name": "crit_rate", "type": "percent", "source": "character", "default": 0.05, "description": "暴击率" },
    { "name": "skill_mult", "type": "float", "source": "user_input", "default": 1.0, "description": "技能倍率" }
  ]
}
```

**source 字段含义**：
- `character` — 角色属性（随角色变化）
- `weapon` — 武器属性（随武器变化）
- `enemy` — 敌方属性（用户手动输入）
- `user_input` — 用户手动输入的参数（如技能倍率、是否暴击）

**type 字段**：`float`、`int`、`bool`、`percent`（percent 也是 float，但 UI 以百分比显示）、`string`

**不要包含计算中间变量** — attr_schema 只声明外部输入，不声明计算过程中产生的值。

### Step 4: 编写 `functions.py`（如有自定义公式）

如果用户的公式可以用 DAG 内置节点类型（binary/condition）实现，就不需要 `functions.py`。
需要自定义公式的情况：

- 特殊数学运算（钳制 clamp、插值 lerp）
- 复杂的条件逻辑
- 查表、取整等

```python
# SPDX-License-Identifier: AGPL-3.0
"""{game} 适配器 — DAG 自定义函数。"""


def clamp(value: float, min_val: float, max_val: float) -> float:
    """将 value 约束在 [min_val, max_val] 区间内。"""
    return max(min_val, min(max_val, value))
```

**规则**：
- 每个函数必须是纯函数（无副作用，同样的输入→同样的输出）
- 函数名就是注册名，在 DAG 的 `expr` 节点中通过函数名调用
- 参数类型建议加注解（但不强制）
- 不要使用 `calc_framework` 内部的导入

### Step 5: 编写 DAG（最核心）

DAG 是计算器的灵魂。AI 根据用户描述的游戏公式，一步步构建计算图。

**决策流程**：

```
用户描述公式
→ AI 列出所有输入变量（从 attr_schema）
→ AI 列出所有中间计算步骤
→ AI 列出所有输出结果
→ AI 组装 DAG 节点
```

**5.1 纯乘法/除法模式**（最简单）：
```json
"nodes": {
  "atk":        { "type": "var", "path": "character.ATK" },
  "mult":       { "type": "var", "path": "user_input.skill_mult" },
  "damage":     { "type": "binary", "op": "*", "lhs": "atk", "rhs": "mult" }
}
```

**5.2 减法防御模式**（ATK×倍率 - DEF×系数）：
参考 card_rpg 的经典减法公式。

**5.3 暴击分支模式**：
```json
"is_crit":    { "type": "var", "path": "user_input.is_crit" },
"crit_mult":  { "type": "condition", "cond": "is_crit", "true_val": "crit_base", "false_val": "const_1" }
```

**5.4 多乘区叠乘模式**（终末地方案）：
每个乘区是一个独立的计算链，最终伤害 = 基础值 × 乘区1 × 乘区2 × ... × 乘区N

**5.5 距离衰减模式**（FPS）：
使用条件节点 + 线性插值：
```
distance → 判断落在哪个区间 → lerp(近距离伤害, 远距离伤害, t)
```

**DAG 编写规范**：
1. 节点 ID 使用有意义的英文名（`total_atk`、`base_damage`、`crit_mult`）
2. `label` 字段写中文标签（`"总攻击力"`、`"基础伤害"`、`"暴击倍率"`）
3. 节点的引用顺序不重要（引擎自动拓扑排序），但要确保没有循环引用
4. 所有用到的变量必须先在 `variables` 中声明
5. outputs 的 key（中文）必须与 ui/layout.json 中的 outputs 名称一致

### Step 6: 编写 `ui/layout.json`

```json
{
  "schema_version": "ui-v1",
  "name": "{游戏名}计算表",
  "sections": [
    {
      "id": "inputs",
      "type": "inputs",
      "title": "输入参数",
      "variables": ["user_input.skill_mult", "user_input.is_crit"]
    },
    {
      "id": "result",
      "type": "outputs",
      "title": "计算结果",
      "outputs": ["总攻击力", "基础伤害", "最终伤害"]
    }
  ]
}
```

**规则**：
- `inputs` 类型的 section：variables 数组引用 DAG 中 source=user_input 的变量名
- `outputs` 类型的 section：outputs 数组引用 DAG 中 outputs 的 key
- 可以有多个 inputs 和 outputs section（分类展示）
- section id 唯一

### Step 7: 验证

生成完所有文件后，做以下检查：

- [ ] **meta.json**：`entry_dag` 路径正确，`functions` 注册了所有使用的函数
- [ ] **DAG 合法性**：所有 node 引用的其他 node ID 存在，variables 都有声明
- [ ] **attr_schema**：`attributes` 数组格式正确（不是旧版 `fields` 格式）
- [ ] **layout.json**：`variables` 引用 DAG 中存在的 `user_input.*` 变量，`outputs` 引用 DAG 中存在的 output key
- [ ] **函数注册**：`expr` 节点调用的函数名在 `functions.py` 中定义且在 `meta.json` 中注册
- [ ] **JSON 语法**：所有 JSON 文件都是合法的 JSON（无 trailing comma、无注释）

---

## 四、品类模板速查

### 4.1 FPS 模板

**典型公式结构**：
```
基础伤害 → 距离衰减(分段线性) → 部位倍率(头部/躯干/四肢) → 护甲减伤 → 实际伤害
                             ↘ 穿透衰减 → 实际伤害（穿墙）

DPS 计算链：
单发伤害 × 射速 = 原始 DPS
原始 DPS × (弹匣容量 / (弹匣容量 + 换弹时间×射速)) = 持续 DPS
```

**自定义函数**：`clamp`（钳制）、`lerp`（线性插值）、`le`/`ge`（条件比较）

**DAG 关键模式**：condition 节点实现部位判断，多个 expr 节点实现 lerp

### 4.2 MOBA 模板

**典型公式结构**：
```
技能伤害 = 技能基础 + AD加成×额外AD + AP加成×AP

物理减伤 = 护甲 / (护甲 + 100 + 穿甲)
魔法减伤 = 魔抗 / (魔抗 + 100 + 法穿)

最终伤害 = 技能伤害 × (1 - 物理/魔法减伤)

普攻 DPS = AD × 攻速 × (1 + 暴击率 × 暴击伤害)
```

**自定义函数**：`percent_of`（百分比计算）、`armor_mult`（护甲乘数）

**DAG 关键模式**：多输入加法（binary 链式相加）、除法实现减伤

### 4.3 卡牌 RPG 模板

**典型公式结构**：
```
总攻击力 = 角色ATK + 武器ATK
基础伤害 = max(总攻击力 × 技能倍率 - 敌方DEF × 系数, 0)
暴击倍率 = (是否暴击 ? 暴击伤害 : 1.0)
最终伤害 = 基础伤害 × 暴击倍率
```

参考 `card_rpg/` 的完整实现。

### 4.4 多乘区 RPG 模板（终末地方案）

**典型公式结构**：
```
攻击力链：基础攻击力 × (1 + 攻击力%加成) + 附加攻击力
         → 中间攻击力 × (1 + 能力值加成) → 最终攻击力

乘区链：最终攻击力 × 技能倍率 × 增伤区 × 易伤区 × 防御区
        × 抗性区 × 减伤区 × 脆弱区 × 失衡区 × 庇护区 ...

每个乘区独立计算，最终全部叠乘。
```

**关键思路**：每个乘区是一个子图（subgraph），可以被 `call` 节点调用。

---

## 五、AI 与用户对话策略

### 5.1 优先问什么

当用户说"我想做一个 X 游戏的计算器"时，AI 应主动问：

1. **伤害公式是什么？** — "最终伤害怎么算的？有没有公开的公式？"
2. **有哪些角色/武器/装备？** — "有 Wiki 链接吗？或者能提供数据表格吗？"
3. **有哪些属性？** — "角色有哪些属性（攻击、防御、暴击...）？"
4. **UI 偏好？** — "需要展示哪些中间结果？"

用户不回答时，AI 应基于同类游戏做合理假设，在注释中标注"待确认"。

### 5.2 当用户提供 Wiki 链接

1. 建议用户先使用 `tools/wiki_scout/` 爬取数据
2. 如果用户无法使用爬虫，让用户粘贴 Wiki 页面内容
3. AI 从 Wiki 文本中提取属性、公式线索

### 5.3 公式提取策略

用户描述的公式可能有多种形式：

| 用户描述 | AI 理解 |
|----------|---------|
| "攻击力×技能倍率" | binary(*, var(ATK), var(skill_mult)) |
| "攻击力减防御力" | binary(-, var(ATK), var(DEF)) |
| "不低于0" | expr(clamp, ...) 或 condition |
| "如果暴击则×1.5" | condition(is_crit, const(1.5), const(1.0)) |
| "100/(100+护甲)" | binary(/, const(100), binary(+, const(100), var(armor))) |

---

## 六、常见错误避坑

| # | 错误 | 后果 | 正确做法 |
|---|------|------|----------|
| 1 | `attr_schema` 用 `fields` 数组 | 框架不识别，变量无法加载 | 使用 `attributes` 数组 |
| 2 | DAG 中引用未声明的变量 | 引擎报错 `variable not found` | 所有变量必须在 `variables` 中声明 |
| 3 | `expr` 节点调用了不在 `meta.json` 中注册的函数 | 引擎报错 `function not registered` | 在 `meta.json.functions` 中注册 |
| 4 | DAG 节点循环引用 | 引擎死循环 | 确保 DAG 无环 |
| 5 | `outputs` 的 key 包含特殊字符 | UI 显示异常 | 使用中文/英文短词 |
| 6 | `layout.json` 引用不存在的 output | UI 面板空白 | 确保 output 名称与 DAG 中一致 |
| 7 | 中文文件名/路径含空格 | 跨平台兼容问题 | 路径使用英文，label 用中文 |
| 8 | functions.py 使用了外部库 | 打包后找不到 | 只使用 Python 标准库 |

---

## 七、生成完整适配包 Checklist

AI 生成完所有文件后，用此清单确认完整：

```
适配包目录 framework/adapters/{game}/
├── meta.json          ✅  必填
├── {game}.dag.json   ✅  必填（文件名必须与 entry_dag 一致）
├── attr_schema.json   ✅  推荐
├── functions.py       ✅  如有自定义函数
└── ui/
    └── layout.json    ✅  推荐

JSON 文件检查：
├── meta.json          → 有效 JSON
├── {game}.dag.json   → 有效 JSON，nodes 完整，outputs 已定义
├── attr_schema.json   → 有效 JSON，attributes 数组格式
└── ui/layout.json     → 有效 JSON，sections 定义

函数检查：
├── functions.py       → Python 语法正确
├── expr 节点引用的函数 → 在 functions.py 中有定义
└── 定义了的函数       → 在 meta.json functions 中注册

DAG 正确性：
├── 所有节点无循环引用
├── 所有 node input 引用的 node ID 存在
├── 所有 var 节点引用的 variable 在 variables 中定义
└── user_input 变量有合理 default 值
```

---

## 八、完整示例对话

> **用户**：我想做《原神》的伤害计算器。
>
> **AI**：好的！原神的伤害公式大概是：
> ```
> 最终伤害 = 攻击力 × 技能倍率 × (1 + 增伤%) × (1 + 暴击伤害) × 防御区 × 抗性区
> ```
> 先用多乘区 RPG 模板。我先问你几个问题：
>
> 1. 角色的攻击力由哪几部分组成？（基础攻击力、百分比攻击力、固定攻击力？）
> 2. 增伤区包含哪些来源？（元素增伤、武器增伤、圣遗物？）
> 3. 防御区和抗性区的公式是怎样的？
>
> 用户回答后，AI 逐个生成文件...
>
> 如果用户说"我也不太清楚，你先按一般RPG做"，AI 基于同类游戏做合理假设。

---

> **用户**：我想做《CS2》的伤害计算器。
>
> **AI**：CS2 的伤害公式大概是：
> ```
> 实际伤害 = 武器基础伤害 × 距离衰减 × 部位倍率 × 护甲减伤
> ```
> 选 FPS 模板。需要你提供：
> 1. 武器的伤害数据（每把武器的基础伤害、射速、弹匣容量）
> 2. 距离衰减曲线（多少米开始衰减，每段衰减多少）
> 3. 各部位的倍率（头、胸、腹、四肢）
> 4. 护甲减伤的计算方式
>
> 有 Wiki 链接就更方便了。
