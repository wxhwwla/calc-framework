# 明日方舟：终末地 伤害计算器项目文档

## 项目概述

本项目是一个用于计算《明日方舟：终末地》游戏中角色和武器属性成长的计算器工具。它提供了从属性数据反推成长公式参数的功能，以及根据成长参数生成完整属性曲线的能力。

---

## 项目结构

```
endfield_damage_calculator/
├── calculation/           # 计算引擎模块
│   ├── formula.py        # 通用计算公式
│   ├── inverse.py        # 反向推导算法
│   ├── config.py         # 集中属性配置
│   ├── data_generator.py # 统一数据生成器
│   └── multiplicative_zones/  # 乘法区计算
├── character_weapon_equipment/  # 角色与武器数据
│   ├── character_data/   # 角色数据管理
│   └── weapon_data/      # 武器数据管理
├── data/                 # 数据加载器
├── gui_design/           # 图形用户界面
├── scripts/              # 命令行脚本
├── tests/                # 单元测试
├── utils/                # 工具函数
├── main.py               # 主入口
├── build.py              # 打包脚本
├── pyproject.toml        # 项目配置
└── README.md             # 项目说明
```

---

## 核心功能模块

### 1. 计算引擎 (calculation/)

#### 1.1 公式计算 (formula.py)

**主要函数：**

| 函数名 | 功能描述 | 参数 | 返回值 |
|--------|----------|------|--------|
| `calculate_growth_curve` | 计算属性成长曲线 | base, growth, divisor, offset, max_level | List[float] (90个值) |
| `calculate_skill_curve` | 计算技能倍率曲线 | base, growth, divisor, offset, special_values | List[float] (12个值) |
| `calculate_bonus_attribute` | 计算附加属性曲线 | base, growth, divisor, offset, special, max_level | List[float] |

**公式说明：**
```
基础公式: round(base + floor((growth * (lv - 1) + offset) / divisor), 1)
```

#### 1.2 反向推导 (inverse.py)

**主要函数：**

| 函数名 | 功能描述 |
|--------|----------|
| `fit_attribute_formula` | 根据90级属性数据反推成长参数 |
| `fit_skill_formula` | 根据12级技能倍率数据反推参数 |
| `fit_skill_formula_no_special` | 根据9级技能数据反推参数 |
| `fit_formula` | 自动检测数据类型并拟合 |
| `validate_attribute_formula` | 验证属性公式正确性 |
| `validate_skill_formula` | 验证技能公式正确性 |

#### 1.3 集中配置 (config.py)

**主要功能：**

| 功能 | 说明 |
|------|------|
| 属性名称常量 | 角色普通属性、技能属性、武器属性列表 |
| 默认成长参数 | 提供默认值配置 |
| 属性分类判断 | 判断属性属于哪种类别 |
| 参数验证 | 验证成长参数合法性 |

**主要函数：**

| 函数名 | 功能描述 |
|--------|----------|
| `get_default_growth_params` | 获取默认成长参数 |
| `is_character_attribute` | 判断是否为角色属性 |
| `is_skill_attribute` | 判断是否为技能属性 |
| `is_weapon_attribute` | 判断是否为武器属性 |
| `get_attribute_category` | 获取属性分类 |
| `validate_growth_params` | 验证成长参数 |

#### 1.4 统一数据生成器 (data_generator.py)

**主要函数：**

| 函数名 | 功能描述 |
|--------|----------|
| `generate_attributes` | 统一属性生成接口 |
| `generate_character_attributes` | 生成角色所有属性 |
| `generate_weapon_attributes` | 生成武器所有属性 |

#### 1.5 乘法区计算 (multiplicative_zones/)

包含伤害计算中各乘法区的计算逻辑：
- `ability_bonus_zone.py` - 技能加成区
- `attribute_zone.py` - 属性区
- `base_zone.py` - 基础区
- `defense_zone.py` - 防御区
- `final_attack_zone.py` - 最终攻击区
- `zone_manager.py` - 区域管理器

---

### 2. 角色与武器数据 (character_weapon_equipment/)

#### 2.1 角色数据 (character_data/)

**文件结构：**
- `formula.py` - 角色属性生成器
- `character_data.py` - 角色数据加载与处理
- `add_character.py` - 角色添加工具
- `characters.json` - 角色数据存储

**主要函数：**

| 函数名 | 功能描述 |
|--------|----------|
| `generate_character_attributes` | 根据成长参数生成角色所有属性 |
| `load_characters_from_json` | 从JSON文件加载角色数据 |

**成长参数格式：**
```python
{
    "力量": {"base": 100, "growth": 50, "divisor": 10, "offset": 0},
    "敏捷": {"base": 80, "growth": 40, "divisor": 10, "offset": 0},
    "战技倍率": [
        {"base": 100, "growth": 20, "divisor": 10, "special": [150, 160, 170]}
    ]
}
```

#### 2.2 武器数据 (weapon_data/)

**文件结构：**
- `formula.py` - 武器属性生成器
- `weapon_data.py` - 武器数据加载与处理
- `add_weapon.py` - 武器添加工具
- `weapons.json` - 武器数据存储

**主要函数：**

| 函数名 | 功能描述 |
|--------|----------|
| `generate_weapon_attributes` | 根据成长参数生成武器属性 |
| `load_weapons_from_json` | 从JSON文件加载武器数据 |

---

### 3. 数据加载器 (data/loader.py)

**主要函数：**

