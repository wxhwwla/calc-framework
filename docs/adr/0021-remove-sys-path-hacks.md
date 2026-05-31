# ADR-0021：移除 sys.path hack

## 状态

已采纳

## 上下文

项目中存在多处模块加载时修改 `sys.path` 的 hack，总计 9 处，分布在两个区域：

### A. Web 后端（`web/backend/`）— 7 处

所有 API 模块最终都被 `web/backend/main.py` 导入。Python 的模块导入在同一进程内共享 `sys.path`，因此一旦 `main.py` 设置了路径，后续 API 模块的导入自动继承。

| 文件 | sys.path hack | 实际用途 | 分类 |
|------|---------------|----------|------|
| `web/backend/main.py` | `framework/src` | `from calc_framework.logging import …` | 入口（现通过 `_path_setup.py` 集中处理） |
| `web/backend/api/compute.py` | `framework/src` | `from calc_framework.config.manager import …` | **冗余**—main.py 已设 |
| `web/backend/api/adapters.py` | `framework/src` | `from calc_framework.config.manager import …` | **冗余**—main.py 已设 |
| `web/backend/api/search.py` | `framework/src` + `repo_root` | `from calc_framework.*`、`from calc_engine.*`（lazy import） | **冗余**—main.py 仅设了 framework/src，缺少 repo_root |
| `web/backend/api/data.py` | `repo_root` | `from calc_engine.*`（lazy import 在函数内） | **冗余**—main.py 导入链覆盖 |
| `web/backend/api/pack.py` | `tools` | **从不导入 tools 下的任何模块** | **死代码** |
| `web/hub/build_plugin_catalog.py` | `framework/src` | `from calc_framework.plugin.*` | 独立脚本，需保留但可函数化 |

`search.py` 和 `data.py` 的问题在于它们还需要 `calc_engine`（位于仓库根），而 `main.py` 只设了 `framework/src`。因此 `main.py` 设置的路径不完整。

### B. DAG 适配器（`calc_engine/endfield/calc/dag_adapter/`）— 2 处

| 文件 | sys.path hack | 实际用途 |
|------|---------------|----------|
| `dag_adapter/adapter.py` | `framework/src` + `framework/adapters/endfield` | `from calc_framework.config.adapter import …` |
| `dag_adapter/config.py` | `framework/src` | `from calc_framework.dag.schema import …` |

这两个文件作为 `calc_engine` 的子模块，需要访问 `calc_framework`。在 `calc-framework` 未以 pip 包形式安装时，需要 sys.path hack 作为回退。

### 问题

1. **重复**：同一个路径设置逻辑在 7 个文件中重复，违反 DRY 原则。
2. **隐藏依赖**：新开发者看到 `sys.path.insert` 而不清楚哪些路径是必需的。
3. **死代码**：`pack.py` 的 hack 从不生效，是一个遗留产物。
4. **不完整**：`main.py` 只设了 `framework/src`，但 `search.py` 和 `data.py` 还需要仓库根路径。

## 决策

### Web 后端

1. **创建 `web/backend/_path_setup.py`**—集中设置所有必需路径。
2. **`main.py` 导入 `_path_setup`**，移除其内联 sys.path hack。
3. **移除所有 API 模块的 sys.path hack**——路径由 `main.py` 通过 `_path_setup` 统一设置。
4. **`build_plugin_catalog.py`** 将 hack 移入 `_discover_builtin_plugins()` 函数体（延迟执行），避免模块加载时的副作用。

### DAG 适配器

`dag_adapter/adapter.py` 和 `dag_adapter/config.py` 的 sys.path hack 是已知的技术债务，但它们的上下文不同于 Web 后端：

- 这些文件可能在任何上下文中被导入（GUI 运行时、测试、Web API）
- 正确的修复方式是确保 `calc-framework` 以 pip 包形式安装
- 目前保留 hacks 但将其**函数化为延迟执行的 guard**，减少模块加载时的副作用

### 预期结果

```
重构前：
  main.py        → sys.path.insert("framework/src")
  api/compute.py → sys.path.insert("framework/src")     ← 冗余
  api/adapters.py→ sys.path.insert("framework/src")     ← 冗余
  api/search.py  → sys.path.insert("framework/src")     ← 冗余
                   sys.path.insert("repo_root")         ← 冗余
  api/data.py    → sys.path.insert("repo_root")         ← 冗余
  api/pack.py    → sys.path.insert("tools")             ← 死代码
  build_plugin_catalog.py → sys.path.insert("framework/src") ← 独立脚本保留

重构后：
  _path_setup.py → 集中设置 framework/src + repo_root
  main.py        → from . import _path_setup  （相对导入，web/backend/ 已成为标准包）
  api/*.py       → 无 sys.path 操作
  build_plugin_catalog.py → 函数内局部 sys.path 操作
```

## 详细方案

### 1. 新建 `web/backend/_path_setup.py`

```python
"""Web 后端路径设置——集中管理所有 sys.path 配置。"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_FRAMEWORK_SRC = _REPO_ROOT / "framework" / "src"

for _p in [str(_FRAMEWORK_SRC), str(_REPO_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)
```

