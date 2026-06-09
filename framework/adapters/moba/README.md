# MOBA 英雄伤害计算适配器

通用 MOBA 游戏伤害公式示例，涵盖 AD/AP 加成、护甲/魔抗减伤、暴击、冷却缩减等 MOBA 特有机制。

## 伤害公式

```
技能基础+AD = skill_base_damage + ad_ratio × attack_damage
技能总基础 = 技能基础+AD + ap_ratio × ability_power

暴击后伤害 = is_crit ? 技能总基础 × crit_dmg : 技能总基础

物理减伤比 = (enemy_armor - lethality) × (1 - armor_pen_pct)
            / [(enemy_armor - lethality) × (1 - armor_pen_pct) + 100]
魔法减伤比 = (enemy_mr - magic_pen) × (1 - magic_pen_pct)
            / [(enemy_mr - magic_pen) × (1 - magic_pen_pct) + 100]

实际冷却 = skill_cooldown × (1 - cooldown_reduction)
技能总伤害 = is_physical ? 暴击后伤害 × (1 - 物理减伤比)
                        : 暴击后伤害 × (1 - 魔法减伤比)
```

## 变量

| 变量 | 类型 | 默认值 | 说明 |
|------|------|:------:|------|
| `character.attack_damage` | float | 60 | 攻击力 (AD) |
| `character.ability_power` | float | 0 | 法术强度 (AP) |
| `character.armor` | float | 30 | 护甲 |
| `character.magic_resist` | float | 30 | 魔法抗性 |
| `character.crit_rate` | float | 0 | 暴击率 |
| `character.crit_dmg` | float | 1.75 | 暴击伤害 |
| `character.lethality` | float | 0 | 穿甲（固定） |
| `character.armor_pen_pct` | float | 0 | 百分比护甲穿透 |
| `character.magic_pen` | float | 0 | 固定法穿 |
| `character.magic_pen_pct` | float | 0 | 百分比法穿 |
| `character.cooldown_reduction` | float | 0 | 冷却缩减 |
| `enemy.armor` | float | 50 | 敌方护甲 |
| `enemy.magic_resist` | float | 30 | 敌方魔抗 |
| `user_input.skill_base_damage` | float | 100 | 技能基础伤害 |
| `user_input.ad_ratio` | float | 0 | AD 加成系数 |
| `user_input.ap_ratio` | float | 0 | AP 加成系数 |
| `user_input.is_physical` | bool | true | 是否为物理伤害 |
| `user_input.is_crit` | bool | false | 是否暴击 |
| `user_input.skill_cooldown` | float | 10 | 技能冷却时间 |

## 输出

| 输出 | 说明 |
|------|------|
| 攻击间隔(秒) | 基于攻速加成的基础攻击间隔 |
| 技能总伤害 | 经减伤后的最终伤害 |
| 基础伤害 | AD+AP 加成后的原始伤害 |
| 暴击后伤害 | 暴击翻倍后的伤害 |
| 实际冷却(秒) | 冷却缩减后的实际 CD |
| 物理减伤比 | 0–1 区间 |
| 魔法减伤比 | 0–1 区间 |

## 使用方式

### 方式一：CalcPackViewer（推荐）

```bash
python scripts/main_launcher.py
```

在启动器中选择「MOBA 英雄伤害计算」，或加载对应的 `.calcpack` 文件。

### 方式二：代码调用

```python
from calc_framework.config.adapter import AdapterPackage

pkg = AdapterPackage("framework/adapters/moba")

ctx = {
    "character": {"attack_damage": 80, "ability_power": 0, "crit_dmg": 1.75, "lethality": 10},
    "enemy": {"armor": 50, "magic_resist": 30},
    "user_input": {"skill_base_damage": 150, "ad_ratio": 1.0, "is_physical": True, "is_crit": True},
}
result = pkg.dag_service.evaluate(ctx)
print(result.outputs)
```

### 方式三：CalcPackViewer API

```python
from calc_framework.ui import CalcPackViewer
from calc_framework.config.adapter import AdapterPackage

pkg = AdapterPackage("framework/adapters/moba")
viewer = CalcPackViewer(pkg)
viewer.show()
```

## 文件结构

```
moba/
├── meta.json               # 适配器元信息
├── attr_schema.json        # 属性声明
├── moba.dag.json           # DAG 公式定义
├── functions.py            # 自定义函数（percent_of/armor_mult）
├── loader.py               # DataContextLoader 实现
├── ui/layout.json          # ComputeSheet 排版
└── README.md               # 本文件
```
