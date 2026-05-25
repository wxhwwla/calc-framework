# 终末地伤害计算器 — 领域上下文

本文件定义项目内统一术语，供 Issue、测试与文档引用。

## 核心对象

| 术语 | 含义 |
|------|------|
| **角色** | `characters.json` 中的一条记录，含类型、星级、等级曲线、四维属性、战技/连携/终结技倍率等 |
| **武器** | `weapons.json` 中的一条记录，含 `基础攻击力` 曲线、`normal_skills`（普通技能词条）与 `special_skills`（特殊技能词条） |
| **装备** | `equipments.json` 中的一条记录；部位为 **护甲 / 护手 / 配件**（与 Wiki「装备种类」一致，旧称「胸甲」作别名） |
| **等级曲线** | 与角色/武器等级列表等长的数值数组（通常 90 级），由 JSON 预存，运行时直接读取 |
| **潜能** | 武器精炼等级序列（`talent`，0–5），不是角色天赋 |

## 属性与计算

| 术语 | 含义 |
|------|------|
| **主能力 / 副能力** | 角色四维（力量、敏捷、智识、意志）中的主、副属性名称 |
| **信赖** | 角色信赖加成，影响能力乘区 |
| **乘区** | `calculation/multiplicative_zones/` 中的乘法区链：能力乘区、能力值加成、最终攻击力等 |
| **15乘区链** | 伤害计算的15个乘法区：能力乘区、能力值加成、武器攻击力、攻击力加成、暴击伤害、伤害加成、物理伤害、元素伤害、防御减伤、抗性减伤、最终减伤、特殊减伤、破韧补正、易伤增伤、治疗加成 |
| **成长公式** | `value(lv) = base + floor((growth * (lv - 1) + offset) / divisor)`，用于反推与数据生成 |
| **普通技能** | 武器 `normal_skills[]`：无条件词条，字段 `zone`（1–3）、`effect`（如 `攻击力+`）、`curve[9]`（潜能 1–9 档） |
| **特殊技能** | 武器 `special_skills[]`：有条件或独立词条，字段 `zone`、`name`（完整展示名）、`condition`、`effect`、`curve[9]`、`max_stack` |
| **武器技能参数（代码）** | 计算/GUI 优先使用 `normal_skill_*` / `special_skill_*`；旧名 `sa1/sa2/sa3/ws/ws2` 仅兼容，触发 `DeprecationWarning` |
| **武器技能选用状态** | `calculation/weapon_skill_selection.WeaponSkillSelection`：普通/特殊技能槽位 → 预设 v2 视图与乘区 kwargs；GUI 面板读写见 `gui_design/weapon_skill_selection.py` |
| **配装攻击力求值** | `calculation/loadout_attack_eval.final_attack_details_for_loadout`：右侧乘区与全量搜索共用的最终攻击力 seam |
| **DamageContext** | 伤害上下文对象，包含攻击力、技能倍率、敌方属性等所有基础参数 |
| **DamageEffect** | 伤害效果对象，包含武器技能词条、装备词条、套装效果等 |
| **SkillScenario** | 技能场景对象，描述技能的伤害类型、倍率、属性等信息 |
| **LoadoutScore** | 配装评分对象，包含最终伤害值、各乘区明细等 |

## 数据管道

| 术语 | 含义 |
|------|------|
| **统一加载层** | `data.loader`：`get_characters()` / `get_weapons()` / `get_equipments()`，带缓存，`strict` 失败抛 `DataLoadError` |
| **预烘焙 JSON** | 已写入完整曲线的 JSON；GUI 不再在运行时调用 `process_*` |
| **录入脚本** | `add_weapon.py`、`add_character.py`、`scripts/seed_*.py`；经 `curve_baker` 烘焙曲线后写回 JSON |
| **懒加载缓存** | `data.loader` 模块的缓存机制：首次调用 get_*() 时加载 JSON 文件并填充全局变量，后续调用直接返回缓存 |
| **reload_*()** | 清除缓存函数：reload_characters()、reload_weapons()、reload_equipments() |
| **GameDataFacade** | 游戏数据门面类，提供统一的数据访问接口和错误处理 |

## 工程

