# ADR-0024：通用逆推引擎完全抽象化 — GrowthFormula 双向公式系统

**日期**：2026-06-13  
**状态**：已批准  
**影响范围**：`framework/src/calc_framework/inverse/`、`games/endfield/calc/damage/inverse/`、`games/arknights/`

---

## 1. 动机

当前逆推引擎存在三个结构性缺陷：

### 1.1 终末地层绕过框架公共 API

`games/endfield/calc/damage/inverse/fit_core.py` 直接调用 `FloorFormulaFitter._search()`（私有方法），而非通过 `InverseEngine.fit()`（公共 API）。这导致：

- 框架升级 `fit()` 的预处理/校验逻辑时，终末地拿不到改进
- 新游戏参考终末地代码时会复制这个错误模式

### 1.2 缺少游戏适配层抽象

每个新游戏接入逆推时，需要手写 `api.py` 的"按数据长度分派"逻辑。这是一个重复模式，应该抽象为框架级工具。

```
# 当前：每个游戏手写这个模式
if len(data) == 90: ...
elif len(data) == 12: ...
elif len(data) == 9: ...
else: raise ValueError
```

### 1.3 参数传递使用裸 dict

`FitResult.params` 是 `dict[str, Any]`，缺少类型安全和 IDE 补全。用户想"给 4 个数 + 等级 → 得到数据"时，需要手动构造 dict。

---

## 2. 设计目标

用户应该能以最简方式使用逆推引擎：

```python
# 反向：数据 → 参数（任何等级数，任何游戏）
params = engine.fit([100, 105, 110, 115, 120])

# 正向：参数 + 等级数 → 数据曲线
curve = engine.compute(params, num_levels=90)

# 新游戏接入：声明式配置，不写分派逻辑
adapter = GameInverseAdapter(
    formula="floor_linear",
    schemas=[InverseSchema(length=90, label="属性成长")]
)
```

---

## 3. 设计方案

### 3.1 新增 `GrowthParams` 类型化参数容器

替代裸 `dict[str, Any]`，提供类型安全和便捷方法。

```python
@dataclass
class GrowthParams:
    """Floor 线性公式的参数容器。"""
    base: float
    growth: float
    divisor: int
    offset: float = 0.0
    is_decimal: bool = False
    special_values: list[float] | None = None

    def to_dict(self) -> dict[str, Any]: ...

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> GrowthParams: ...

    def tuple(self) -> tuple[float, float, int, float]:
        """返回 (base, growth, divisor, offset)，兼容旧 API。"""
        return (self.base, self.growth, self.divisor, self.offset)
```

**影响**：`FitResult.params` 保持为 `dict`（向后兼容），但新增 `FitResult.growth_params` 属性返回 `GrowthParams`。

### 3.2 `InverseEngine` 增强 — 成为唯一入口

```python
class InverseEngine:
    # 现有方法保持兼容
    def fit(self, data, formula_id="floor_linear", *, num_levels=None, **options) -> FitResult: ...
    def compute(self, formula_id, params, num_levels) -> list[float]: ...
    def validate(self, formula_id, params, data) -> FitResult: ...
    def fit_auto(self, data, **options) -> tuple[str, FitResult] | None: ...
    def list_formula_types(self) -> list[dict]: ...

    # 新增便捷方法
    def data_to_params(self, data: Sequence[float], formula_id: str = "floor_linear") -> GrowthParams:
        """数据 → 4 参数（最简调用）。"""

    def params_to_curve(self, params: GrowthParams | dict, num_levels: int,
                        formula_id: str = "floor_linear") -> list[float]:
        """4 参数 + 等级 → 数据曲线（最简调用）。"""
```

### 3.3 新增 `InverseSchema` — 声明式数据模式

替代手写 `if/elif/elif` 分派逻辑：

```python
@dataclass
class InverseSchema:
    """描述一种数据格式与公式的映射关系。"""
    length: int                    # 数据长度（如 90）
    formula_id: str = "floor_linear"
    label: str = ""               # 人类可读标签
    special_indices: list[int] | None = None  # 特殊值索引（如技能 10-12 级 = [9,10,11]）
    search_options: dict | None = None        # 自定义搜索范围
```

### 3.4 新增 `GameInverseAdapter` ABC

新游戏接入逆推的标准接口：

```python
class GameInverseAdapter(ABC):
    """游戏适配器的逆推入口。

    每个游戏实现一个子类，声明其数据模式，框架自动处理拟合。
    """

    @property
    @abstractmethod
    def schemas(self) -> list[InverseSchema]:
        """该游戏支持的数据模式列表。"""

    @abstractmethod
    def default_formula(self) -> str:
        """默认公式类型。"""

    def fit(self, data: Sequence[float]) -> FitResult:
        """自动按长度匹配 schema 并拟合。"""
        # 框架提供默认实现：遍历 schemas，匹配长度，调用 engine.fit()

    def compute(self, params: GrowthParams | dict, num_levels: int) -> list[float]:
        """正向计算曲线。"""

    def validate(self, params: GrowthParams | dict, data: Sequence[float]) -> FitResult:
        """验证参数。"""
```

