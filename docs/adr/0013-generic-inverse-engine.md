# ADR-0013：通用公式反推引擎 SPI

**状态**：生效  
**日期**：2026-05-30  
**决策者**：维护者  

---

## 上下文

项目的公式反推引擎（`adapters/endfield/calc/damage/inverse/`）是为终末地专属的 floor 线性公式设计的：`value = base + floor((growth * (lv - 1) + offset) / divisor)`。

随着框架新增 card_rpg / moba / fps 三个跨品类适配器，需要将反推逻辑**从游戏专属适配器提升为框架级 SPI 服务**，使得：
1. 任何游戏适配器都能直接使用框架的反推引擎
2. 新游戏只需注册 `FormulaType` 即可获得反推能力
3. 终末地专属的反推包精简为薄适配层

---

## 决策

### SPI 架构

```
calc_framework/inverse/
├── __init__.py        # 公共导出
├── base.py            # FormulaFitter（ABC）+ FloorFormulaFitter（内置实现）
├── registry.py        # FormulaType + Registry + 全局 registry
└── engine.py          # InverseEngine 统一入口
```

### 核心接口

**`FormulaFitter`**（抽象基类）：
- `describe()` — 公式元数据（名称、参数描述、配置选项）
- `fit(data, num_levels, **options)` — 从等级数据反推参数
- `compute(params, num_levels)` — 正向计算各等级值
- `validate(params, data)` — 验证拟合质量

**`FitResult`**（dataclass）：
- `params` — 拟合参数字典
- `computed` — 正向计算值列表
- `max_error` — 最大逼近误差
- `is_exact` — 是否精确匹配

**`InverseEngine`**（统一入口）：
- `fit(data, formula_id, **options)` — 指定公式类型反推
- `fit_auto(data, **options)` — 自动选择最优公式类型
- `compute(formula_id, params, num_levels)` — 正向计算
- `validate(formula_id, params, data)` — 验证

### 内置实现

`FloorFormulaFitter` 从终末地 `fit_core.py` 提升，保留全部核心能力：
- 整数/小数双路线（×10 → int floor → ÷10）
- GCD 自动约分
- 多等价参数优选（按 growth → divisor → |offset| 字典序）
- 精确解 / 近似解双模式搜索
- 搜索范围可配置（divisor_range / growth_range / offset_search_limit）

### 终末地适配器变更

| 文件 | 变更 |
|------|------|
| `fit_core.py` | 从 298 行核心算法 → 79 行薄适配层，委托 `FloorFormulaFitter` |
| `attribute.py` / `skill.py` / `api.py` | 无变更（调用的 `_find_best_params` 签名不变） |

---

## 影响分析

| 组件 | 影响 |
|------|------|
| `adapters/endfield/calc/damage/inverse/` | `fit_core.py` 精简 73%，`_find_best_params` 委托框架 |
| `adapters/endfield/tests/.../test_inverse_refactored.py` | 12 个测试 0 回归 |
| `adapters/card_rpg/` | 可通过 `InverseEngine` 直接反推，无需自实现 |
| `framework/tests/inverse/` | 新增 26 个测试 |
| CLI/GUI 反推工具 | 无变更（底层委托框架） |

---

## 备选方案

### 不提升，保持终末地专属
反推引擎对其他游戏适配器不可见，card_rpg / moba 需各自实现反推 → 重复造轮子。

### 只提取核心算法，不做 SPI
直接在 `fit_core` 处暴露公共函数 → 缺乏公式类型扩展性，新游戏需改框架代码。

---

## 后续

- **更多 FormulaType**：指数增长公式、分段公式、带阈值公式可通过注册 `FormulaFitter` 子类扩展
- **`InverseEngine` CLI 入口**：`python -m calc_framework.inverse` 交互式反推（复用 `inverse_cli.py` 逻辑）
- **GUI 集成**：`CalcPackViewer` / 数据设计器可直接用框架反推引擎