| 函数名 | 功能描述 |
|--------|----------|
| `get_characters` | 获取所有角色数据列表 |
| `get_weapons` | 获取所有武器数据列表 |
| `load_json_file` | 加载JSON文件 |
| `check_and_save_characters` | 检查并保存角色数据 |
| `process_input_data` | 处理输入数据，返回缩放后的值和数据类型元数据 |
| `restore_data` | 还原处理后的数据，确保双向一致性 |

---

### 4. 图形界面 (gui_design/)

提供可视化界面功能：
- `gui.py` - 主界面
- `selection_panel.py` - 角色/武器选择面板
- `property_display.py` - 属性展示组件
- `gui_settings.py` - 界面设置

---

### 5. 命令行工具 (scripts/)

#### 5.1 反向计算 CLI (inverse_cli.py)

**功能：** 交互式公式参数计算器

**使用方法：**
```bash
cd endfield_damage_calculator
python scripts/inverse_cli.py
```

**支持的数据格式：**
- 属性数据：90或94个数值（等级1-90）
- 技能倍率：9或12个数值（等级1-9或1-12）
- 支持百分比格式：如 "8.9%" 或 "89"

---

## 使用指南

### 方法一：使用 CLI 工具反推公式参数

```bash
# 进入项目目录
cd endfield_damage_calculator

# 运行 CLI 工具
python scripts/inverse_cli.py
```

**操作流程：**
1. 选择数据类型（属性数据或技能倍率）
2. 输入数据（空格分隔）
3. 工具自动计算并输出公式参数

### 方法二：编程方式使用

```python
from calculation.formula import calculate_growth_curve
from calculation.inverse import fit_attribute_formula

# 生成属性成长曲线
curve = calculate_growth_curve(
    base=100,
    growth=50,
    divisor=10,
    offset=0
)
# 返回: [100.0, 105.0, 110.0, ...] (90个值)

# 反向推导公式参数
data = [100, 105, 110, ...]  # 90个数据
base, growth, divisor, offset = fit_attribute_formula(data)
```

### 方法三：使用 GUI（待完善）

```bash
cd endfield_damage_calculator
python main.py
```

---

## 数据格式规范

### 属性数据格式

**输入数据：** 90个数值（等级1-90）或94个数值（包含重复数据）

**输出参数：**
```python
{
    "力量": {"base": int/float, "growth": int/float, "divisor": int, "offset": int},
    "敏捷": {"base": int/float, "growth": int/float, "divisor": int, "offset": int},
    "智识": {"base": int/float, "growth": int/float, "divisor": int, "offset": int},
    "意志": {"base": int/float, "growth": int/float, "divisor": int, "offset": int},
    "基础攻击力": {"base": int/float, "growth": int/float, "divisor": int, "offset": int}
}
```

### 技能倍率格式

**输入数据：** 9个数值（等级1-9）或12个数值（等级1-12）

**输出参数：**
```python
{
    "战技倍率": [
        {"base": int/float, "growth": int/float, "divisor": int, "offset": int, "special": [lv10, lv11, lv12]}
    ],
    "连携技倍率": [...],
    "终结技倍率": [...]
}
```

---

## 测试运行

```bash
# 运行所有测试
cd endfield_damage_calculator
python -m pytest tests/ -v

# 运行特定测试
python -m pytest tests/test_calculation.py -v
python -m pytest tests/test_data_generators.py -v
```

**测试覆盖：**
- 公式计算测试（整数/小数参数）
- 反向推导测试
- 数据生成器测试
- 数据加载器测试
- 小数数据处理测试
- 统一数据生成器测试

---

## 环境要求

- Python 3.8+
- 依赖库：通过 pyproject.toml 管理
- 虚拟环境：建议使用 `.venv`

**安装依赖：**
```bash
cd endfield_damage_calculator
pip install -e .
```

---

## 配置说明

### 环境变量

| 变量名 | 作用 | 默认值 |
|--------|------|--------|
| `GIT_USERNAME` | GitHub 用户名（用于上传脚本） | wxhwwla |

### 文件配置

| 文件 | 说明 |
|------|------|
| `git_key.txt` | GitHub Token（用于上传脚本） | 需手动创建 |
| `characters.json` | 角色数据存储 | 自动维护 |
| `weapons.json` | 武器数据存储 | 自动维护 |

---

## 常见问题

### Q1: 输入数据后提示"数据长度错误"

**原因：** 属性数据需要90或94个值，技能数据需要9或12个值

**解决：** 检查输入的数据数量是否正确

### Q2: 反推结果与预期不符

**原因：** 数据格式不正确或存在特殊值

**解决：**
- 确保数据为等级1到等级90（或9/12）的顺序
- 检查是否有重复数据需要处理
- 使用 `remove_duplicates` 函数处理94个数据的情况

### Q3: 导入模块失败

**原因：** Python路径未正确配置

**解决：**
```bash
cd endfield_damage_calculator
python -c "import sys; sys.path.insert(0, '.'); from calculation.formula import calculate_growth_curve"
```

---

## 更新日志

### 当前版本

- 支持小数参数的属性计算
- 修复类型检查错误
- 完善单元测试覆盖
- 优化模块导入结构

---

## 开发指南

### 添加新角色

1. 使用 `add_character.py` 脚本添加
2. 或直接编辑 `characters.json`
3. 确保成长参数格式正确

### 添加新武器

1. 使用 `add_weapon.py` 脚本添加
2. 或直接编辑 `weapons.json`

### 扩展功能

1. 在 `calculation/` 目录添加新公式
2. 在 `tests/` 目录添加对应测试
3. 更新文档

---

## 许可证

本项目仅供学习和研究使用。

---

**文档版本**: v1.0  
**生成日期**: 2026年5月  
**项目地址**: https://github.com/wxhwwla/endfield_damage_calculator_2.0