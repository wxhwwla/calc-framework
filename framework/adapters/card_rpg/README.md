# 卡牌RPG 伤害计算适配器

经典回合制卡牌 RPG 伤害公式示例，用于演示框架的多品类适配能力。

## 伤害公式

```
总攻击力 = 角色ATK + 武器ATK_bonus
基础伤害 = max(总攻击力 × skill_mult - 敌方DEF × 0.5, 0)
暴击倍率 = 暴击 ? (1 + crit_dmg) : 1
最终伤害 = 基础伤害 × 暴击倍率
```

## 变量

| 变量 | 类型 | 来源 | 说明 |
|------|------|------|------|
| `character.ATK` | float | character | 角色攻击力 |
| `character.DEF` | float | character | 角色防御力 |
| `character.crit_rate` | float (0.05) | character | 暴击率 |
| `character.crit_dmg` | float (0.5) | character | 暴击伤害 |
| `weapon.ATK_bonus` | float (0) | weapon | 武器攻击力加成 |
| `enemy.DEF` | float (50) | enemy | 敌方防御力 |
| `user_input.skill_mult` | float (1.0) | user_input | 技能倍率 |
| `user_input.is_crit` | bool (false) | user_input | 是否暴击 |

## 输出

| 输出 | 说明 |
|------|------|
| 总攻击力 | ATK + ATK_bonus |
| 基础伤害 | 减伤后伤害（不低于 0） |
| 暴击倍率 | 1.0（未暴击）或 1+crit_dmg |
| 最终伤害 | 基础伤害 × 暴击倍率 |

## 使用方式

### 方式一：CalcPackViewer（推荐）

```bash
python scripts/main_launcher.py
```

在启动器中选择「卡牌RPG伤害计算」，或加载对应的 `.calcpack` 文件。

### 方式二：代码调用

```python
from calc_framework.config.adapter import AdapterPackage

pkg = AdapterPackage("framework/adapters/card_rpg")

ctx = {
    "character": {"ATK": 100, "DEF": 50, "crit_rate": 0.05, "crit_dmg": 0.5},
    "weapon": {"ATK_bonus": 15},
    "enemy": {"DEF": 60},
    "user_input": {"skill_mult": 1.0, "is_crit": True},
}
result = pkg.dag_service.evaluate(ctx)
print(result.outputs)
# 预期: 总攻击力=115.0, 基础伤害=85.0, 暴击倍率=1.5, 最终伤害=127.5
```

### 方式三：CalcPackViewer API

```python
from calc_framework.ui import CalcPackViewer
from calc_framework.config.adapter import AdapterPackage

pkg = AdapterPackage("framework/adapters/card_rpg")
viewer = CalcPackViewer(pkg)
viewer.show()
```

## 文件结构

```
card_rpg/
├── meta.json               # 适配器元信息
├── attr_schema.json        # 属性声明
├── card_rpg.dag.json       # DAG 公式定义
├── functions.py            # 自定义函数（clamp）
├── loader.py               # DataContextLoader 实现
├── ui/layout.json          # ComputeSheet 排版
└── README.md               # 本文件
```
