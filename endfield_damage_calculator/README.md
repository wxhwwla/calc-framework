# 终末地伤害计算小工具（详细文档）

> 本文件为 **Python 包目录** `[包]` 下的详细说明。  
> GitHub 首页与速览见仓库根 [**README.md**](../README.md)；日常命令见 [**操作指令集**](../docs/操作指令集.md)；术语见 [**CONTEXT.md**](../CONTEXT.md)；算法细节见 [**docs/算法与架构.md**](../docs/算法与架构.md)；通用框架见 [**framework/**](../framework/)。

> PySide6 GUI，支持乘区计算、全量搜索、配装对比

## 🌟 项目简介

本工具旨在帮助玩家计算角色和武器的属性成长、伤害乘区等数据，优化配装和战斗策略。

### 🎯 功能特性

| 功能模块 | 说明 |
|---------|------|
| 角色选择 | 支持按类型、星级筛选角色 |
| 武器选择 | 支持按类型、星级筛选武器，含**普通技能 / 特殊技能**等级与层数选择 |
| 属性展示 | **角色属性列**（四维、基础攻击与技能倍率）与**武器属性列**分列显示等级曲线明细（选择区仅负责操作，不重复摘要） |
| 乘区计算 | 点击「确认选择」后，在角色与武器均有效时刷新右侧乘区（能力、攻击力等） |
| 单段伤害 / 快照 | 计算模式：15 乘区单段伤害、乘区快照 |
| 全量搜索（实验） | 固定配装 0–4 + TopN 弹窗；可选多技能加权总伤；导出至 `search_output/` |
| 工具与分享 | 配装预设 JSON、多方案对比、操作日志、计算历史、伤害仪表盘；可选 `plugins/enemies/` 敌人防御 |
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
│       ├── dag/               # DAG 引擎适配器（桥接 calc-framework）
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
├── gui_design/                # GUI 界面模块（PySide6）
│   ├── shell/                 # 主窗口与控制栏
│   │   ├── qt_app.py          # 主应用（双页签：计算页 + 高级页）
│   │   └── qt_control_dock.py # 高级页三列控制栏
│   ├── panels/                # 选择面板
│   │   └── selection/
│   │       ├── qt_panel.py    # 四级联动选择面板（类型/星级/名称/等级）
│   │       ├── qt_subpanels.py # 技能等级面板
│   │       └── qt_ability_panel.py  # 能力值面板
│   ├── shared/                # 共享模块
│   │   ├── display_view/
│   │   │   └── qt_columns.py  # QtAttributeColumns 属性列展示
│   │   ├── calc_history.py    # 计算历史管理
│   │   ├── calc_mode_labels.py # 计算模式标签映射
│   │   ├── damage_visualization.py # matplotlib 伤害仪表盘
│   │   ├── preset_batch_compare.py # 多方案对比
│   │   └── ui_preferences.py  # 启动页策略、ui_preferences.json
│   ├── app/                   # 应用逻辑层
│   │   ├── confirm_refresh.py # 确认刷新去重与签名
│   │   ├── display_request.py # 确认刷新统一输入
│   │   ├── loadout_evaluation.py # 预览/仪表盘求值
│   │   ├── loadout_preset.py  # 配装预设 JSON 导入导出
│   │   └── loadout_state.py   # 从面板刮取配装状态
│   ├── backends/              # Qt 后端工具
│   │   ├── qt_factory.py      # Qt 控件工厂
│   │   └── qt_worker.py       # 搜索线程
│   ├── controls/              # 控件目录
│   │   ├── enhancement/       # 高级控制对话框
│   │   ├── manual_buff/       # 场外 Buff 窗口
│   │   ├── multi_skill/       # 多技能次数
│   │   └── search/            # 搜索操作
│   ├── presentation/          # 展示层
│   │   ├── display/           # 属性列文本格式
│   │   ├── preview/           # 技能预览
│   │   ├── damage_snapshot.py # 确认后伤害快照
│   │   ├── display_lines.py   # 属性列格式化文案
│   │   ├── preview_lines.py   # 单/多技能快速预览（带缓存）
│   │   └── search_results_lines.py # 搜索结果格式化
│   ├── search_ui/             # 搜索 UI
│   │   ├── search_settings.py # 并行线程/TopN 配置
│   │   ├── search_export_paths.py # search_output/ 导出路径
│   │   └── search_estimate_message.py # 搜索预估文案
│   └── layout/
│       └── gui_layout.py      # grid 常量、窄屏重排、按钮尺寸
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
    ├── path_utils.py          # get_application_dir / get_resource_path
    ├── gui_fonts.py           # 系统 UI 字体 + matplotlib 中文
    ├── gui_chart_theme.py     # 仪表盘图表与 CTk 深色主题同步
    └── platform_win32_patch.py # Windows WMI 规避（启动/打包）
```

### 仓库根目录（与本包并列）

| 路径 | 说明 |
|------|------|
| [`framework/`](../framework/) | **通用计算框架 calc-framework**：DAG 引擎 + 数据引擎 + 声明式 UI + 布局编辑器（独立 pip 包） |
| [`tools/`](../tools/README.md) | BWIKI 侦察、审计等；在 `[根]` 执行 `python tools/bwiki_scout/scout.py` |
| [`docs/`](../docs/README.md) | 操作指令集、许可、算法文档 |
| [`legacy/`](../legacy/README.md) | 遗留脚本，新录入请用本包 `add_character` / `add_weapon` |
| `github_upload_module.py` / `github_download_module.py` | 在 `[根]` 运行 |

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- PySide6 6.6+（默认 GUI 后端）
- matplotlib 3.8+（运行时依赖，含伤害仪表盘）

### 项目依赖

- 运行时：`PySide6` + `matplotlib`（见 `pyproject.toml`）
- 开发：`[dev]` → pytest；打包：`[build]` → PyInstaller

首次安装：`pip install -e .`（或 `pip install -e ".[dev]"`）。缺依赖时 `main.py` 会警告但不会自动 pip。

### 版本号

- `_VERSION`：日常由上传脚本在有业务改动并 push 成功时自动递增（见下方「GitHub 上传」）；`pyproject.toml` 通过 dynamic 读取。
- `_EXE_VERSION`：仅重新打包 exe 前在 `please_read_me.py` **手动**修改；**改后必须重新 `python build.py`**，旧 `dist/` 内 exe 不会自动更新。
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

打包前会检查 PyInstaller 与 matplotlib；Windows 上通过 `pyinstaller_entry` 规避 WMI 卡死；各 GUI 子模块 import CTk 前亦打补丁。默认 20 分钟超时 + 15 秒心跳（见 `docs/操作指令集.md` §7）。产物内仪表盘无需用户另装 matplotlib。

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

### GUI 使用说明（详细）

完整的 GUI 操作文档见 **[docs/GUI使用说明.md](../docs/GUI使用说明.md)**，涵盖：

- 计算页：角色/武器选择、属性展示、乘区计算
- 高级页：全量搜索、多技能加权、异常矩阵
- 确认计算流程、预设系统、外部 Buff 微调
- 工具与分享：多方案对比、伤害仪表盘、计算历史

### 基本操作流程

1. **选择角色**：计算页左起第一个面板，四级联动（类型 → 星级 → 名称 → 等级）
2. **选择武器**：计算页第二面板，自动按角色武器类型过滤
3. **调整参数**：技能等级、信赖等级、潜能（武器）、层数（特殊技能）
4. **确认**：点击「确认选择」——刷新属性列与乘区
5. **高级操作**（可选）：切换到**高级页**
   - 全量搜索、多技能加权
   - 工具与分享、导入导出配装
   - 异常矩阵、Buff 微调

### GUI 布局

主窗口为 **双页签**（`shell/qt_app.py` + `shell/qt_control_dock.py`）：

| 页签 | 布局 | 说明 |
|------|------|------|
| **计算页** | 两列 Splitter + 顶部选择面板 | 左：角色/武器选择 + 属性列；右：乘区展示（ComputeSheet） |
| **高级页** | 三列 | 操作/工具、全量搜索、多技能次数 |

- 启动后自动确认一次；切页不丢输入；关闭时保存 `ui_preferences.json`（启动页策略）。
- 全量：开「使用手动次数」后按段级加权总伤排名，否则按当前技能单段伤害。
- 角色或武器无效时，仅对应属性列显示提示，且不刷新乘区。
- 武器属性列数值规则：按词条名区分展示——`附加攻击力+`、四维+、主/副能力+ 等为**固定整数**；`攻击力+`、*伤害+、*率+、充能效率 带 `%`（与 `display_lines.weapon_bonus_display_uses_percent` 一致）。

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
| `test_gui_layout_contract.py` | 计算页五列 + 高级页 dock 布局契约 |
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

仓库内 JSON 为**中文键**、**数组曲线**，运行时经 `data.loader` 读取。详见 [`CONTEXT.md`](../CONTEXT.md) 与 `tests/test_game_data_contract.py`。

### 角色数据 (`characters.json`)

每条为数组元素（非嵌套 `角色ID` 对象）。示例：

```json
{
  "名称": "陈千语",
  "类型": "近卫",
  "星级": 5,
  "主能力": "敏捷",
  "副能力": "力量",
  "力量": [10, 11, "…", 90],
  "基础攻击力": [100, 105, "…", 90],
  "战技倍率": [[100, 110, "…", 1200]],
  "连携技倍率": [[50, "…", 600]],
  "终结技倍率": [[200, "…", 800], [636, "…", 900]]
}
```

### 武器数据 (`weapons.json`)

每条须含 `normal_skills` 与 `special_skills`：

```json
{
  "名称": "示例武器",
  "类型": "单手剑",
  "星级": 5,
  "基础攻击力": [100, 105, "…", 280],
  "normal_skills": [
    {"zone": 1, "effect": "智识+", "curve": [12.0, "…", 93.0]},
    {"zone": 2, "effect": "攻击力+", "curve": [3.0, "…", 23.4]}
  ],
  "special_skills": [
    {
      "zone": 3,
      "name": "施放战技后，法术伤害+",
      "condition": "施放战技后",
      "effect": "法术伤害+",
      "curve": [12.0, "…", 33.6],
      "max_stack": 2
    }
  ]
}
```

读写与迁移：`weapon_data/special_fields.py`；`tools/migrate_weapon_skills_schema.py`。

### 配装预设 (`endfield_loadout_preset_v2`)

```json
{
  "schema": "endfield_loadout_preset_v2",
  "char_name": "秋栗",
  "weapon_name": "逐鳞3.0",
  "weapon_normal_levels": [9, 8, 1],
  "weapon_special_states": [{"level": 7, "stack": 2}],
  "multi_skill_counts": {"战技:1": 2}
}
```

v1 与旧 `ws_*` 字段导入时自动归一（`loadout_preset.py`）。

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

## 🤝 贡献与反馈

| 方式 | 说明 |
|------|------|
| **报告 Bug** | GitHub **Issues → New issue → Bug 报告**（请填复现步骤与窗口标题中的版本号） |
| **功能建议** | 同上，选 **功能建议** |
| **文档** | 人类操作见 [`docs/操作指令集.md`](../docs/操作指令集.md)；Agent 见 [`docs/会话接续手册.md`](../docs/会话接续手册.md) |
| **代码贡献** | Fork 后 PR；大改动请先开 Issue 讨论 |

Issue 模板与 `gh` 用法：[`docs/agents/issue-tracker.md`](../docs/agents/issue-tracker.md)。