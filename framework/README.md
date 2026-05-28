# calc-framework — 通用伤害计算框架

适配任意 RPG 游戏的**公式可配置**伤害计算框架。
公式写在 DAG JSON 中，无需改代码即可调整乘区顺序、增删乘区、修改计算逻辑。

---

## 架构总览

```
┌─────────────────────────────────────────────┐
│               适配包 (AdapterPackage)         │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│  │ meta.json│  │ dag/*    │  │ ui/*      │  │
│  │          │  │ .dag.json│  │ layout.json│  │
│  └──────────┘  └──────────┘  └───────────┘  │
└──────────────────────┬──────────────────────┘
                       │ 加载
┌──────────────────────▼──────────────────────┐
│              框架核心 (calc_framework)        │
│                                              │
│  ┌─────────────┐  ┌──────────────────┐       │
│  │ DAG 引擎     │  │ DataContext      │       │
│  │ 9 种节点类型  │  │ 标准上下文       │       │
│  │ 拓扑排序     │  │ make_context()   │       │
│  │ 子图展开     │  │ DataContextLoader│       │
│  │ AST 沙箱     │  │ (抽象基类)       │       │
│  └─────────────┘  └──────────────────┘       │
│                                              │
│  ┌─────────────┐  ┌──────────────────┐       │
│  │ ComputeSheet│  │ 日志系统          │       │
│  │ 自动渲染输入  │  │ setup_logging() │       │
│  │ 实时求值     │  │ get_logger()    │       │
│  └─────────────┘  └──────────────────┘       │
└──────────────────────────────────────────────┘
```

---

## 快速开始

详见 [`docs/quickstart.md`](docs/quickstart.md)。

```python
from calc_framework.config.adapter import AdapterPackage
from calc_framework.data.loader import DataContextLoader
from calc_framework.data.context import make_context

# 1. 加载适配包
pkg = AdapterPackage("path/to/game-adapter")

# 2. 构建数据上下文
ctx = make_context(
    character={"基础攻击": 100, "力量": 50},
    weapon={"基础攻击": 40},
    computed={"最终攻击力": 140},
)

# 3. 求值
result = pkg.dag_service.evaluate(ctx)
print(result.outputs)
```

---

## 核心模块

### DAG 引擎 — `calc_framework.dag`

| 模块 | 职责 |
|------|------|
| `schema.py` | 9 种节点类型（const/var/unary/binary/condition/expr/user_input/call） |
| `engine.py` | 拓扑排序 + 节点求值 + 默认值回退 |
| `subgraph.py` | call 节点内联展开 |
| `sandbox.py` | AST 解析 + 白名单校验 + 安全求值 |
| `serializer.py` | DAG JSON ↔ DAGGraph |
| `service.py` | DAGService 统一入口 |

### 数据层 — `calc_framework.data`

| 模块 | 职责 |
|------|------|
| `context.py` | DataContext TypedDict + make_context 工厂 |
| `loader.py` | DataContextLoader 抽象基类 |
| `schema.py` | 四层数据契约（EntitySchema / SkillSchema / SegmentSchema） |

### UI 层 — `calc_framework.ui`

| 模块 | 职责 |
|------|------|
| `compute_sheet.py` | 声明式计算表 QWidget，从 DAG + layout.json 自动渲染 |
| `controls.py` | infer_control 根据变量声明推断控件类型 |
| `layout.py` | Layout/Section 排版定义 |
| `format.py` | 数值格式化 |

### 配置层 — `calc_framework.config`

| 模块 | 职责 |
|------|------|
| `adapter.py` | AdapterPackage 加载 meta.json + DAG |

---

## 适配包结构

一个完整的游戏适配包：

```
my-game-adapter/
├── meta.json              # 元信息
├── dag/                   # DAG 公式定义
│   └── main.dag.json
└── ui/                    # UI 排版定义
    └── layout.json
```

`meta.json` 示例：

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

## 构建 DAG 公式

DAG JSON 是框架的核心配置。一个完整 DAG 包含：

```json
{
  "schema_version": "dag-v1",
  "name": "伤害计算",
  "variables": {
    "character.基础攻击": {
      "type": "float",
      "source": "character",
      "description": "角色基础攻击力"
    }
  },
  "subgraphs": {
    "final_attack": { "nodes": { ... }, "outputs": { ... } }
  },
  "nodes": {
    "base_atk": {
      "type": "var",
      "path": "character.基础攻击"
    },
    "total_atk": {
      "type": "binary",
      "op": "+",
      "lhs": "base_atk",
      "rhs": "weapon_atk"
    }
  },
  "outputs": {
    "最终攻击力": { "node": "total_atk", "label": "最终攻击力" }
  }
}
```

---

## 日志

```python
from calc_framework.logging import setup_logging, get_logger

# 在应用入口调用一次
setup_logging(level="INFO", log_file="calc.log")

# 在各模块获取 logger
logger = get_logger(__name__)
logger.info("DAG 求值完成")
```

环境变量控制：`CALC_FRAMEWORK_LOG_LEVEL`（默认 WARNING）、`CALC_FRAMEWORK_LOG_FILE`。

---

## 测试

```bash
cd framework
python -m pytest tests/
```
