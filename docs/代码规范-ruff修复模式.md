# 代码规范与常见 ruff 修复模式

本文档记录本项目在 ruff 严格检查（`select = ["E", "F", "W", "I", "N", "UP", "SIM", "RUF"]`）下反复出现的规范问题及其标准修复模式。

**配置参考**：`endfield_damage_calculator/pyproject.toml` → `[tool.ruff.lint]`

---

## 1. 行超长 (E501)

**规则**：`line-length = 120`。

**典型场景**：dataclass / 无装饰器 class 构造调用在 dict value 位置，一行放不下所有参数。

**修复模式**：断开为多行调用，每个参数单独一行：

```python
# ❌ 超长 (>120)
"main_flat": DAGVariable(type="float", source="computed", description="主能力平值（基础 + 武器平值加成 + 信赖）"),

# ✅ 多行断开
"main_flat": DAGVariable(
    type="float", source="computed",
    description="主能力平值（基础 + 武器平值加成 + 信赖）",
),
```

**注意**：dict value 的尾逗号后面会有 `),` → 结尾括号与逗号的组合，ruff 接受这种写法。

**长描述字符串**：用隐式字符串拼接（括号内相邻字符串字面量自动连接）：

```python
# ❌
description="终末地 15 乘区完整伤害公式 DAG。子图含 ability_bonus / final_attack / single_hit_damage 用于独立校验；主图扁平求值。",

# ✅
description=(
    "终末地 15 乘区完整伤害公式 DAG。"
    "子图含 ability_bonus / final_attack / single_hit_damage 用于独立校验；"
    "主图扁平求值。"
),
```

---

## 2. 未使用的导入 (F401)

### 2.1 可安全删除

**场景**：`import` 后确实未在任何地方使用。

**操作**：`ruff check --fix` 自动删除。**但在批量修复前务必确认是否 re-export。**

### 2.2 `__init__.py` 的显式 re-export

**场景**：`__init__.py` 中 `from .module import X` 是为了对外暴露 API。

**规则**：项目的 `[tool.ruff.lint.per-file-ignores]` 配置中 `"**/__init__.py" = ["F401"]`。因此 `__init__.py` 的 F401 会被允许。

**修复模式**：如果不想用 per-file-ignore，可用显式别名：

```python
# ✅ re-export（ruff 接受）
from .editor import LayoutEditor as LayoutEditor
```

### 2.3 门面模块 (Facade) 的 re-export

**场景**：像 `gui_design/presentation/preview_lines.py` 这样的门面模块，从子模块导入并对外暴露。

```python
# ❌ ruff --fix 会删除这两行
from .preview import build_multi_skill_search_preview_lines
from .preview import build_single_skill_search_preview_lines

# ✅ 显式别名
from .preview import build_multi_skill_search_preview_lines as build_multi_skill_search_preview_lines
from .preview import build_single_skill_search_preview_lines as build_single_skill_search_preview_lines
```

**危险操作**：对非 `__init__.py` 的文件执行 `ruff check --fix` 前，先确认文件中是否有 re-export。批量 `--fix` 不会区分 re-export 和真正未使用的导入。

---

## 3. 变量命名 (N806)

**规则**：函数/方法内的局部变量用小写 `snake_case`。全大写仅用于模块级常量。

```python
# ❌ N806
def compute_zone(selection):
    ATTR_DISPLAY_ORDER = ("力量", "敏捷", "智识", "意志")

# ✅
def compute_zone(selection):
    attr_display_order = ("力量", "敏捷", "智识", "意志")
```

**注意**：项目配置已忽略 `N803`（允许参数名大写，与数据字段名一致）。

---

## 4. 歧义变量名 (E741)

**规则**：禁止用 `l`（像 `1`）、`O`（像 `0`）、`I`（像 `l`）。

```python
# ❌ E741
dag_final = [l for l in dag_lines if l.text.startswith("最终攻击力:")][0]

# ✅
dag_final = [line for line in dag_lines if line.text.startswith("最终攻击力:")][0]
```

---

## 5. 特定文件忽略（per-file-ignores）

