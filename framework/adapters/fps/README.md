# FPS 武器伤害计算适配器

通用 FPS 武器伤害公式示例，涵盖距离衰减、部位倍率、护甲穿透等 FPS 特有机制。

## 伤害公式

```
部位倍率 = is_head ? head_mult : (is_limb ? 0.75 : body_mult)
基础×部位 = base_damage × 部位倍率

距离衰减:
  distance ≤ decay_start → 1.0
  distance ≥ decay_end   → min_damage_ratio
  中间 → 线性插值

护甲减伤 = armor / (armor + 100)  （穿透后有效护甲）
有效护甲 = max(armor - penetration × wall_pen_count, 0)
单发伤害 = 衰减后伤害 × (1 - 护甲减伤比)
原始 DPS = 单发伤害 × fire_rate / 60
持续 DPS = 原始 DPS × mag_size / (mag_size / fire_rate × 60 + reload_time)
```

## 变量

| 变量 | 类型 | 默认值 | 说明 |
|------|------|:------:|------|
| `weapon.base_damage` | float | 30 | 武器基础伤害 |
| `weapon.fire_rate` | float | 600 | 射速（发/分钟） |
| `weapon.mag_size` | int | 30 | 弹匣容量 |
| `weapon.reload_time` | float | 2.5 | 换弹时间（秒） |
| `weapon.decay_start` | float | 15 | 距离衰减起始（米） |
| `weapon.decay_end` | float | 50 | 距离衰减终止（米） |
| `weapon.min_damage_ratio` | float | 0.5 | 最小伤害比例 |
| `weapon.penetration` | float | 0 | 护甲穿透值 |
| `enemy.distance` | float | 20 | 目标距离（米） |
| `enemy.armor` | float | 50 | 目标护甲 |
| `enemy.head_mult` | float | 2.0 | 头部倍率 |
| `enemy.body_mult` | float | 1.0 | 躯干倍率 |
| `user_input.is_head` | bool | false | 是否击中头部 |
| `user_input.is_limb` | bool | false | 是否击中四肢 |
| `user_input.wall_pen_count` | int | 0 | 穿透墙体数 |

## 输出

| 输出 | 说明 |
|------|------|
| 单发伤害 | 经距离衰减 + 部位倍率 + 护甲减伤后的最终伤害 |
| 距离衰减系数 | 0.5–1.0 区间 |
| 部位倍率 | 0.75/1.0/2.0 取决于命中部位 |
| 护甲减伤比 | 护甲 / (护甲 + 100) |
| 原始 DPS | 不考虑换弹的连续伤害 |
| 持续 DPS(含换弹) | 含换弹时间的实战 DPS |
| 持续 DPS(含护甲) | 含换弹 + 护甲减伤的实战 DPS |

## 使用方式

### 方式一：CalcPackViewer（推荐）

```bash
python scripts/main_launcher.py
```

在启动器中选择「FPS 武器伤害计算」，或加载对应的 `.calcpack` 文件。

### 方式二：代码调用

```python
from calc_framework.config.adapter import AdapterPackage

pkg = AdapterPackage("framework/adapters/fps")

ctx = {
    "weapon": {"base_damage": 40, "fire_rate": 600, "decay_start": 20, "decay_end": 50},
    "enemy": {"distance": 25, "armor": 50, "head_mult": 2.0, "body_mult": 1.0},
    "user_input": {"is_head": True, "is_limb": False, "wall_pen_count": 0},
}
result = pkg.dag_service.evaluate(ctx)
print(result.outputs)
```

### 方式三：CalcPackViewer API

```python
from calc_framework.ui import CalcPackViewer
from calc_framework.config.adapter import AdapterPackage

pkg = AdapterPackage("framework/adapters/fps")
viewer = CalcPackViewer(pkg)
viewer.show()
```

## 文件结构

```
fps/
├── meta.json               # 适配器元信息
├── attr_schema.json        # 属性声明
├── fps.dag.json            # DAG 公式定义
├── functions.py            # 自定义函数（clamp/lerp/le/ge）
├── loader.py               # DataContextLoader 实现
├── ui/layout.json          # ComputeSheet 排版
└── README.md               # 本文件
```
