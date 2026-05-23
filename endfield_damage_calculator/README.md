# 终末地伤害计算小工具（详细文档）

> 本文件为 **Python 包目录** `[包]` 下的详细说明。  
> GitHub 首页与速览见仓库根 [**README.md**](../README.md)；日常命令见 [**操作指令集**](../docs/操作指令集.md)；术语见 [**CONTEXT.md**](../CONTEXT.md)；算法细节见 [**docs/算法与架构.md**](../docs/算法与架构.md)。

> 基于 CustomTkinter 开发的《明日方舟：终末地》伤害计算辅助工具

## 🌟 项目简介

本工具旨在帮助玩家计算角色和武器的属性成长、伤害乘区等数据，优化配装和战斗策略。

### 🎯 功能特性

| 功能模块 | 说明 |
|---------|------|
| 角色选择 | 支持按类型、星级筛选角色 |
| 武器选择 | 支持按类型、星级筛选武器，包含特殊能力等级选择 |
| 属性展示 | **角色属性列**（四维、基础攻击与技能倍率）与**武器属性列**分列显示等级曲线明细（选择区仅负责操作，不重复摘要） |
| 乘区计算 | 点击「确认选择」后，在角色与武器均有效时刷新右侧乘区（能力、攻击力等） |
| 单段伤害 / 快照 | 计算模式：15 乘区单段伤害、乘区快照 |
| 全量搜索（实验） | 固定配装 0–4 + TopN 弹窗；可选多技能加权总伤；导出至 `search_output/` |
| 公式反推 | 支持从数值数据反推成长公式参数 |
| 数据管理 | 支持添加新角色和武器数据；装备经 BWIKI `sync_equipments.py` |

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
│   ├── DATA_README.md         # 数据许可说明（见仓库根 DATA_LICENSE）
│   ├── character_data/        # 角色数据
│   │   ├── characters.json    # 角色JSON数据
│   │   ├── character_data.py  # 角色数据管理
│   │   ├── add_character.py   # 添加角色脚本
│   │   └── formula.py         # 角色公式（保留兼容）
│   ├── weapon_data/           # 武器数据
│   │   ├── weapons.json
│   │   ├── add_weapon.py
│   │   └── formula.py         # 保留兼容
│   └── equipment_data/
│       └── equipments.json    # 装备（全量搜索）
├── data/                      # 统一数据加载层
│   └── loader.py              # get_characters / get_weapons / get_equipments
├── calculation/               # 伤害引擎、装备、搜索、MVP 流水线（见 docs/MVP搜索验收说明.md）
├── gui_design/                # GUI 界面模块
│   ├── gui.py                 # 主应用（5 列 + 底栏）
│   ├── gui_layout.py          # grid 常量
│   ├── fixed_loadout_controls.py  # 固定配装 UI
│   ├── confirm_refresh.py     # 确认刷新去重
│   ├── preview_lines.py       # 单/多技能快速预览文案
│   ├── search_export_paths.py # search_output/ 导出路径
│   ├── gui_settings.py        # 主题与字体
│   ├── selection_panel.py     # 选择面板
│   ├── selection_components.py
│   └── property_display.py    # 确认后属性列与乘区
├── legal/                     # 许可与数据来源（GUI 对话框）
│   └── attribution.py
├── scripts/                   # 包内维护脚本（非 pytest；≠ 仓库 tools/）
│   ├── inverse_cli.py         # 反推公式 CLI
│   ├── inverse_formula_gui.py # 反推公式 GUI（维护用）
│   ├── seed_weapons.py        # 武器录入示例
│   └── seed_characters.py     # 角色录入示例
├── tests/                     # pytest 单元测试
│   ├── test_calculation.py
│   ├── test_game_data_contract.py
│   └── ...
├── release_bundle/            # 发布布局（勿命名 packaging）
│   └── release_layout.py
├── search_output/             # 全量/MVP 搜索导出（gitignore，运行后生成）
└── utils/
    └── path_utils.py          # get_application_dir / get_resource_path
```

### 仓库根目录（与本包并列）

| 路径 | 说明 |
|------|------|
| [`tools/`](../tools/README.md) | BWIKI 侦察、审计等；在 `[根]` 执行 `python tools/bwiki_scout/scout.py` |
| [`docs/`](../docs/README.md) | 操作指令集、许可、算法文档 |
| [`legacy/`](../legacy/README.md) | 遗留脚本，新录入请用本包 `add_character` / `add_weapon` |
| `github_upload_module.py` / `github_download_module.py` | 在 `[根]` 运行 |

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

若本机已配置 Git 提交签名（`commit.gpgsign` 或 `user.signingkey`），脚本会在 commit 时自动签名，便于 GitHub 显示 **Verified**；未配置会打印设置提示（见 [`docs/操作指令集.md`](../docs/操作指令集.md) §1.5）。

**从远程覆盖本地（危险）**：在 `[根]` 运行 `python github_download_module.py`，须输入确认词 **`覆盖本地`**；会丢弃未提交与未跟踪文件。详见操作指令集 §5.2。

### 安装依赖

```bash
cd endfield_damage_calculator
pip install -e ".[dev]"
```

（`[dev]` 含 pytest；`[build]` 含 PyInstaller。仅 GUI：`pip install -e .`；要打包：`pip install -e ".[build]"`。）

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
pip install -e ".[build]"
python build.py
```