部分文件因结构特殊性需要在项目级忽略特定规则。新增文件时，如果确实需要忽略，添加到 `pyproject.toml` → `[tool.ruff.lint.per-file-ignores]`：

```toml
[tool.ruff.lint.per-file-ignores]
"tests/*" = ["RUF", "N802", "N806", "SIM115"]
"gui_design/*" = ["N802", "N806"]
"**/__init__.py" = ["F401"]
```

**原则**：per-file-ignore 只在必要的情况下使用，不应掩盖真正可修复的问题。

---

## 6. 日常工作流

```bash
# 快速检查
ruff check

# 自动修复（安全操作）
ruff check --fix

# ⚠️ auto-fix 前先手动审查：确认没有 re-export 被误删
# 审查命令：只看 F401 结果
ruff check --select F401

# 全量回归
python -m pytest tests/ -q
```

**习惯**：
- 提交前必跑 `ruff check`
- `ruff check --fix` 后必跑全量回归
- 对非 `__init__.py` 文件的 F401 fix 要单独审查

---

## 7. Pyright / Pylance 类型检查

### 7.1 pyrightconfig.json 抑制规则

项目根目录 [`pyrightconfig.json`](../pyrightconfig.json) 配置了 `typeCheckingMode: standard` 并抑制了以下不适合本项目的规则：

| 抑制的规则 | 原因 |
|-----------|------|
| `reportAttributeAccessIssue` | 双后端（CTk + PySide6）共用 Any 类型访问 |
| `reportMissingImports` | 独立脚本通过 sys.path.insert 添加路径 |
| `reportOptionalMemberAccess` | 大量 `dict.get()` 和可选链模式的正常用法 |
| `reportInconsistentConstructor` | GUI mixin 多重继承的构造差异 |
| `reportPrivateImportUsage` | 内部模块跨目录引用 |

### 7.2 常见类型错误与修复

**dict 值类型不变性 (invariance)**

pyright 严格检查 `dict[K, V]` 的值类型。`dict[str, SubType]` 不能赋值给 `dict[str, SuperType]`。

```python
# ❌ reportArgumentType
# 函数签名: def f(variables: dict[str, DAGVariable | dict[str, Any]])
# 调用: f(variables=dag.variables)  # dag.variables 类型是 dict[str, DAGVariable]
# pyright 报错: dict[str, DAGVariable] 不能赋值给 dict[str, DAGVariable | dict[str, Any]]

# ✅ 修复：将参数类型缩窄为实际调用类型
# 函数签名: def f(variables: dict[str, DAGVariable])
```

**QDoubleSpinBox setMinimum/setMaximum**

PySide6 类型 stub 将 `setMinimum`/`setMaximum` 标注为 `int`（继承自 `QAbstractSpinBox`），但 `QDoubleSpinBox` 实际接受 `float`。

```python
# ✅
box.setMinimum(spec.min_val)  # type: ignore[reportArgumentType]
box.setMaximum(spec.max_val)  # type: ignore[reportArgumentType]
```

**`**kwargs` 拆包 + 联合值类型**

当函数返回 `dict[str, int | str]` 时，`**` 拆包后每个 keyword 值被推断为 `int | str`，无法赋值给分别要求 `int` 或 `str` 的形参。

```python
# 根源：返回类型过窄
def calculation_kwargs(self) -> dict[str, int | str]:  # ← 联合值类型
    return {"name": "abc", "level": 1}

# ❌ 拆包后每个值都是 int | str
def f(*, name: str, level: int): ...
f(**calculation_kwargs())  # reportArgumentType ×2

# ✅ 修复：调用点标注为 dict[str, Any]（拆包语义上确实是 Any）
kwargs: dict[str, Any] = obj.calculation_kwargs()
f(**kwargs)
```

> **原则**：`**kwargs` 拆包在 Python 类型系统中无法保留 per-key 粒度。当返回 `dict[str, T1 | T2]` 时，应该标注变量为 `dict[str, Any]`，在拆包前 "抹平" 联合类型。这不应滥用——只在 `**` 拆包场景下使用。

### 7.3 当前 pyright 状态（2026-05-28）

