# calc-framework — 通用伤害计算框架

适配任意 RPG 游戏的**公式可配置**伤害计算框架。
公式写在 DAG JSON 中，无需改代码即可调整乘区顺序、增删乘区、修改计算逻辑。

---

## 架构总览

> **注意**：通过 `pip install calc-framework-endfield` 安装后，DAG 引擎、搜索、inverse 等计算核心功能开箱即用。GUI 功能（CalcPackViewer、ComputeSheet、启动器、图编辑器）需要本项目完整环境（含 `utils/`、`tools/` 等目录），在纯 pip 安装环境下不可用。

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
| `serializer.py` | DAG JSON ↔ DAGGraph（加载时自动展开模板引用） |
| `service.py` | DAGService 统一入口 |
| `templates.py` | 可复用公式模板库（5 内置模板，支持 ``"template"`` 字段引用） |

### 配置/加载层 — `calc_framework.config`

| 模块 | 职责 |
|------|------|
| `adapter.py` | 适配包加载器（meta.json → DAGService） |
| `manager.py` | 适配器管理器（发现/缓存/加载多个适配包） |

### 搜索/枚举引擎 — `calc_framework.search`

| 模块 | 职责 |
|------|------|
| `engine.py` | 搜索引擎核心（枚举空间 + 遍历策略） |
| `tracker.py` | Top-N 结果追踪（通用泛型） |
| `parallel.py` | 并行执行器（进度回调、Top-N、取消） |
| `persist.py` | 搜索进度持久化（SQLite） |
| `session.py` | 搜索会话管理 |
| `result.py` | 通用搜索结果类型 |

适用于任何需要遍历大量候选并保留最优结果的场景（配装搜索、参数枚举、伤害最大化等）。

### 插件系统 — `calc_framework.plugin`

| 模块 | 职责 |
|------|------|
| `base.py` | BasePlugin / PluginMeta 基类 |
| `registry.py` | PluginRegistry 全局注册表 |
| `builtin.py` | 3 内置插件（crit_handler / dodge_handler / distance_decay） |

### 发布/分享 — `calc_framework.publish`

| 模块 | 职责 |
|------|------|
| `schema.py` | JSON Schema 校验（validate_package） |
| `catalog.py` | 静态 HTML 目录生成（build_catalog） |

### 数据层 — `calc_framework.data`

| 模块 | 职责 |
|------|------|
| `context.py` | DataContext TypedDict + make_context 工厂 |
| `loader.py` | DataContextLoader 抽象基类 |
| `schema.py` | 四层数据契约（EntitySchema / SkillSchema / SegmentSchema） |
| `attr_schema.py` | 属性声明 Schema — 适配器声明字段结构，框架自动构建 DataContext（resolve/validate） |

### UI 层 — `calc_framework.ui`

| 模块 | 职责 |
|------|------|
| `compute_sheet.py` | 声明式计算表 QWidget，从 DAG + layout.json 自动渲染 |
| `controls.py` | infer_control 根据变量声明推断控件类型 |
| `layout.py` | Layout/Section 排版定义 |
| `theme.py` | ThemeManager 多主题管理（dark/light/high_contrast） |
| `viewer.py` | CalcPackViewer 通用展示层 |
| `viewer_render.py` | 查看器动态渲染引擎 |
| `sheet_evaluator.py` | ComputeSheet 实时求值器 |
| `sheet_widgets.py` | 输入控件工厂 |

### 逆推引擎 — `calc_framework.inverse`

| 模块 | 职责 |
|------|------|
| `base.py` | FormulaFitter 基类与类型定义 |
| `engine.py` | InverseEngine 统一逆推入口 |
| `registry.py` | FormulaType 注册表 |
| `strategies.py` | 通用拟合策略（floor/growth 等） |
| `exponential_fitter.py` | 指数公式拟合器 |
| `piecewise_fitter.py` | 分段公式拟合器 |
| `threshold_fitter.py` | 阈值公式拟合器 |

### 图编辑器 — `calc_framework.graph_editor`

| 模块 | 职责 |
|------|------|
| 可视化 DAG 编辑画布 | QGraphicsView 节点拖拽、连线、网格吸附 |
| 复合节点支持 | 双击进入子图编辑 |
| 模板管理 | 内置模板浏览与插入 |