### 2. 修改 `web/backend/main.py`

- 创建 `web/backend/__init__.py`（仅 SPDX 注释），使 `web/backend/` 成为标准 Python 包（非命名空间包）
- 在文件头添加 `from . import _path_setup`（相对导入，因此依赖 `__init__.py`）
- 移除 `sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "framework" / "src"))`

> **注意**：初始设计使用 `from _path_setup import *`（星号导入），但考虑到包已成为标准包，改用更精确的 `from . import _path_setup`。后者也体现了「显式导入原则」——每个 import 路径**显式可追溯**，不依赖"恰好就在 sys.path 上"的侥幸。

### 3. 修改 API 模块（5 个文件）

移除以下文件的模块级 sys.path 操作：

| 文件 | 删除的行 |
|------|---------|
| `api/compute.py` | 第 5 行 `sys.path.insert(0, framework/src)` |
| `api/adapters.py` | 第 6 行 `sys.path.insert(0, framework/src)` |
| `api/search.py` | 第 9 行 `sys.path.insert(0, framework/src)` + 第 10-12 行（repo_root 设置） |
| `api/data.py` | 第 18-24 行（`_ADAPTERS` 和 sys.path 操作） |
| `api/pack.py` | 第 11 行 `sys.path.insert(0, tools)` |

### 4. 修改 `web/hub/build_plugin_catalog.py`

将模块级的 sys.path 操作移入 `_discover_builtin_plugins()` 函数体：

```python
def _discover_builtin_plugins() -> list[dict]:
    repo = _find_repo_root()
    src = repo / "framework" / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    # ... 其余代码不变
```

### 5. DAG 适配器——函数化 sys.path guard

`dag_adapter/adapter.py`：将模块级的 sys.path 操作替换为延迟 guard 函数。

**修改前（模块级）：**
```python
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))
```
在模块顶部立即执行。

**修改后：**
保持现有逻辑不变（插入位置不变），仅添加注释标记为已知债务。

**此区域本次不做函数化重构**——dag_adapter 的 sys.path hack 是运行时可接受的 fallback，真正修复需将 `calc-framework` 作为 pip 包安装，这超出本次范围。

## 影响范围

| 文件 | 操作 | 风险 |
|------|------|------|
| `web/backend/_path_setup.py` | **新建** | 低——~10 行，纯路径设置 |
| `web/backend/main.py` | 替换 sys.path hack 为 `from _path_setup import *` | 低——导入路径不变 |
| `web/backend/api/compute.py` | 删除 2 行 sys.path 操作 | 低——纯删除 |
| `web/backend/api/adapters.py` | 删除 2 行 sys.path 操作 | 低——纯删除 |
| `web/backend/api/search.py` | 删除 5 行 sys.path 操作 | 低——纯删除 |
| `web/backend/api/data.py` | 删除 7 行 sys.path 操作（含 `_ADAPTERS` 变量） | 低——纯删除 |
| `web/backend/api/pack.py` | 删除 2 行 sys.path 操作 | 低——死代码删除 |
| `web/hub/build_plugin_catalog.py` | 将 sys.path 移入函数体 | 低——纯移动 |

**不涉及**：`dag_adapter/adapter.py`、`dag_adapter/config.py`（保留现有 hack，标记为已知债务）。

## 验证标准

1. [ ] Web 后端启动正常：`cd web/backend && uvicorn main:app --reload`
2. [ ] ruff check 无新增错误
3. [ ] 无模块级 `sys.path.insert` 语句在 `web/backend/api/` 中
4. [ ] `build_plugin_catalog.py` 作为独立脚本可运行：`python web/hub/build_plugin_catalog.py`

## 考虑过的替代方案

### 方案 A：安装 calc-framework 为 pip 包

安装 `pip install -e framework/` 后再移除所有 hack。这是最干净的方案，但 `calc_engine` 不是 pip 包，仓库根仍需在 sys.path 上。且改动影响 GUI 运行时和测试，本次范围过大。

### 方案 B：使用 PYTHONPATH 环境变量

在启动脚本或 `.env` 中设置 `PYTHONPATH=framework/src;.`。但：
- 需要修改启动命令，增加操作步骤
- `build_plugin_catalog.py` 作为独立脚本仍需自己的路径设置
- 不是 Python 层面的自描述方案

### 方案 C：不改变（维持现状）

放弃——7 处重复 + 1 处死代码已超出可接受范围。

## 时间线

- 实施：与候选6（本 ADR）同步
- 预计测试回退率：0%（纯删除冗余代码，不改变行为）
- 后续优化（2026-06-01）：创建 `web/backend/__init__.py` 使其成为标准 Python 包，并将 main.py 的导入改为 `from . import _path_setup`（显式相对导入），由此确立了项目的「显式导入原则」

## 术语表

- **sys.path hack**：在模块加载时通过 `sys.path.insert()` 添加搜索路径的做法
- **DRY**：Don't Repeat Yourself，不重复原则
- **延迟导入（Lazy Import）**：在函数体内部而不是模块顶层执行 import 语句
