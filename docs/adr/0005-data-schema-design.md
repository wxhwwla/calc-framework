# ADR-0005：标准数据录入规范 — 四层数据契约

**状态**：已批准  
**日期**：2026-05-28  
**决策者**：维护者（Grill 设计会话）  
**影响范围**：`tools/data_pipeline/`、框架 `DataContext`、未来适配器开发

---

## 1. 概述

本文档定义从原始数据（CSV / 旧 JSON）转换为标准 JSON 的**四层数据契约**，以及对应的 ETL 工具链设计。它回答：「新游戏接入框架时，数据应该长什么样？」和「终末地旧数据怎么迁移到统一格式？」

设计目标：
- **方便录入**：尽可能复用终末地已有结构，每条决策都有 Grill 验证
- **框架友好**：输出可直接喂给 `DataContextLoader`，打通 DAG 引擎
- **游戏通用**：不绑定终末地特有字段名，开发者自由定义筛选层

---

## 2. 四层架构（核心决策）

### L1 — 实体层（Entity Layer）

| 决策 | 结论 |
|------|------|
| 实体独立性 | 角色、武器、装备、坐骑为**独立平级实体**，各有独立 JSON 或 JSON 分节 |
| 唯一标识 | 同游戏内用 `名称` 做标识；跨游戏隔离由适配器保证，不引入额外 ID |
| 实体类型标记 | 可选字段 `_entity_type`：`"character"` / `"weapon"` / `"equipment"` / `"mount"` |

### L2 — 属性筛选层（Filter Layer）

| 决策 | 结论 |
|------|------|
| 字段来源 | **不由框架规定**，开发者自由定义。框架只提示"此处放筛选条件" |
| 常见示例 | `星级`、`类型`（近卫/术师）、`属性`（灼热/物理）、`武器`（单手剑/手铳） |
| 存储位置 | 平铺在 `EntitySchema` 顶层，与 L1 同级 |

### L3 — 技能层（Skill Layer）

| 决策 | 结论 |
|------|------|
| 统一结构 | 角色主动技能（战技/连携技）和武器被动加成共用 `技能[]` 数组 |
| 主动 vs 被动 | 用 `标签` 区分：`"主动"`（倍率类） vs `"被动"`（加成型） |
| 技能名即筛选 key | `"战技"`、`"战技:1"`、`"主能力值+"` 既是展示名也是选择器 |
| 伤害类型默认链 | 适配器级默认 → 技能级 `技能类型` → 段级 `伤害类型`（逐级覆盖，空则继承上层）|

### L4 — 数值层（Segment Layer）

| 决策 | 结论 |
|------|------|
| 倍率存储格式 | **整数**存储（如 `169` 代表 169%），通过 `百分比: true/false` 标记是否 ÷100 |
| 倍率索引语义 | **框架不规定**索引方式，适配器自解释（按技能等级 / 按角色等级） |
| 段级扩展 | 核心字段 `倍率` + `伤害类型`；额外字段自由扩展（如 `叠加上限`） |

---

## 3. 数据结构（Schema）

详见 [`tools/data_pipeline/schema.py`](../../tools/data_pipeline/schema.py)。

```python
class EntitySchema(TypedDict, total=False):
    名称: str
    技能: List[SkillSchema]
    _entity_type: str            # 可选
    # L2 任意筛选字段自由平铺

class SkillSchema(TypedDict, total=False):
    名称: str                    # 技能名 / 筛选 key
    标签: str                    # "主动" / "被动"
    百分比: bool                 # 倍率是否 ÷100
    技能类型: str                # 可选，段级默认值
    段: List[SegmentSchema]

class SegmentSchema(TypedDict, total=False):
    倍率: List[int]              # 各等级值，索引语义由适配器决定
    伤害类型: str                # 可选，覆盖技能级类型
```

### 示例：角色（L1+L2 → 终末地陈千语）

```json
{
  "名称": "陈千语",
  "星级": 5,
  "类型": "近卫",
  "武器": "单手剑",
  "主能力": "敏捷",
  "副能力": "力量",
  "_entity_type": "character",
  "技能": [
    {"名称": "战技", "标签": "主动", "百分比": true, "段": [
      {"倍率": [169, 186, 203, 219, 236, 253, 270, 287, 304, 325, 350, 380], "伤害类型": "物理"}
    ]},
    {"名称": "连携技", "标签": "主动", "百分比": true, "段": [
      {"倍率": [120, 132, 144, 156, 168, 180, 192, 204, 216, 231, 249, 270], "伤害类型": "灼热"}
    ]},
    {"名称": "终结技", "标签": "主动", "百分比": true, "段": [
      {"倍率": [36, 40, 43, 47, 50, 54, 58, 61, 65, 69, 75, 81], "伤害类型": "灼热"},
      {"倍率": [455, 500, 545, 591, 636, 682, 727, 773, 818, 875, 943, 1023], "伤害类型": "灼热"}
    ]}
  ]
}
```