| 端 | 总错误 | 本轮修复引入 | 本轮修复消除 | 剩余 pre-existing | 核心来源 |
|----|--------|------------|------------|-----------------|---------|
| 包端 | 390 | 0 | 148 | 390 | 测试 `dict` 解包 + gui_design mixin + shell 桥接 |
| 框架 | 3 | 0 | 0 | 3 | `sandbox.py` ast 类型 + `test_context.py` TypedDict |

**pre-existing 说明**（不打算大批量修复）：

- **`reportArgumentType` (364)**：主要在 `tests/`（~338）和 `gui_design/shell/`。测试文件将松散 `dict` 传递给严格类型签名，修复需结构性修改测试基类。
- **`reportGeneralTypeIssues` (14)**：gui_design mixin 模式（`Self@Mixin` 类型推断），不影响运行时。
- **框架 pre-existing (3)**：`sandbox.py` 的 ast `_ConstantValue` 和 `test_context.py` 的 TypedDict 协变，深度类型问题。
- **本轮消除 148 个**：`zone_snapshot.py` 和 `adapter.py` 的 `**kwargs` + `int|str` 级联错误，在调用点标注 `dict[str, Any]`。

### 7.4 VS Code Problems 面板

VS Code 的 `#problems_and_diagnostics` 面板显示 Pylance + ruff 的全部诊断。当前面板中的问题来自上述 pre-existing 项，而非本轮新引入。

ruff 双端 **All checks passed**，pyright 我们引入的 5 处错误已全部修复。

---

## 8. TypeScript 前端诊断（web/ 子项目）

`web/` 目录下的 React + TypeScript 前端有一个独立的 `tsconfig.json` 和 `node_modules/`，诊断规则与 Python 后端不同。

### 8.1 隐式 any 类型（ts(7006)）

**规则**：`tsconfig.json` 中 `strict: true` 包含 `noImplicitAny`。

**典型场景**：MUI 组件的事件回调没有类型标注。

```tsx
// ❌ 参数 "e" 隐式具有 "any" 类型
<Select onChange={(e) => selectAdapter(e.target.value)} />

// ✅ 添加事件类型
import type { SelectChangeEvent } from "@mui/material/Select";
<Select onChange={(e: SelectChangeEvent) => selectAdapter(e.target.value)} />

// ✅ 通用 DOM 事件
<Switch onChange={(e: React.ChangeEvent<HTMLInputElement>) => setParam(key, e.target.checked)} />
<TextField onChange={(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => ...} />
```

**修复模式**：MUI 组件优先使用 MUI 专有类型（`SelectChangeEvent`），通用 HTML 控件用 `React.ChangeEvent<HTMLInputElement>`。

### 8.2 VS Code 工作区找不到模块（ts(2307) — 仅 VS Code 面板）

**症状**：`#problems_and_diagnostics` 面板显示大量"找不到模块"错误，但 `npm run build`（`tsc -b && vite build`）通过。

**根因**：这是 **VS Code 工作区级别的假阳性**，不是真正的构建错误。原因：