### 开发者工具箱 — `calc_framework.dev_toolkit`

CLI 工具集，含 DAG 调试器、图验证、模板管理等开发辅助功能。

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
├── attr_schema.json       # 属性声明 Schema（可选）
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

也可引用 `attr_schema.json` 和自定义函数：

```json
{
  "name": "卡牌RPG伤害计算",
  "game": "经典卡牌RPG（示例）",
  "version": "1.0.0",
  "schema_version": "dag-v1",
  "entry_dag": "card_rpg.dag.json",
  "attr_schema": "attr_schema.json",
  "functions": {
    "clamp": "functions.py"
  }
}
```

## 适配器示例

### 终末地（15 乘区）

`framework/adapters/endfield/` — 真实游戏完整适配器，含角色/武器/装备数据和 15 乘区 DAG。

### 卡牌RPG（攻击-防御公式）— [详细文档](adapters/card_rpg/README.md)

`framework/adapters/card_rpg/` — 示例适配器，证明框架跨品类通用。经典回合制减法公式：

```
最终伤害 = max((ATK + ATK_bonus) × skill_mult - DEF × 0.5, 0) × crit_mult
```

### FPS 武器伤害 — [详细文档](adapters/fps/README.md)

`framework/adapters/fps/` — 通用 FPS 伤害公式，含距离衰减、部位倍率、护甲穿透：

```
单发伤害 = base_damage × 部位倍率 × 距离衰减 × (1 - 护甲减伤比)
```

### MOBA 英雄伤害 — [详细文档](adapters/moba/README.md)

`framework/adapters/moba/` — 通用 MOBA 伤害公式，含 AD/AP 加成、双抗减伤、暴击、冷却缩减：

```
技能总伤害 = (skill_base + ad_ratio×AD + ap_ratio×AP) × crit_mult × (1 - 减伤比)
```

```python
from calc_framework.config.adapter import AdapterPackage

# 加载卡牌RPG适配器
pkg = AdapterPackage("framework/adapters/card_rpg")

# 构建上下文并求值
ctx = {
    "character": {"ATK": 100, "crit_rate": 0.05, "crit_dmg": 0.5},
    "weapon": {"ATK_bonus": 15},
    "enemy": {"DEF": 60},
    "user_input": {"skill_mult": 1.0, "is_crit": True},
}
result = pkg.dag_service.evaluate(ctx)
print(result.outputs)
# {"总攻击力": 115.0, "基础伤害": 85.0, "暴击倍率": 1.5, "最终伤害": 127.5}
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

### DAG 模板

框架内置 5 个通用公式模板（`defense_reduction`、`crit_multiplier`、`clamp_to_range`、`percent_of`、`attribute_scaling`），可在 DAG JSON 中直接引用：

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

加载时自动展开为完整节点。也可通过 `register_template()` 注册自定义模板。

---

## 日志

```python
from calc_framework.logging import setup_logging, get_logger
from calc_framework.data.attr_schema import AttributeSchema

# 在应用入口调用一次
setup_logging(level="INFO", log_file="calc.log")

# 在各模块获取 logger
logger = get_logger(__name__)
logger.info("DAG 求值完成")

# 加载属性 Schema
schema = AttributeSchema.from_file("attr_schema.json")
ctx = schema.resolve(raw_data)
errors = schema.validate(ctx)
```

环境变量控制：`CALC_FRAMEWORK_LOG_LEVEL`（默认 WARNING）、`CALC_FRAMEWORK_LOG_FILE`。

## 游戏启动器

通过 ``calc_framework.launcher`` 可交互选择适配包并启动 ComputeSheet GUI：

```bash
# 交互选择
python -m calc_framework.launcher

# 直接指定
python -m calc_framework.launcher "终末地计算器（Calc Framework）"
```

适配器搜索路径由 ``CALC_ADAPTERS_DIR`` 环境变量控制（默认 ``framework/adapters/``）。

## 发布 Catalog

```bash
python -c "from calc_framework.publish import build_catalog; build_catalog('dist')"
```

生成 ``dist/index.html``，可部署到 GitHub Pages 作为社区适配器市场。

---

## 开发与测试

---

## 测试

```bash
cd framework
python -m pytest tests/ -q    # 293 passed
```