产物为 **`dist/终末地伤害计算器/` 文件夹**（onedir）：exe 与 `characters.json` / `weapons.json`、`DATA_LICENSE` 等同目录分发，符合软件与数据许可分离。请整夹分发，勿只发 exe。详见 [`docs/操作指令集.md`](../docs/操作指令集.md) §7。

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

1. **选择角色**：第 0 列选择类型、星级、名称与等级（含信赖、技能等级）
2. **选择武器**：第 1 列选择武器并调整技能与特殊能力滑块
3. **确认**：底栏「确认选择」——刷新属性列与右侧乘区/预览（输入未变时不会重复整页重绘）
4. **全量搜索**（可选）：底栏设置武器/装备范围、固定配装、多技能次数后点「全量遍历」

### GUI 布局

主窗口为 **5 列 + 底栏**（`gui_layout.py`，`APP_COLUMN_WEIGHTS = (0, 0, 1, 1, 5)`）：

| 区域 | 内容 | 宽度策略 |
|------|------|----------|
| 列 0 | 角色选择 | `weight=0`，min ~260px |
| 列 1 | 武器选择 | `weight=0` |
| 列 2 | **角色属性** | `weight=1` |
| 列 3 | **武器属性** | `weight=1` |
| 列 4 | **右侧乘区** | `weight=5`，主伸缩列 |
| 底栏 | 确认/模式、**全量搜索**（固定配装、遍历、MVP）、**多技能次数** | 横跨列 0–3 |

- 启动后自动确认一次；输入未变时不会重复清空三列（最小化恢复不闪屏）。
- 全量：开「使用手动次数」后按加权总伤排名，否则按当前技能单段伤害。
- 角色或武器无效时，仅对应属性列显示提示，且不刷新乘区。
- 武器属性列数值规则：**第一技能**对应条目为 JSON 整数；**其余** `xxx+` 与特殊能力字段按百分数显示（如 `27.6%`）。

术语与列号说明见仓库根目录 [`CONTEXT.md`](../CONTEXT.md)。

### 数据来源与许可

武器列下方 **「数据来源与许可」** 打开简略说明，可跳转 `LICENSE`、`DATA_LICENSE`、BWIKI、CC 与完整文档 [`docs/数据来源与许可.md`](../docs/数据来源与许可.md)。

### BWIKI 数据侦察与同步（`[根]` / `tools/bwiki_scout/`）

对比 [终末地 BWIKI](https://wiki.biligame.com/zmd/) 与本地 JSON；侦察默认只写 `tools/bwiki_scout/output/`（已 gitignore）。经 `sync_*.py --apply` 才更新本目录下的 `characters.json` / `weapons.json` 与 `scripts/seed_*.py`。

```powershell
cd e:\endfield_damage_calculator   # [根]
python tools/bwiki_scout/scout.py              # 拉取/续跑缓存（含干员 */详细数据）
python tools/bwiki_scout/compare_stats.py      # 干员数值对比报告（离线）
python tools/bwiki_scout/sync_operators.py     # 预览：属性 + 技能倍率
python tools/bwiki_scout/sync_weapons.py       # 预览：武器攻击与词条（需 Wiki 含 rank 表）
python tools/bwiki_scout/sync_operators.py --apply
```

完整字段映射与模块说明见 [`tools/bwiki_scout/README.md`](../tools/bwiki_scout/README.md)、[`docs/操作指令集.md`](../docs/操作指令集.md) §9。

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
| `test_gui_layout_contract.py` | 主界面 5 列 + 底栏布局权重契约 |
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

## 📄 许可证与数据来源

- **软件**：[`LICENSE`](../LICENSE)（AGPL-3.0 或商业许可）
- **数据**：[`DATA_LICENSE`](../DATA_LICENSE)（商用不可用本仓库 JSON）
- **说明**：[`docs/数据来源与许可.md`](../docs/数据来源与许可.md) · [`合规自查清单`](../docs/合规自查清单.md)
- **GUI**：「数据来源与许可」按钮

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！