1. VS Code 打开的是仓库根目录（`e:\endfield_damage_calculator\`）
2. 根目录没有 `tsconfig.json`（或与 `web/frontend/` 无关），VS Code 的 TS language service 使用推断的配置
3. 推断配置不知道 `web/frontend/node_modules/` 的存在，因此无法解析 `react`、`@mui/material`、`vite` 等模块

**修复方案**：

| 层级 | 方案 | 说明 |
|------|------|------|
| 项目级 | 添加根 `tsconfig.json` 用 `references` | 已实施：根 `tsconfig.json` → `{ "references": [{ "path": "web/frontend" }] }` |
| 前端 | `web/frontend/tsconfig.json` 加 `composite: true` | 已实施，同时配置 `emitDeclarationOnly` + `outDir` |
| 用户级 | 重新打开 VS Code 或重载 TS Server | `Ctrl+Shift+P` → `TypeScript: Reload Project` |

**如果仍然出现**：这是 VS Code 工作区缓存问题，不影响 CI 和实际构建。可打开 `web/frontend/` 作为单独工作区根来彻底消除。

### 8.3 项目引用配置（composite）

当 Monorepo 根 `tsconfig.json` 使用 `references` 引用子项目时，子项目 `tsconfig.json` 必须满足：

```jsonc
// web/frontend/tsconfig.json — 被引用的子项目
{
  "compilerOptions": {
    "composite": true,                    // 必须
    "emitDeclarationOnly": true,          // 替代 noEmit（Vite 负责打包）
    "outDir": "./dist-types",             // 声明输出目录
    "tsBuildInfoFile": "./dist-types/tsconfig.tsbuildinfo",
    "rootDir": ".",                       // 明确指定
  }
}
```

### 7.5 `QLayout.addWidget` 的 `stretch` 参数 — 类型收窄

**背景**：通过 `widget.layout()` 获取的布局返回类型为 `QLayout | None`，Pylance 推断为基类 `QLayout`。而 `QLayout.addWidget(w)` 只接受 1 个参数（widget），不接受 `stretch` 关键字参数。`stretch` 仅在 `QBoxLayout.addWidget(w, stretch, alignment)` 上可用。

**现象**：Pylance 报错 `没有名为"stretch"的参数` 或 `应为 1 个位置参数`。

**修复模式**：使用 `assert isinstance()` 将类型收窄为子类（`QVBoxLayout` / `QHBoxLayout`）：

```python
# ❌ Pylance 报错（QLayout.addWidget 无 stretch 参数）
sheet_layout = self._compute_sheet_widget.layout()  # 类型: QLayout | None
sheet_layout.addWidget(widget, stretch=1)

# ✅ assert isinstance 收窄类型
sheet_layout = self._compute_sheet_widget.layout()
assert isinstance(sheet_layout, QVBoxLayout)   # 告知 Pylance 实际类型
sheet_layout.addWidget(widget, stretch=1)       # 现在 QVBoxLayout.addWidget 接受 stretch
```

**原理**：`QVBoxLayout` → `QHBoxLayout` → `QBoxLayout` 全部继承自 `QLayout`。`QWidget.layout()` 返回基类指针，但运行时实际类型就是创建时指定的子类。`assert isinstance` 在运行时可被 `-O` 移除（零成本 assert），同时在静态分析层面完成类型收窄。

**适用场景**：任何通过 `widget.layout()` 获取布局后需要调用 `stretch` 关键字参数的地方。

**例外**：直接创建的 `QVBoxLayout()` / `QHBoxLayout()` 局部变量无需收窄，因为 Pylance 已经知道它们的类型。

---

## 9. 常见 Pylance 类型诊断与修复（持续更新）

本节记录本项目中反复出现的 Pylance（pyright）类型诊断问题及其标准修复模式。不同于 §7（pyright CLI 的 pre-existing 宏观状态），本节聚焦**可立即修复的具体模式**。

---

### 9.1 `from __future__ import annotations` 破坏 dataclass 类型推断

**根源**：`from __future__ import annotations` 将所有注解变为惰性求值的字符串，Pylance 无法正确推断 `@dataclass` 生成的 `__init__` 签名。这导致所有 dataclass 的构造调用参数都报 `没有名为"xxx"的参数`。

```python
# ❌ schema.py 顶部有 from __future__ import annotations
# Pylance 报错：test_file_io.py 中 GraphDocument(name=..., nodes=...)
# → "没有名为 name/nodes/edges/layout 的参数"

# ✅ 移除 from __future__ import annotations
# Python 3.13 原生支持 list[X] / dict[str, X] / X | Y 语法，无需此导入
```

**检查清单**：所有 `@dataclass` 所在的文件都应检查是否因遗留原因保留了 `from __future__ import annotations`。在 Python ≥ 3.10 项目中，仅当需要在 `isinstance` 中使用 `str | int` 等联合类型注解时才需要此导入（3.10 之前只能用 `Optional[str]`）。Python 3.13 已完全支持类型运算中的原生泛型，通常不需要。

**修复模式**：

```python
# ❌ 有 from __future__ import annotations
# Pylance → GraphDocument 构造参数不可见
@dataclass
class GraphDocument:
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)
    ...