### 示例：武器（被动加成共用技能结构）

```json
{
  "名称": "吉米尼12",
  "星级": 3,
  "类型": "施术单元",
  "_entity_type": "weapon",
  "技能": [
    {"名称": "主能力值+", "标签": "被动", "百分比": false, "段": [
      {"倍率": [10, 18, 26, 34, 42, 51, 59, 67, 79]}
    ]},
    {"名称": "附加攻击力+", "标签": "被动", "百分比": false, "段": [
      {"倍率": [12, 14, 17, 19, 22, 24, 26, 29, 34]}
    ]}
  ]
}
```

---

## 4. ETL 工具链

### 4.1 目录结构

```
tools/data_pipeline/
├── __init__.py
├── schema.py                   # 四层数据契约 TypedDict
├── cli.py                      # CLI 入口（python -m tools.data_pipeline.cli）
├── readers/
│   ├── __init__.py
│   ├── csv_reader.py           # CSV → RawRecord
│   └── json_reader.py          # JSON → RawRecord
├── transformers/
│   ├── __init__.py
│   ├── to_standard.py          # RawRecord → 标准 EntitySchema
│   └── from_legacy_endfield.py # 终末地旧 JSON 迁移器
└── validators/
    ├── __init__.py
    └── schema_check.py         # 结构校验
```

### 4.2 CLI 用法

```bash
# 终末地旧格式迁移
python -m tools.data_pipeline.cli characters.json --migrate-characters -o output.json
python -m tools.data_pipeline.cli weapons.json --migrate-weapons -o output.json

# CSV → 标准 JSON（新游戏录入）
python -m tools.data_pipeline.cli data.csv -o output.json

# 校验标准 JSON
python -m tools.data_pipeline.cli data.json --validate

# 查看 schema 帮助
python -m tools.data_pipeline.cli --schema-help
```

### 4.3 数据流向

```
CSV / 旧 JSON
    → readers/*.py  (读入 → RawRecord)
    → transformers/*.py  (转换 → EntitySchema)
    → validators/schema_check.py  (校验)
    → 标准 JSON 输出
        → EndfieldContextLoader  (适配器构建 DataContext)
            → DAG engine (evaluate_graph)
```

### 4.4 新游戏适配步骤

1. 用 CSV 按标准 schema 录入数据（或直接用 JSON 写）
2. `python -m tools.data_pipeline.cli data.csv --validate -o standard.json`
3. 实现 `DataContextLoader` 子类，将 `standard.json` → `make_context()`
4. 编写 `DAGGraph` 公式图（或复用子图）
5. 注册 `AdapterPackage`

---

## 5. 迁移规则（终末地旧格式）

### 角色（characters.json）

| 旧字段 | 目标 | 说明 |
|--------|------|------|
| `战技倍率[N]` | `技能[].段[].倍率` | 嵌套列表 → 逐段映射；小数 ×100 归整 |
| `*段伤害类型` | `段[].伤害类型` | cross-reference 映射 |
| `名称`/`星级`/`类型`/`武器` | 透传 L1+L2 | |
| `力量`/`敏捷`/`智识`/`意志`/`基础攻击力` | 透传 | 供现有引擎继续使用 |

### 武器（weapons.json）

| 旧字段 | 目标 | 说明 |
|--------|------|------|
| `normal_skills[*].effect` | `技能[].名称` | effect 名映射为技能名 |
| `normal_skills[*].curve` | `技能[].段[0].倍率` | 曲线值按 `百分比` 标记转换 |
| `名称`/`类型`/`星级`/`基础攻击力` | 透传 | |

---

## 6. 未决定事项

| 事项 | 说明 |
|------|------|
| 坐骑实体 schema | 待第一个含坐骑游戏接入时定义 |
| 装备实体 schema | 终末地装备词条复杂（三件套效果、属性词条列表），需单独设计 |
| 武器特殊技能（`special_skills`） | 暂不迁移，直接透传。待框架支持条件触发属性时再规范化 |
