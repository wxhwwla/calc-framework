# ADR-0020: multiplicative_zones 循环依赖解耦

## 状态

已采纳

## 上下文

`calc_engine/endfield/calc/multiplicative_zones/` 包包含两类职责不同的代码：

1. **旧引擎乘区计算**：`ability_bonus_calc.py`、`ability_bonus_details.py`、`attribute_zone.py`、`final_attack_zone.py`、`base_zone.py`、`zone_manager.py` 等——纯游戏逻辑，无框架依赖。
2. **DAG 桥接层**：`dag/adapter.py`、`dag/loader.py`、`dag/config.py`、`dag/_subgraph_builders.py`——将旧引擎的计算委托给 `calc_framework` 的 DAG 引擎。
3. **生产入口**：`zone_snapshot.py`——暴露 `ZoneDisplayLine`、`WeaponBonusSelection`、`MultiplicativeZoneSelection` 类型及 `compute_multiplicative_zone_snapshot()` 函数，内部委托 `dag/adapter`。

这三类代码被塞在同一个包中，导致以下问题：

### 包级循环依赖

```
multiplicative_zones/__init__.py
  → zone_snapshot.py             (运行时导出 ZoneDisplayLine)
    → dag/adapter.py             (lazy 导入 compute_snapshot_with_dag)
      → multiplicative_zones     (from … import ZoneDisplayLine)
        → __init__.py
          → zone_snapshot.py     ← 循环！
```

当前依赖 `zone_snapshot.py` 内部使用 `lazy import` 回避了运行时崩溃，但**设计上的循环**仍然存在——`dag/` 子包作为桥接层嵌在它理应替代的旧引擎内部，导致：
- 模块边界模糊，新开发者难以理解包职责
- 无法在 `dag/` 中做静态分析或类型检查而不引入循环
- 违反"依赖方向应指向稳定层"的原则

### sys.path hack

`dag/adapter.py` 和 `dag/config.py` 在模块加载时修改 `sys.path` 以导入 `calc_framework`。这是因为它们作为 `calc_engine` 的子包，需要跨包访问框架。将此子包移出后可考虑后期用更标准的方式解决。

## 决策

将 `multiplicative_zones/` 拆分为三个独立的包，消除循环依赖：

```
calc_engine/endfield/calc/
├── multiplicative_zones/     ← 纯旧引擎，不再感知 DAG
│   ├── __init__.py
│   ├── ability_bonus_calc.py
│   ├── ability_bonus_details.py
│   ├── attribute_zone.py
│   ├── _attribute_zone_bonus.py
│   ├── base_zone.py
│   ├── final_attack_zone.py
│   └── zone_manager.py
├── zone_snapshot/            ← 新建：生产入口 + 展示类型
│   ├── __init__.py
│   ├── types.py              ← ZoneDisplayLine, WeaponBonusSelection, MultiplicativeZoneSelection
│   └── compute.py            ← compute_multiplicative_zone_snapshot()
└── dag_adapter/              ← 新建：DAG 桥接层
    ├── __init__.py
    ├── adapter.py
    ├── loader.py
    ├── config.py
    ├── _subgraph_builders.py
    └── __main__.py
```

### 依赖方向

```
multiplicative_zones (纯旧引擎，零外部依赖)
    ↑
dag_adapter/loader.py (委托旧引擎做预处理)
    ↑
dag_adapter/adapter.py (组装 DAG 计算 → 返回 ZoneDisplayLine[])
    ↑
zone_snapshot/compute.py (生产入口，委托 dag_adapter)
    ↑
GUI / 测试代码
```

**不再有任何循环。**

## 具体变更

### 新建文件

| 文件 | 来源 |
|------|------|
| `zone_snapshot/__init__.py` | 新建，重导出 types + compute |
| `zone_snapshot/types.py` | 从 `zone_snapshot.py` 提取 DataClass |
| `zone_snapshot/compute.py` | 从 `zone_snapshot.py` 提取 `compute_multiplicative_zone_snapshot()` |
| `dag_adapter/__init__.py` | 从 `dag/__init__.py` 迁移，更新导入路径 |
| `dag_adapter/adapter.py` | 从 `dag/adapter.py` 迁移，更新导入路径 |
| `dag_adapter/loader.py` | 从 `dag/loader.py` 迁移，更新导入路径 |
| `dag_adapter/config.py` | 从 `dag/config.py` 迁移，无导入路径变更 |
| `dag_adapter/_subgraph_builders.py` | 从 `dag/_subgraph_builders.py` 迁移，无导入路径变更 |
| `dag_adapter/__main__.py` | 从 `dag/__main__.py` 迁移，更新导入路径 |

### 删除文件

| 文件 | 原因 |
|------|------|
| `multiplicative_zones/dag/` (整个目录) | 已迁移到 `dag_adapter/` |
| `multiplicative_zones/zone_snapshot.py` | 已拆分为 `zone_snapshot/` 包 |

### 修改文件

| 文件 | 变更 |
|------|------|
| `multiplicative_zones/__init__.py` | 移除 zone_snapshot 相关的 4 个导出 |
| `qt_columns.py` | 导入路径 `multiplicative_zones.zone_snapshot` → `zone_snapshot` |
| `test_zone_snapshot.py` | 同上 |
| `test_dag_adapter.py` | 同上 + `dag.adapter` → `dag_adapter.adapter` |
| `test_endfield_dag_integration.py` | `dag.config` → `dag_adapter.config`，`dag.loader` → `dag_adapter.loader` |

## 理由

1. **消除循环依赖**：三个包形成单向依赖链，再无包级循环。
2. **职责分离**：旧引擎计算、DAG 桥接、生产入口各归其位。
3. **不破坏公共 API**：`calc/__init__.py` 只导出旧引擎类型，不受影响。`ZoneDisplayLine` 等展示类型的新路径是 `zone_snapshot` 而非 `multiplicative_zones`，这是合理的归属。
4. **最小扩散**：仅有 3 个外部文件（1 个 GUI + 2 个测试）需要修改导入路径。

## 后果

- 所有 `from calc_engine.endfield.calc.multiplicative_zones.dag import` 的调用方需要更新。
- 所有 `from calc_engine.endfield.calc.multiplicative_zones.zone_snapshot import` 的调用方需要更新。
- `multiplicative_zones.__init__` 不再暴露 `ZoneDisplayLine`、`WeaponBonusSelection`、`MultiplicativeZoneSelection`、`compute_multiplicative_zone_snapshot`。
- `sys.path hack` 暂时保留（`dag/adapter.py` 和 `dag/config.py`）——移出 `multiplicative_zones` 后，可独立解决（候选6）。