# ✅ 无 from __future__ import annotations
# Pylance 正确推断：GraphDocument(nodes=..., edges=..., ...)
@dataclass
class GraphDocument:
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)
```

---

### 9.2 嵌套函数向前引用（reportUnboundVariable）

**根源**：Pylance 静态分析要求变量/函数在被引用之前已定义。在嵌套函数（`def fn()` 定义在 `def outer()` 内部）中，如果先 `connect(fn)` 再 `def fn()`，Pylance 认为 `fn` 未绑定。

```python
# ❌ Pylance 报错: "fn" 未绑定
prop_panel.node_changed.connect(_on_node_config_changed)  # ← 此时 _on_node_config_changed 尚未定义

def _on_node_config_changed(node_id: str) -> None:
    ...

# ✅ 修复：先定义函数，再绑定信号
def _on_node_config_changed(node_id: str) -> None:
    ...

prop_panel.node_changed.connect(_on_node_config_changed)
```

**原理**：Python 运行时对于嵌套函数确实允许向前引用（函数定义在运行时一次性执行，`def` 语句执行前函数名不存在）。但 Pylance 遵循静态分析规则，无法确定运行时执行顺序。标准做法是将 `connect` 调用放在函数定义之后。

**适用场景**：任何在 Qt 信号连接、装饰器、回调注册等场景中引用尚未定义的嵌套函数的地方。

---

### 9.3 字符串赋值给 Literal 类型（reportArgumentType）

**根源**：`NodeType = Literal["const", "var", ...]` 是严格的联合字面量类型。从外部来源（JSON 反序列化、用户输入、注册表 key）获取的 `str` 值无法直接赋值给 `NodeType`，即使运行时可确保值的合法性。

```python
# ❌ Pylance 报错: 类型 "str" 不可分配给类型 "Literal['const', 'var', ...]"
node.type = json_dict.get("type", "const")  # d.get() 返回 str

# ✅ 修复：在边界处用 cast() 类型转换
from typing import cast
node.type = cast(NodeType, json_dict.get("type", "const"))
```

**原则**：`cast()` 应仅在**边界处**使用——即值来自类型系统无法验证的外部来源（JSON、数据库、用户输入），但业务逻辑已经确保其合法性的场景。不要在内部纯计算链中使用 `cast()`。

**安全前提**：对于 `NodeType`，调用 `cast` 之前应有校验函数（如 `validate_graph()`）确保值属于 `VALID_NODE_TYPES`。也可在 `cast` 之前加 `assert`：

```python
type_str = json_dict.get("type", "const")
assert type_str in VALID_NODE_TYPES, f"无效节点类型: {type_str}"
node.type = cast(NodeType, type_str)
```

---

### 9.4 函数返回类型 `-> float` 与可选 `str` 返回值冲突（reportReturnType）

**根源**：当函数需要在特定条件下返回字符串（而非 float）时，如果函数签名标注 `-> float`，Pylance 会报错。

```python
# ❌ Pylance 报错: 类型 "str" 不可分配给返回类型 "float"
def _eval_node(node, scope) -> float:
    if isinstance(node.value, str):
        return node.value       # ← str 不能赋值给 float
    return float(node.value)

# ✅ 修复：返回类型改为 Any（调用方负责类型判断）
def _eval_node(node, scope) -> Any:
    if isinstance(node.value, str):
        return node.value       # 字符串常量保持原值
    if isinstance(node.value, (int, float)):
        return float(node.value)
    raise ValueError(f"不支持的常量类型: {type(node.value).__name__}")
```

**适用场景**：求值器、解释器、表达式引擎等需要处理多类型常量的函数。返回 `Any` 表示调用方应使用 `isinstance` 检查实际返回类型。

---

### 9.5 `float(x)` 接收非数值类型（reportArgumentType）

**根源**：`ast.Constant.value` 的类型是 `_ConstantValue`（`bytes | bool | int | float | complex | str | EllipsisType | None` 的联合）。对任意值不加区地调用 `float()` 会触发 Pylance 的 `reportArgumentType`，因为 `EllipsisType` / `bytes` / `complex` 等类型无法转换为 `float`。

```python
# ❌ Pylance 报错: "bytes | bool | int | float | complex | EllipsisType | None" 不可赋值给 "ConvertibleToFloat"
return float(node.value)  # EllipsisType / bytes / complex 不可转换