### 3.5 终末地重构

终末地层变为框架公共 API 的消费者：

```python
# games/endfield/calc/damage/inverse/adapter.py（新文件）
class EndfieldInverseAdapter(GameInverseAdapter):
    """终末地逆推适配器。"""

    @property
    def schemas(self):
        return [
            InverseSchema(length=90, label="属性成长",
                         search_options={"divisor_range": (1, 201), "growth_range": (1, 301)}),
            InverseSchema(length=12, label="技能倍率(12级)", special_indices=[9, 10, 11]),
            InverseSchema(length=9,  label="技能倍率(9级)"),
        ]

    def default_formula(self):
        return "floor_linear"
```

旧的 `api.py` / `attribute.py` / `skill.py` 保留为向后兼容的薄封装，内部委托给 `EndfieldInverseAdapter`。

---

## 4. 与现有代码的关系

| 现有模块 | 变更 |
|---------|------|
| `calc_framework/inverse/base.py` | 新增 `GrowthParams`、`FitResult.growth_params` |
| `calc_framework/inverse/engine.py` | 新增 `data_to_params()`、`params_to_curve()` |
| `calc_framework/inverse/schema.py` | **新建** — `InverseSchema`、`GameInverseAdapter` |
| `games/endfield/calc/damage/inverse/fit_core.py` | 重构：用 `InverseEngine.fit()` 替代 `_search()` |
| `games/endfield/calc/damage/inverse/api.py` | 重构：委托给 `EndfieldInverseAdapter` |
| `games/endfield/calc/damage/inverse/adapter.py` | **新建** — `EndfieldInverseAdapter` |

---

## 5. 使用示例

### 5.1 最简调用（任何游戏）

```python
from calc_framework.inverse.engine import InverseEngine

engine = InverseEngine()

# ── 反向：给数据 → 得 4 个参数 ──
data = [100, 105, 110, 115, 120, 125, 130, 135, 140]
params = engine.data_to_params(data)
print(params)  # GrowthParams(base=100, growth=5, divisor=1, offset=0)

# ── 正向：给 4 个参数 + 等级数 → 得曲线 ──
curve = engine.params_to_curve(params, num_levels=90)
print(curve[:5])  # [100.0, 105.0, 110.0, 115.0, 120.0]
```

### 5.2 新游戏接入

```python
from calc_framework.inverse.schema import GameInverseAdapter, InverseSchema

class MyGameAdapter(GameInverseAdapter):
    @property
    def schemas(self):
        return [
            InverseSchema(length=60, label="属性成长"),     # 60 级游戏
            InverseSchema(length=20, label="技能倍率"),
        ]

    def default_formula(self):
        return "floor_linear"

adapter = MyGameAdapter()

# 自动按长度匹配
result = adapter.fit([...])   # 60 个数据 → 自动走属性 schema
curve = adapter.compute(result.growth_params, num_levels=60)
```

---

## 6. 实现步骤

| 步骤 | 内容 | 影响范围 |
|:--:|------|------|
| 1 | 新建 `GrowthParams` dataclass，集成到 `FitResult` | `framework/inverse/base.py` |
| 2 | `InverseEngine` 新增 `data_to_params()` / `params_to_curve()` | `framework/inverse/engine.py` |
| 3 | 新建 `InverseSchema` + `GameInverseAdapter` ABC | `framework/inverse/schema.py`（新文件） |
| 4 | `__init__.py` 导出新符号 | `framework/inverse/__init__.py` |
| 5 | 重构 `fit_core.py`：用 `InverseEngine.fit()` 替代 `_search()` | `games/endfield/calc/damage/inverse/` |
| 6 | 新建 `EndfieldInverseAdapter` | `games/endfield/calc/damage/inverse/adapter.py` |
| 7 | 重构 `api.py`：委托给 `EndfieldInverseAdapter` | 同上 |
| 8 | 运行全量测试确认无回归 | `framework/tests/` + `games/endfield/tests/` |

---

## 7. 向后兼容

- `FitResult.params` 保持 `dict[str, Any]` 不变，新增 `growth_params` 属性
- `InverseEngine.fit()` / `compute()` / `validate()` 签名不变
- 终末地 `api.py` 的 `fit_formula()` 等公开函数签名不变，内部委托给新适配器
- `FloorFormulaFitter._search()` 保留（向后兼容），但标记为 deprecated
