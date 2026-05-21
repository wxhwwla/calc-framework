# 终末地伤害计算小工具

> 基于 CustomTkinter 开发的《明日方舟：终末地》伤害计算辅助工具  
> **操作指令速查**：仓库根目录 [`docs/操作指令集.md`](../docs/操作指令集.md)

## 🌟 项目简介

本工具旨在帮助玩家计算角色和武器的属性成长、伤害乘区等数据，优化配装和战斗策略。

### 🎯 功能特性

| 功能模块 | 说明 |
|---------|------|
| 角色选择 | 支持按类型、星级筛选角色 |
| 武器选择 | 支持按类型、星级筛选武器，包含特殊能力等级选择 |
| 属性展示 | **角色属性列**与**武器属性列**分列显示等级曲线明细（选择区仅负责操作，不重复摘要） |
| 乘区计算 | 点击「确认选择」后，在角色与武器均有效时刷新右侧乘区（能力、攻击力等） |
| 公式反推 | 支持从数值数据反推成长公式参数 |
| 数据管理 | 支持添加新角色和武器数据 |

---

## 📁 项目结构

```
endfield_damage_calculator/
├── main.py                    # 项目入口，启动应用
├── pyproject.toml             # 打包配置文件
├── please_read_me.py          # 项目说明文档
├── build.py                   # 打包脚本
├── calculation/               # 计算逻辑模块
│   ├── __init__.py
│   ├── config.py              # 集中属性配置
│   ├── data_generator.py      # 统一数据生成器
│   ├── formula.py             # 正向计算公式
│   ├── inverse.py             # 反向拟合算法
│   └── multiplicative_zones/  # 乘区计算子模块
│       ├── base_zone.py       # 乘区基类
│       ├── attribute_zone.py  # 能力乘区
│       ├── defense_zone.py    # 防御减伤区
│       ├── ability_bonus_zone.py  # 能力值加成区
│       ├── final_attack_zone.py   # 最终攻击力区
│       └── zone_manager.py    # 乘区管理器
├── character_weapon_equipment/# 数据文件目录
│   ├── character_data/        # 角色数据
│   │   ├── characters.json    # 角色JSON数据
│   │   ├── character_data.py  # 角色数据管理
│   │   ├── add_character.py   # 添加角色脚本
│   │   └── formula.py         # 角色公式（保留兼容）
│   └── weapon_data/           # 武器数据
│       ├── weapons.json       # 武器JSON数据
│       ├── weapon_data.py     # 武器数据管理
│       ├── add_weapon.py      # 添加武器脚本
│       └── formula.py         # 武器公式（保留兼容）
├── data/                      # 统一数据加载层
│   └── loader.py              # 数据统一加载与缓存
├── gui_design/                # GUI界面模块
│   ├── gui.py                 # 主应用类
│   ├── gui_tools.py           # GUI工具组件
│   ├── gui_settings.py        # GUI设置初始化
│   ├── selection_panel.py     # 选择面板
│   ├── selection_components.py # 选择组件
│   └── property_display.py    # 确认后分列展示角色/武器属性与乘区
├── scripts/                   # 辅助脚本（非 pytest）
│   ├── inverse_cli.py         # 反推公式 CLI
│   ├── inverse_formula_gui.py # 反推公式 GUI（维护用）
│   └── seed_weapons.py        # 武器录入示例
├── tests/                     # pytest 单元测试
│   ├── test_calculation.py
│   ├── test_game_data_contract.py
│   └── ...
└── utils/                     # 工具函数
    └── path_utils.py          # 路径处理工具
```

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- CustomTkinter 5.2.2+

### 版本号

- `_VERSION`：日常由上传脚本在有业务改动并 push 成功时自动递增（见下方「GitHub 上传」）；`pyproject.toml` 通过 dynamic 读取。
- `_EXE_VERSION`：仅重新打包 exe 前在 `please_read_me.py` **手动**修改。
- 完整流程说明：同文件中的 `UPLOAD_WORKFLOW` 常量，或 `python please_read_me.py` 打印帮助。

### GitHub 上传（仓库根目录）

