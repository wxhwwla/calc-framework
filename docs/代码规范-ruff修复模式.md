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

注意：
- `composite: true` 与 `noEmit: true` **冲突**，需要用 `emitDeclarationOnly: true`
- `outDir` 输出的是 `.d.ts` 声明文件（Vite/esbuild 不依赖它们）
- `dist-types/` 已加入根 `.gitignore`

---

## 变更记录

| 日期 | 说明 |
|------|------|
| 2026-05-28 | 初始版本。基于 `ruff check` 全量修复过程中发现的规律编写。涵盖 E501 / F401 / N806 / E741 四类高频问题。 |
| 2026-05-28 | 新增 §7 Pyright/Pylance 类型检查。记录 `reportArgumentType` / dict 不变性 / QDoubleSpinBox 等典型修复模式与 pre-existing 状态。 |
| 2026-05-28 | 新增 §8 TypeScript 前端诊断。记录隐式 any 事件类型、VS Code 工作区模块解析、Monorepo composite 配置。 |
