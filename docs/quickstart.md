# quickstart — 第三方游戏接入 calc-framework

本文演示如何为一个新 RPG 游戏接入 calc-framework 框架。
使用框架的 DAG 引擎定义伤害公式、用 ComputeSheet 自动渲染 UI。

---

## 前置

```bash
pip install PySide6
```

框架位置：`framework/`，适配器位置：`framework/adapters/<game>/`。

---

## 第一步：创建适配包目录结构

```
framework/adapters/my-game/
├── meta.json
├── dag/
│   └── main.dag.json
└── ui/
    └── layout.json
```

---

## 第二步：定义 meta.json

```json
{
  "name": "我的游戏伤害计算",
  "game": "我的游戏",
  "version": "1.0.0",
  "schema_version": "dag-v1",
  "entry_dag": "dag/main.dag.json"
}
```

---

## 第三步：编写 DAG 公式

以最终攻击力 = 基础攻击力 × (1 + 攻击力%) + 固定攻击力 为例。

`dag/main.dag.json`：

```json
{
  "schema_version": "dag-v1",
  "name": "攻击力链",
  "variables": {
    "character.基础攻击力": {
      "type": "float",
      "source": "character",
      "description": "角色基础攻击力"
    },
    "computed.攻击力百分比": {
      "type": "float",
      "source": "computed",
      "description": "攻击力%加成总和",
      "default": 0.0
    },
    "computed.固定攻击力": {
      "type": "float",
      "source": "computed",
      "description": "固定攻击力加成总和",
      "default": 0.0
    }
  },
  "nodes": {
    "base": {
      "type": "var",
      "path": "character.基础攻击力"
    },
    "pct": {
      "type": "var",
      "path": "computed.攻击力百分比"
    },
    "flat": {
      "type": "var",
      "path": "computed.固定攻击力"
    },
    "pct_bonus": {
      "type": "binary",
      "op": "*",
      "lhs": "base",
      "rhs": "pct",
      "label": "百分比加成"
    },
    "total": {
      "type": "binary",
      "op": "+",
      "lhs": "base",
      "rhs": "pct_bonus",
      "label": "百分比加成后"
    },
    "final": {
      "type": "binary",
      "op": "+",
      "lhs": "total",
      "rhs": "flat",
      "label": "最终攻击力"
    }
  },
  "outputs": {
    "最终攻击力": {
      "node": "final",
      "label": "最终攻击力"
    }
  }
}
```

### 节点类型速查

| 类型 | 用途 | 关键字段 |
|------|------|---------|
| `const` | 常量 | `value` |
| `var` | 从上下文取值 | `path`（点分隔） |
| `unary` | 一元运算 | `op`（neg/floor/ceil/abs/sqrt）, `input` |
| `binary` | 二元运算 | `op`（+-*/^ min max）, `lhs`, `rhs` |
| `condition` | 条件分支 | `cond`, `true_val`, `false_val` |
| `expr` | 内联表达式 | `expr`（如 `a * (b + c)`）, `inputs` |
| `user_input` | GUI 输入控件 | `default`, `min`, `max`, `step` |
| `call` | 子图调用 | `subgraph`, `bindings` |
| `template` | 公式模板引用 | `template`, `bindings` |

### 使用公式模板

框架内置 5 个通用公式模板，可直接引用：

```json
{
  "def_reduc": {
    "template": "defense_reduction",
    "bindings": {
      "defense": "enemy_def",
      "scale": "const_0_5"
    }
  }
}
```

加载时自动展开为完整节点。内置模板：

| 模板名 | 公式 |
|--------|------|
| `defense_reduction` | `100 / (100 + defense × scale)` |
| `crit_multiplier` | `is_crit ? (1 + crit_dmg) : 1` |
| `clamp_to_range` | `clamp(value, min, max)` |
| `percent_of` | `value / total` |
| `attribute_scaling` | `base + floor((growth×(level-1) + offset) / divisor)` |

### 子图

大型公式可拆分子图，通过 `call` 节点引用：

```json
{
  "subgraphs": {
    "final_attack": {
      "nodes": { ... },
      "outputs": { "result": { "node": "final" } }
    }
  },
  "nodes": {
    "calc_atk": {
      "type": "call",
      "subgraph": "final_attack",
      "bindings": {
        "base_atk": "base",
        "atk_pct": "pct"
      }
    }
  }
}
```

---

## 第三步 B（可选）：属性声明 Schema

框架支持适配器用 `attr_schema.json` 声明自己的属性结构，由框架自动构建 DataContext 并校验数据完整性。

```json
{
  "attributes": [
    { "name": "ATK", "type": "float", "source": "character", "description": "角色攻击力" },
    { "name": "DEF", "type": "float", "source": "enemy", "default": 50, "description": "敌方防御" },
    { "name": "crit_rate", "type": "float", "source": "character", "default": 0.05 }
  ]
}
```

在 `meta.json` 中引用：

```json
{
  "name": "我的游戏",
  "entry_dag": "dag/main.dag.json",
  "attr_schema": "attr_schema.json"
}
```

然后在 Python 中使用：

