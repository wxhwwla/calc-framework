# ADR-0026：多段等级曲线蓝图（CurveBlueprint）

**日期**：2026-06-15  
**状态**：已批准  
**影响范围**：`framework/src/calc_framework/inverse/curve.py`、`games/*/calc/inverse/`、JSON `成长参数` 扩展形态

---

## 1. 背景

ADR-0024 将单段定长数组的反推抽象为 `InverseSchema` + `GameInverseAdapter`。实际游戏存在多种分段模型：

| 游戏 | 段数 | 段长 |
|------|------|------|
| 终末地 | 1 | 90（属性）/ 9–12（技能） |
| 明日方舟 | 3（精0/1/2） | 随星级变化（如 6★：50/30/10） |
| 未来游戏 | N | 每段独立 |

仅用 `InverseSchema(length=N)` + 枚举 `key`（如 `elite_1_30`）会导致：

- 同长度多语义无法可靠 `fit(data)` 自动分派
- 每上新游戏复制一段组合逻辑
- JSON `成长参数` 缺少统一的「多段存储」形态

数学层（`InverseEngine` / `FormulaFitter`）已足够通用；缺的是**多段声明、拟合、物化、存储**的中间层。

---

## 2. 决策

在 `calc_framework.inverse` 新增 **曲线蓝图** 一等概念，游戏只声明 blueprint，框架执行段级 fit/compute。

### 2.1 核心类型

```python
@dataclass
class SegmentSpec:
    key: str                    # 段 ID，如 "e0" / "main" / "skill_sp"
    length: int                 # 段内等级数（1-based 索引物化）
    formula_id: str = "floor_linear"
    special_indices: list[int] | None = None   # 段内 0-based special
    search_options: dict | None = None

@dataclass
class CurveBlueprint:
    segments: list[SegmentSpec]  # 有序 N 段
```

### 2.2 引擎

`SegmentCurveEngine`（框架提供）：

| 方法 | 职责 |
|------|------|
| `fit_segment(data, spec)` | 单段反推（含 special 剥离/注入） |
| `compute_segment(params, spec)` | 单段正向（special → level_overrides） |
| `fit_by_key(data, blueprint, key)` | 按段 ID 拟合 |
| `materialize(blueprint, stored)` | 多段 params → `{key: [values...]}` |

### 2.3 JSON 存储（`成长参数` 扩展）

**多段形态**（新游戏 / AK）：

```json
{
  "segments": [
    {
      "key": "e0",
      "length": 50,
      "base": 711,
      "growth": 137,
      "divisor": 22,
      "offset": 9
    },
    {
      "key": "skill_sp",
      "length": 10,
      "base": 50,
      "growth": -202,
      "divisor": 99,
      "offset": 24,
      "special_values": [36, 34, 30]
    }
  ]
}
```

**单段形态**（终末地，向后兼容）：顶层仍可为 `{ "力量": { base, growth, ... }, ... }` 或未来可选 `{ "segments": [{ "key": "main", "length": 90, ... }] }`。

加载层规则：

- 有 `segments` 数组 → 多段物化
- 无 `segments` → 现有终末地 `curve_materialize` 逻辑

### 2.4 输入形态（per-segment，游戏层声明）

| 形态 | 说明 |
|------|------|
| `full_array` | 完整段内数组，直接 `fit_segment` |
| `endpoints` | 仅 `{start, end}` + `length`，线性展开后拟合（Wiki 里程碑） |

`endpoints` 策略由游戏 adapter 调用 `expand_segment_linear`（框架工具函数），不在 blueprint 内硬编码游戏语义。

### 2.5 与现有 API 关系

| 模块 | 变更 |
|------|------|
| `InverseSchema` / `GameInverseAdapter` | **保留**；`SegmentSpec.to_schema()` 桥接；单段游戏可继续只用 adapter |
| `InverseSchema.key` + `fit_with_key` | **保留**；多段同长时仍须按 key 分派 |
| `FloorFormulaFitter` 负 growth | **保留**（递减 SP 等） |
| `ArknightsInverseAdapter` | **迁移**为 `SegmentCurveAdapter` + `blueprint_for_rarity()` |
| `EndfieldInverseAdapter` | **迁移**为 `SegmentCurveAdapter` + `ENDFIELD_*_BLUEPRINT` |
| `inverse/materialize.py` | **新建** — `has_segment_storage`、`blueprint_from_stored`、实体物化 |
| `inverse/segment_adapter.py` | **新建** — `SegmentCurveAdapter` ABC |

---

## 3. 非目标（本 ADR 不做）

- Designer GUI / Web 反推页的多段 UI（后续）
- 通用 `compact_curve` CLI（后续；终末地 `compact_game_json` 保持独立）
- 在框架内命名「精英」「专精」等领域词 — 仅 `SegmentSpec.key` 由游戏定义

---

## 4. 新游戏接入清单

1. 定义 `CurveBlueprint`（静态或按 rarity/模板动态生成）
2. 子类化 `SegmentCurveAdapter`，实现 `iter_blueprints()`
3. 映射数据源 → 段内数组或 endpoints → `SegmentCurveEngine.fit_segment`
4. 写回 `成长参数.segments[]`；加载时 `materialize_entity_from_stored_segments()` 双读

---

## 5. 参考

- ADR-0024：单段 `GameInverseAdapter`
- ADR-0013：通用反推引擎 SPI
- `docs/操作指令集.md` §3.1.2 明日方舟分段逆推
- `CONTEXT.md`：Elite Segment / CurveBlueprint 术语