# ✅ 修复：isinstance 守卫窄化类型
if isinstance(node.value, (int, float)):
    return float(node.value)
raise DAGRuntimeError(f"不支持的常量类型: {type(node.value).__name__}")
```

**原则**：在调用 `float(x)` / `int(x)` 之前，先用 `isinstance` 过滤掉不支持的类型。这既是类型安全的，也是运行时安全的。

---

### 9.6 修复模式速查表

| # | 症状 | 修复 | 关键字 |
|---|------|------|--------|
| 9.1 | `没有名为"xxx"的参数` (dataclass) | 移除 `from __future__ import annotations` | `__future__` / dataclass |
| 9.2 | `"fn" 未绑定` (嵌套函数) | 把 `connect(fn)` 移到 `def fn()` 之后 | forward ref / unbound |
| 9.3 | `"str" 不可分配给 Literal` | 边界处 `cast(LiteralType, value)` + 前置 `assert` | cast / Literal |
| 9.4 | `"str" 不可分配给 "float"` | 返回类型改为 `-> Any` | return type / Any |
| 9.5 | `EllipsisType 无法转 float` | `isinstance` 守卫窄化 + 抛异常 | isinstance guard / float |

---

## 10. 诊断工作流总结

```bash
# VS Code Problems 面板 — 查看全部诊断
# 使用 `#problems_and_diagnostics` 查看实时状态

# ruff 检查（不影响类型诊断）
ruff check

# pyright 专项检查
pyright .

# 全量回归验证
python -m pytest tests/ -q
```

---

## 变更记录

| 日期 | 说明 |
|------|------|
| 2026-05-28 | 初始版本。基于 `ruff check` 全量修复过程中发现的规律编写。涵盖 E501 / F401 / N806 / E741 四类高频问题。 |
| 2026-05-28 | 新增 §7 Pyright/Pylance 类型检查。记录 `reportArgumentType` / dict 不变性 / QDoubleSpinBox 等典型修复模式与 pre-existing 状态。 |
| 2026-05-28 | 新增 §8 TypeScript 前端诊断。记录隐式 any 事件类型、VS Code 工作区模块解析、Monorepo composite 配置。 |
| 2026-05-28 | 新增 §7.5 `QLayout.addWidget` stretch 参数类型收窄模式。新增 §9 诊断工作流总结。 |
| 2026-05-28 | 新增 §9 Pylance 可选依赖模式。记录 try/except 条件导入的 _QtWidgets/_QtGui 未绑定问题及修复方案。 |
| 2026-05-29 | 新增 §9.1–§9.6 Pylance 常见诊断模式。记录 `__future__` annotations 破坏 dataclass、嵌套函数向前引用、str→Literal cast、返回类型 Any、isinstance 守卫 float 转换。 |

---

## 9. Pylance 可选依赖条件导入模式

### 9.1 问题描述

当代码通过 `try/except ImportError` + `if guard` 实现可选依赖时，Pylance（VS Code 的类型检查器）无法理解这种运行时条件模式，会认为在 `if _HAS_PYSIDE:` 块内部的 `_QtWidgets`、`_QtGui` 等导入变量**可能未绑定**。

**典型报错**：

```
"_QtWidgets" 可能未绑定   (reportGeneralTypeIssues)
```

**根因**：Pylance 的静态分析在 `try/except` 之后无法确定 `_QtWidgets` 是否确实被赋值。虽然运行时因为 `_HAS_PYSIDE` guard 保证了 `_QtWidgets` 一定存在，但 Pylance 不追踪 `if guard` 和 `try` 的关联性。

此外，`if/else` 各定义一个同名类也会触发：

```
类声明"StepDebuggerWidget"被同名的声明遮蔽   (reportGeneralTypeIssues)
```

### 9.2 修复方案

**方案 A（推荐）**：在 `if` 块内使用 `type: ignore[no-redef]`，在 **每个** 使用到可选导入变量的行加 `type: ignore[reportGeneralTypeIssues]`。

```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6 import QtGui as _QtGui
    from PySide6 import QtWidgets as _QtWidgets