```python
from calc_framework.data.attr_schema import AttributeSchema

schema = AttributeSchema.from_file("attr_schema.json")

# 自动构建 DataContext（含类型转换和默认值回退）
ctx = schema.resolve({
    "character": {"ATK": 100, "crit_rate": 0.05},
    "enemy": {"DEF": 60},
})

# 校验数据完整性
errors = schema.validate(ctx)  # 空列表 = 校验通过
```

支持的属性类型：`float`、`int`、`bool`、`str`、`percent`。

---

## 第四步：编写布局文件

`ui/layout.json` — 告诉 ComputeSheet 哪些输出要展示：

```json
{
  "schema_version": "ui-v1",
  "name": "攻击力计算表",
  "sections": [
    {
      "id": "attack",
      "type": "outputs",
      "title": "攻击力",
      "outputs": ["最终攻击力"]
    }
  ]
}
```

---

## 第五步：Python 中加载并求值

```python
from calc_framework.config.adapter import AdapterPackage
from calc_framework.data.context import make_context

pkg = AdapterPackage("framework/adapters/my-game")

context = make_context(
    character={"基础攻击力": 100},
    computed={
        "攻击力百分比": 0.5,    # 50%
        "固定攻击力": 30,
    },
)

result = pkg.dag_service.evaluate(context)
print(result.outputs)  # {"最终攻击力": 180.0}
```

---

## 第六步：用 ComputeSheet 渲染 UI

```python
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from calc_framework.config.adapter import AdapterPackage
from calc_framework.ui.compute_sheet import ComputeSheet
from calc_framework.ui.layout import load_layout_json

app = QApplication([])
win = QMainWindow()
central = QWidget()
win.setCentralWidget(central)
layout = QVBoxLayout(central)

pkg = AdapterPackage("framework/adapters/my-game")
layout_def = load_layout_json(...)  # 从文件或字符串加载

sheet = ComputeSheet(
    dag_service=pkg.dag_service,
    layout=layout_def,
    variables=pkg.dag_service.dag.variables,
    base_context=make_context(character={"基础攻击力": 100}),
)
layout.addWidget(sheet.widget)
sheet.evaluate()

win.show()
app.exec()
```

ComputeSheet 会自动：
- 为 `user_input` 类型的变量渲染滑块/输入框
- 展示 outputs 区段的计算结果
- 点击「计算」按钮刷新求值

---

## 第七步：接入日志

```python
from calc_framework.logging import setup_logging

# 在应用入口调用一次
setup_logging(level="DEBUG", log_file="my_game.log")
```

环境变量快捷方式：

```bash
set CALC_FRAMEWORK_LOG_LEVEL=INFO
set CALC_FRAMEWORK_LOG_FILE=calc.log
python main.py
```

---

## 完整接入示例

### 示例 1：终末地适配器（15 乘区）

参考 `framework/games/endfield/`：

| 文件 | 用途 |
|------|------|
| `meta.json` | 终末地适配器元信息 |
| `../../src/calc_framework/configs/endfield_full.dag.json` | 15 乘区 DAG 定义（5 子图、58 节点、18 输出） |
| `ui/layout.json` | 乘区展示排版 |
| `attr_schema.json` | 属性声明（14 个属性） |
| `games/endfield/calc/dag_adapter/loader.py` | `EndfieldContextLoader` 实现 |

```python
from games.endfield.calc.dag_adapter.loader import EndfieldContextLoader

loader = EndfieldContextLoader()
context = loader.build_context(
    character=char_dict,
    weapon=weapon_dict,
    char_level=80,
    weapon_level=80,
    trust_level=0,
)
```

### 示例 2：卡牌RPG适配器（攻击-防御公式，验证跨品类通用性）

参考 `framework/adapters/card_rpg/`：

| 文件 | 用途 |
|------|------|
| `meta.json` | 适配器元信息（含 attr_schema + functions 引用） |
| `attr_schema.json` | 属性声明（ATK/DEF/crit_rate/crit_dmg/ATK_bonus） |
| `card_rpg.dag.json` | DAG 公式（`max(ATK × skill - DEF × 0.5, 0) × crit`） |
| `loader.py` | CardRPGLoader 实现（可选——无 loader 也可直接传入 raw dict） |
| `ui/layout.json` | ComputeSheet 排版（含 inputs + outputs 双区段） |

```python
from calc_framework.config.adapter import AdapterPackage

pkg = AdapterPackage("framework/adapters/card_rpg")
ctx = {
    "character": {"ATK": 100, "DEF": 50, "crit_rate": 0.05, "crit_dmg": 0.5},
    "weapon": {"ATK_bonus": 15},
    "enemy": {"DEF": 60},
    "user_input": {"skill_mult": 1.0, "is_crit": True},
}
result = pkg.dag_service.evaluate(ctx)
print(result.outputs)
# 不动一行框架代码，接入了完全不同的游戏品类
```

---

## 测试你的适配器

```python
# tests/test_my_game_adapter.py
from calc_framework.config.adapter import AdapterPackage

def test_basic_dag_eval():
    pkg = AdapterPackage("framework/adapters/my-game")
    ctx = make_context(character={"基础攻击力": 100},
                       computed={"攻击力百分比": 0.0, "固定攻击力": 0})
    result = pkg.dag_service.evaluate(ctx)
    assert result.outputs["最终攻击力"] == 100.0
```