```bash
python github_upload_module.py              # 默认 patch：1.8.1 → 1.8.2
python github_upload_module.py --minor        # 大改动：1.8.1 → 1.9.0
python github_upload_module.py --no-bump    # 提交推送但不改 _VERSION
```

上传前脚本会根据改动在 `please_read_me.py` **底部**生成临时总结块，commit 消息读取该块（`v版本: 标题` + 列表）；**push 成功后**自动删除总结块。失败则保留总结便于重试。

### 安装依赖

```bash
cd endfield_damage_calculator
pip install -e ".[dev]"
```

（`[dev]` 含 pytest，用于运行测试；仅使用 GUI 时可 `pip install -e .`。）

### 运行测试

```bash
cd endfield_damage_calculator
python -m pytest tests/ -q
```

### 运行项目

```bash
python main.py
```

### 打包发布

```bash
pip install setuptools wheel pyinstaller
python build.py
```

打包产物为 `dist/终末地伤害计算器.exe`（已加入 `.gitignore`，请勿提交到 Git）。

### 数据加载约定

| 场景 | 入口 |
|------|------|
| GUI / 乘区计算 / pytest | `data.loader.get_characters()`、`get_weapons()` |
| 录入新角色/武器 | `scripts/seed_characters.py`、`scripts/seed_weapons.py` 或库函数 `add_character` / `add_weapon` |
| JSON 内容 | 须含完整等级曲线；`process_*` 仅用于录入时补全缺省字段 |

加载失败时 GUI 会弹窗提示；开发模式下 `strict=True` 会抛出 `DataLoadError`。

---

## 📖 使用指南

### 基本操作流程

1. **选择角色**：在第 0 列选择角色类型、星级、名称与等级（含信赖、战技等级）
2. **选择武器**：在第 1 列选择武器并调整第一～三技能与特殊能力滑块
3. **调整等级**：在两侧选择区完成上述设置（改滑块后需再次确认才会刷新属性列）
4. **查看结果**：点击武器列下方「确认选择」——刷新角色/武器属性列；两侧数据均有效时再更新右侧乘区

### GUI 布局

主窗口为 **8 列** grid（偶数列为间隙），内容区从左到右：

| 列 | 内容 | 宽度策略 |
|----|------|----------|
| 0 | 角色选择 | 最小宽度（`weight=0`） |
| 1 | 武器选择 + 确认按钮 | 最小宽度 |
| 3 | **角色属性**（力量、敏捷、智识、意志、基础攻击力等） | 最小宽度 |
| 5 | **武器属性**（基础攻击、各条 `xxx+`、特殊能力数值） | 最小宽度 |
| 7 | **右侧乘区** | 占满剩余宽度（`weight=1`） |

- 启动完成后会自动确认一次，用默认角色/武器填充属性列与乘区。
- 角色或武器无效时，仅对应属性列显示提示，且不刷新乘区。
- 武器属性列数值规则：**第一技能**对应条目为 JSON 整数；**其余** `xxx+` 与特殊能力字段按百分数显示（如 `27.6%`）。

术语与列号说明见仓库根目录 [`CONTEXT.md`](../CONTEXT.md)。

### 公式反推工具

1. 运行反推 GUI（需先 `pip install -e .`）：
```bash
python scripts/inverse_formula_gui.py
```

2. 输入数据格式：
   - 支持整数和小数数据
   - 支持百分比格式（如 "8.9%"）
   - 90个数据点 → 属性成长
   - 9/12个数据点 → 技能倍率

---

## 🧮 核心算法

### 成长公式

所有属性和技能倍率使用统一的 floor 公式：

```
value(lv) = base + floor((growth * (lv - 1) + offset) / divisor)
```

### 小数数据处理

对于小数数据（如百分比加成），采用"乘10→整数计算→除10"策略：

```python
# 小数数据检测
is_decimal = any(isinstance(x, float) and x != int(x) for x in data)
scale_factor = 10 if is_decimal else 1

# 计算过程
scaled_base = base * scale_factor
calculated = scaled_base + math.floor((growth * (lv - 1) + offset) / divisor)
result = calculated / scale_factor
```

### 伤害计算公式

