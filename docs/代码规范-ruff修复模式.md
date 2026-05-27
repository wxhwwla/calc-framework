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

## 变更记录

| 日期 | 说明 |
|------|------|
| 2026-05-28 | 初始版本。基于 `ruff check` 全量修复过程中发现的规律编写。涵盖 E501 / F401 / N806 / E741 四类高频问题。 |
