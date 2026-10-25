# 我的第一个游戏计算器

这是一个基于 Calc Framework 的简单计算器示例。

## 文件结构

```
my_first_calculator/
├── README.md           # 本文件
├── meta.json           # 适配器元数据
├── formula.dag.json    # DAG 计算公式
├── functions.py        # 自定义函数（可选）
├── attr_schema.json    # 属性定义
├── ui/
│   └── layout.json     # UI 布局
└── data/
    └── characters.json # 角色数据（可选）
```

## 快速开始

```bash
# 1. 测试计算器
python test_calculator.py

# 2. 运行 GUI（需要 PySide6）
python run_gui.py

# 3. 打包为 .calcpack
python build_calcpack.py
```

## 伤害公式

```
最终伤害 = max(ATK × 技能倍率 - DEF, 0) × 暴击倍率

其中：
- ATK = 角色基础攻击力
- 技能倍率 = 用户输入（默认 100%）
- DEF = 敌人防御力
- 暴击倍率 = 是否暴击 ? (1 + 暴击伤害) : 1
```

## 自定义修改

1. **修改公式**：编辑 `formula.dag.json`
2. **添加变量**：在 `variables` 中添加新变量
3. **修改 UI**：编辑 `ui/layout.json`
4. **添加数据**：在 `data/` 中添加 JSON 文件

## 变量说明

| 变量路径 | 类型 | 来源 | 默认值 | 说明 |
|---------|------|------|--------|------|
| `character.ATK` | float | character | 100 | 角色攻击力 |
| `character.crit_dmg` | float | character | 0.5 | 暴击伤害 |
| `enemy.DEF` | float | enemy | 50 | 敌人防御力 |
| `user_input.skill_mult` | float | user_input | 1.0 | 技能倍率 |
| `user_input.is_crit` | bool | user_input | false | 是否暴击 |