```
最终攻击力 = 中间攻击力 × (能力值加成 + 1)
中间攻击力 = 攻击加成攻击力 + 附加攻击力
攻击加成攻击力 = 基础攻击力 × 攻击力+乘区
能力值加成 = 主能力×0.005 + 副能力×0.002
```

---

## 🔧 API 文档

### 计算模块

#### `calculation/formula.py`

| 函数名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `calculate_skill_curve` | `base, growth, divisor, offset, special=None, max_level=12` | `List[float]` | 计算技能倍率曲线 |
| `calculate_bonus_attribute` | `base, growth, divisor, offset, special=None, max_level=9` | `List[float]` | 计算属性加成曲线 |
| `calculate_growth_curve` | `base, growth, divisor, offset` | `List[int]` | 计算属性成长曲线（90级） |

#### `calculation/inverse.py`

| 函数名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `fit_attribute_formula` | `data: List[int\|float]` | `Tuple[base, growth, divisor, offset]` | 拟合属性成长公式 |
| `fit_skill_formula` | `data: List[int\|float]` | `Tuple[base, growth, divisor, offset, special]` | 拟合技能倍率公式（12级） |
| `fit_skill_formula_no_special` | `data: List[int\|float]` | `Tuple[base, growth, divisor, offset, special]` | 拟合技能倍率公式（9级） |
| `fit_formula` | `data: List[int\|float]` | `Tuple` | 自动检测并拟合公式 |

---

## 🧪 测试说明

### 测试覆盖

| 测试文件 | 覆盖内容 |
|----------|----------|
| `test_calculation.py` | 基础计算功能测试 |
| `test_config.py` | 配置模块测试 |
| `test_data_generators.py` | 数据生成器测试 |
| `test_decimal_scaling.py` | 小数数据处理测试 |
| `test_inverse_refactored.py` | 反推算法重构测试 |
| `test_unified_data_generator.py` | 统一数据生成器测试 |
| `test_gui_layout_contract.py` | 主界面 8 列布局权重契约 |
| `test_property_display_lines.py` | 角色/武器属性列明细文本 |
| `test_confirm_selection_state.py` | 确认选择后的分列提示与乘区联动 |
| `test_weapon_property_display.py` | 武器属性数值格式（整数 / 百分数） |
| `test_weapon_panel_layout.py` | 武器技能标题与 bonus 顺序 |

### 运行测试

```bash
python -m pytest tests/ -v
```

---

## 📦 数据格式

### 角色数据 (characters.json)

```json
{
  "角色ID": {
    "name": "角色名称",
    "type": "角色类型",
    "star": 5,
    "attributes": {
      "攻击力": {"base": 100, "growth": 10, "divisor": 1, "offset": 0},
      "生命值": {"base": 1000, "growth": 50, "divisor": 1, "offset": 0}
    },
    "skills": {
      "战技倍率": [100, 110, 120, ...]
    }
  }
}
```

### 武器数据 (weapons.json)

```json
{
  "武器ID": {
    "name": "武器名称",
    "type": "武器类型",
    "star": 4,
    "attributes": {
      "基础攻击力": {"base": 34, "growth": 31, "divisor": 9, "offset": 8},
      "攻击力+": {"base": 3.0, "growth": 12, "divisor": 5, "offset": 0, "special": [23.4]}
    },
    "special_ability": "特殊能力描述"
  }
}
```

---

## 🔄 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| v1.7.0 | 2024-XX-XX | 统一小数数据处理，新增荧光雷羽武器 |
| v1.6.0 | 2024-XX-XX | 重构计算引擎，优化乘区系统 |
| v1.5.0 | 2024-XX-XX | 添加公式反推功能 |
| v1.0.0 | 2024-XX-XX | 初始版本 |

---

## 📝 开发指南

### 添加新角色

```bash
python character_weapon_equipment/character_data/add_character.py
```

### 添加新武器

```bash
python character_weapon_equipment/weapon_data/add_weapon.py
```

### 代码规范

- 使用 PEP 8 编码规范
- 使用类型注解
- 添加单元测试

---

## 📄 许可证

MIT License

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！