try:
    from PySide6 import QtGui as _QtGui
    from PySide6 import QtWidgets as _QtWidgets
    _HAS_PYSIDE = True
except ImportError:
    _HAS_PYSIDE = False


if _HAS_PYSIDE:

    class StepDebuggerWidget(_QtWidgets.QWidget):  # type: ignore[no-redef]
        def __init__(self) -> None:
            super().__init__()
            layout = _QtWidgets.QVBoxLayout(self)  # type: ignore[reportGeneralTypeIssues]
            ...
else:

    class StepDebuggerWidget:  # type: ignore[no-redef]
        ...
```

| 标注 | 解决什么问题 | 加在哪里 |
|------|------------|---------|
| `TYPE_CHECKING` 导入 | 为 Pylance 提供类型信息（解决 `type: ignore` 时的裸类型需求） | `if TYPE_CHECKING:` 块 |
| `no-redef` | 同名类在两个分支定义 | `class` 行 |
| `reportGeneralTypeIssues` | 可选导入的变量 `_QtWidgets` 等被认为未绑定 | **每个**使用到这些变量的行 |

**方案 B（不推荐）**：使用 `cast()` 或 `Any` 类型标注。但这样会丢失具体的类型信息，IDE 代码补全也会失效。

**方案 C（不推荐）**：使用 `importlib.util.find_spec` 代替 `try/except`。但这同样无法解决 Pylance 的静态推断限制。

### 9.3 TYPE_CHECKING 模式详解

`TYPE_CHECKING` 是 Python 3.5+ 内置常量，仅在类型检查时（如 Pylance/pyright/mypy）为 `True`，运行时为 `False`。利用此特性，可以为 `try/except` 可选导入提供类型信息：

```python
from __future__ import annotations
from typing import TYPE_CHECKING

# 类型检查时：使 Pylance 知道这两个模块的存在和类型
# 运行时：不导入，避免拉取未安装的依赖
if TYPE_CHECKING:
    from PySide6 import QtGui as _QtGui
    from PySide6 import QtWidgets as _QtWidgets

try:
    from PySide6 import QtGui as _QtGui    # 运行时真实导入
    from PySide6 import QtWidgets as _QtWidgets
    _HAS_PYSIDE = True
except ImportError:
    _HAS_PYSIDE = False
```

**关键注意点**：

1. `TYPE_CHECKING` 块中的导入必须与其他导入同级（顶层），不能放在 `if _HAS_PYSIDE:` 内部
2. `from __future__ import annotations` 是必要的——它将所有注解变为惰性求值的字符串，避免 `TYPE_CHECKING` 中的类型在运行时被实际求值
3. 类型检查时有效的类、函数签名中的 `QtWidgets.QWidget`、`DAGGraph` 等类型引用都依赖此机制
4. 运行时 `_QtWidgets` 仍然来自 `try` 块的 `import`，`TYPE_CHECKING` 块不影响运行时行为

### 9.4 与现有模式的比较

| 模式 | 解决 | 不解决 |
|------|------|--------|
| **§7.2 QDoubleSpinBox** | stub 类型错误 `int≠float` | — |
| **§7.2 `**kwargs` 拆包** | 联合值类型无法匹配形参 | — |
| **§9.2 try/except 可选依赖** | `_QtWidgets` 可能未绑定 + 类遮蔽 | 每行一个 `type: ignore` 的冗长问题 |

**原则**：`type: ignore` 不是"脏标记"，而是告知类型检查器"我知道这个边界情况，请接受"。在可选依赖场景下，这是无法避免的。核心代码应尽量减少此类标注，但工具/ui 代码可以接受。

### 9.5 当前 VS Code 诊断状态（2026-05-28）

| 文件 | 诊断数 | 说明 |
|------|--------|------|
| `debugger_gui.py` | **0** | 已用 §9 模式完全修复 |
| 框架其他文件 | **0** | 无诊断 |
| 包端 | **0** | `pyrightconfig.json` 的 `include` 限定到 `endfield_damage_calculator`，不含 `web/` |
| Web 前端 | **0** | `tsc --noEmit` 通过 |
| **总计** | **0** | ✅ 全零 |