| 术语 | 含义 |
|------|------|
| **仓库根目录** | Git 克隆顶层（含 `CONTEXT.md`、`.github/`（CI + Issue 模板）、`github_upload_module.py`、`docs/`、`tools/`） |
| **Python 包目录** | `endfield_damage_calculator/`（`main.py`、`tests/`、`pip install -e` 的工作目录） |
| **遗留目录** | `legacy/`：旧脚本归档，新功能勿依赖 |
| **应用根目录** | `utils.path_utils.get_application_dir()`：开发=包目录，打包=exe 所在发布文件夹 |
| **打包路径** | `get_resource_path` 读 exe **同级** JSON（非 onefile 内嵌） |
| **搜索导出** | 默认 `<应用根>/search_output/`；全量/MVP 续跑库与导出文件 |
| **全量遍历** | 枚举武器×四格配装；默认按当前技能单段伤害 TopN；开「使用手动次数」时按 **Σ(单段×次数)** TopN |
| **固定配装** | GUI **高级页**可固定 0–4 件具体装备（`FixedLoadoutSelection`）；未勾选部位在装备范围内遍历 |
| **搜索流水线** | 全量搜索的四阶段工作流：构建搜索计划 → 生成任务 → 评估任务 → 收集结果 |
| **run_signature** | 基于配置、数据版本、代码版本生成的唯一标识，用于续跑检测 |
| **TopNTracker** | Top-N 结果维护类，用于在全量搜索中跟踪最优配装 |
| **多技能加权** | 按技能释放次数加权计算总伤害：Σ(单次伤害 × 释放次数) |
| **计算与搜索区** | GUI **高级页**中部：武器/装备范围、固定配装、全量遍历、并行线程、预估与 MVP |
| **多技能次数区** | GUI **高级页**右侧：段级次数与「使用手动次数」开关 |
| **计算页** | 五列主视图：选择、属性、乘区；快速确认在乘区下方 |
| **高级页** | 原底栏三列（操作 / 全量搜索 / 多技能）；工具与分享在「更多设置」折叠内 |
| **右侧乘区** | 计算页第 4 列（`ZONE_COLUMN`），展示 15 乘区链 |
| **主界面列权重** | 计算页 `(0, 0, 1, 1, 0)`；乘区固定宽 340px |
| **UI 偏好** | `<应用根>/ui_preferences.json`：启动页策略（总是计算页 / 记住上次）、`last_page` |
| **预设 ui_state** | 配装 JSON 可选字段：折叠区展开态、`current_page`（计算页/高级页） |
| **配装预设 v2** | `schema: endfield_loadout_preset_v2`；含 `weapon_normal_levels`、`weapon_special_states[{level, stack}]`；v1 与旧 `ws_*` 导入仍兼容 |
| **上传流程** | 根目录 `github_upload_module.py`；`_VERSION` 自动 bump；可选提交签名；说明见 `please_read_me.UPLOAD_WORKFLOW` |
| **下载覆盖** | 根目录 `github_download_module.py`；须输入确认词 `覆盖本地`；会丢弃未提交与未跟踪文件 |
| **数据来源与许可** | GUI 按钮 + `docs/数据来源与许可.md`；软件 AGPL/商业双许可，数据见 `DATA_LICENSE` |
| **仓库维护工具** | `tools/`：仓库级脚本（BWIKI 侦察、审计等），与包内 `endfield_damage_calculator/scripts/` 区分 |
| **代码结构约束** | 每目录直接子项 **≤ 10**；业务 `.py` **≤ 400 行**（硬顶 500）；见 [`docs/adr/0001-code-layout-constraints.md`](docs/adr/0001-code-layout-constraints.md)、[`docs/代码结构规范.md`](docs/代码结构规范.md) |
| **BWIKI 侦察** | `tools/bwiki_scout/`：阶段 C 拉取 Wiki 至 `output/raw/`（gitignore）；阶段 B `parse_draft.py` 仅生成对照草案 |
| **BWIKI 同步** | `sync_operators.py` / `sync_weapons.py`：默认预览差异；`--apply` 反推公式后写入 `characters.json`/`weapons.json` 与 `seed_*.py`（以 Wiki 为准） |
| **项目依赖** | 运行时：`customtkinter`（见 `pyproject.toml`）；开发：`[dev]`→pytest；打包：`[build]`→PyInstaller；布局模块：`release_bundle/`（勿命名 `packaging`） |
