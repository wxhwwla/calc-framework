# ADR-0018：graph_editor ↔ dag 单向依赖重构

## 状态

已采纳

## 上下文

`calc_framework.dag` 和 `calc_framework.graph_editor` 之间存在隐藏的双向依赖：

```
dag/service.py ────(lazy import)──→ graph_editor/compiler.py
                                         │
                                         └──(direct import)──→ dag/schema.py
```

`dag/service.py` 通过延迟导入函数 `_import_graph_editor()` 引用 `graph_editor.compiler.compile_graph` 和 `graph_editor.serializer.document_from_json`，以支持 `DAGService.from_graph_document()` 和 `DAGService.from_graph_file()` 两个类方法。

**设计问题**：

1. **循环依赖风险**：延迟导入是代码异味，表明模块划分边界不清晰
2. **违反单向依赖原则**：核心服务层（dag）不应依赖 UI/编辑器层（graph_editor）
3. **API 职责混淆**：DAGService 是一个求值服务，不应承担"从编辑器格式编译"的职责
4. **没有跨模块复用**：`from_graph_document`/`from_graph_file` 仅被测试代码使用，没有生产代码调用

graph_editor 依赖 dag 是合理的（编译器将可视化图转为 DAG 格式），但 dag 依赖 graph_editor 则不合理。

## 决策

消除 `dag → graph_editor` 的反向依赖，使其完全单向：

1. **删除** `dag/service.py` 中的 `_import_graph_editor()` 函数
2. **删除** `dag/service.py` 中 `DAGService.from_graph_document()` 和 `DAGService.from_graph_file()` 类方法
3. **新建** `graph_editor/dag_service_factory.py`，提供等价的工厂函数
4. **更新**测试文件，将 `DAGService.from_graph_document(...)` 替换为工厂函数调用

重构后的依赖关系：

```
dag/                          ← 完全独立，不感知 graph_editor
  └── service.py              ← 只导入 dag 内部模块

graph_editor/
  ├── compiler.py ──────→ dag/schema.py     (编译：可视化图 → DAG 格式)
  └── dag_service_factory.py → dag/service.py (工厂：编译 + 构建服务)
```

## 详细方案

### 1. 新建 `graph_editor/dag_service_factory.py`

```python
"""工厂函数 —— 从 graph_editor 格式构建 DAGService。"""

from pathlib import Path
from typing import Any

from calc_framework.dag.service import DAGService
from calc_framework.graph_editor.compiler import compile_graph
from calc_framework.graph_editor.serializer import document_from_json


def dag_service_from_graph_document(doc: Any) -> DAGService:
    """从 graph_editor 的 GraphDocument 编译并创建 DAGService。"""
    dag = compile_graph(doc)
    return DAGService(dag)


def dag_service_from_graph_file(path: str | Path) -> DAGService:
    """从 graph_editor 格式的 graph.json 文件加载并创建 DAGService。"""
    import json
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    doc = document_from_json(data)
    return dag_service_from_graph_document(doc)
```

### 2. 修改 `dag/service.py`

- 删除 `_import_graph_editor()` 函数（第 18-22 行）
- 删除 `from_graph_document` 类方法（第 53-57 行）
- 删除 `from_graph_file` 类方法（第 60-67 行）
- 不影响其他方法（`__init__`、`evaluate`、`step_debug` 等保持原样）

### 3. 更新测试文件

- `tests/dag/test_graph_file_service.py`：`DAGService.from_graph_document(...)` → `dag_service_from_graph_document(...)`
- `tests/dag/test_end_to_end.py`：同上模式

### 4. 依赖分析验证

重构后，运行以下命令验证无反向依赖：
```
grep -r "from calc_framework\.graph_editor" framework/src/calc_framework/dag/
```
应返回空。

## 影响范围

| 文件 | 操作 | 风险 |
|------|------|------|
| `framework/src/calc_framework/dag/service.py` | 删除 3 个方法/函数 | 低 —— 均为纯删除，不影响核心 API |
| `framework/src/calc_framework/graph_editor/dag_service_factory.py` | 新建 | 低 —— ~20 行，无外部 API 变化 |
| `framework/tests/dag/test_graph_file_service.py` | 替换导入路径 | 低 —— 纯替换 |
| `framework/tests/dag/test_end_to_end.py` | 替换导入路径 | 低 —— 纯替换 |

## 验证标准

1. [ ] 843 测试全部通过
2. [ ] `dag/` 中无 `from calc_framework.graph_editor` 导入
3. [ ] ruff check 无新增错误
4. [ ] `DAGService` 的 `from_file`/`from_dict`/`__init__` 保持向后兼容

## 考虑过的替代方案

### 方案 A：将 factory 放在 `dag/` 内

不可行 —— 那只是把延迟导入挪了个位置，dag 依然依赖 graph_editor。

### 方案 B：在 `calc_framework/` 层次创建独立的 `factory.py`

可行但过度设计 —— graph_editor 到 dag 的编译逻辑天然属于 graph_editor，放在 graph_editor 内更合理。

### 方案 C：不从 DAGService 中移除，保持现状

放弃 —— 延迟导入是明确的代码异味，应在发现时消除。

## 时间线

- 实施：与候选 3（本 ADR）同步
- 预计测试回退率：0%（纯移动逻辑，不改变行为）

## 术语表

- **DAGService**：dag 模块中的求值服务类，封装加载、缓存与求值
- **GraphDocument**：graph_editor 模块中的可视化图文档格式
- **compile_graph()**：将 GraphDocument 编译为 DAGGraph 的编译器函数
