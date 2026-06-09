# Calc Framework（通用游戏计算框架）— 领域上下文

本文件定义项目内统一术语，供 Issue、测试与文档引用。

## 核心对象

| 术语 | 含义 |
|------|------|
| **角色** | `characters.json` 中的一条记录，含类型、星级、等级曲线、四维属性（力量/敏捷/智识/意志）、基础攻击力、基础生命值、基础防御力、战技/连携/终结技倍率等 |
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
| **普通技能** | 武器 `normal_skills[]`：无条件词条，字段 `zone`（1–3）、`effect`（如 `攻击力+`）、`curve[9]`（精炼等级 1–9 档数值） |
| **精炼等级** | 武器精炼等级，值域 1–9，影响 `normal_skills` 中所有 `curve[9]` 的索引值；也称为品质倍率 |
| **特殊技能** | 武器 `special_skills[]`：有条件或独立词条，字段 `zone`、`name`（完整展示名）、`condition`、`effect`、`curve[9]`、`max_stack` |
| **武器技能参数（代码）** | 计算/GUI 优先使用 `normal_skill_*` / `special_skill_*`；旧名 `sa1/sa2/sa3/ws/ws2` 仅兼容，触发 `DeprecationWarning` |
| **武器技能选用状态** | `calculation/weapon_skill_selection.WeaponSkillSelection`：普通/特殊技能槽位 → 预设 v2 视图与乘区 kwargs；GUI 面板读写见 `gui/weapon_skill_selection.py` |
| **配装攻击力求值** | `calculation/loadout_attack_eval.final_attack_details_for_loadout`：右侧乘区与全量搜索共用的最终攻击力 seam |
| **DamageContext** | 伤害上下文对象，包含攻击力、技能倍率、敌方属性（防御/抗性/无视抗性/失衡易伤系数/失衡状态）等所有基础参数 |
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
| **Python 包目录** | `games/endfield/`（`main.py`、`tests/`、`pip install -e` 的工作目录） |
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
| **纯 DAG 适配器架构** | `games/{game}/` 不包含独立计算引擎，所有计算逻辑以 DAG 自定义函数形式放在 `framework/adapters/{game}/functions.py` 中 |
| **薄游戏包** | `games/{game}/` 只做数据加载 + DAG 适配 + 轻量 GUI，不做重型计算 |
| **单计算路径** | 游戏只有一个公式实现源头（DAG 自定义函数），不存在需要同步的两套代码 |
| **game-template** | `docs/game-template/` 下的标准游戏包骨架模板，用于快速创建新游戏 |
| **标准化游戏包结构** | ADR-0023 定义的 `games/{game}/` 标准目录布局，所有游戏包对齐此结构 |
| **计算与搜索区** | GUI **高级页**中部：武器/装备范围、固定配装、全量遍历、并行线程、预估与 MVP |
| **多技能次数区** | GUI **高级页**右侧：段级次数与「使用手动次数」开关 |
| **计算页** | 五列主视图：选择、属性、乘区；快速确认在乘区下方 |
| **高级页** | 原底栏三列（操作 / 全量搜索 / 多技能）；工具与分享在「更多设置」折叠内 |
| **右侧乘区** | 计算页第 4 列（`ZONE_COLUMN`），展示 15 乘区链 |
| **主界面列权重** | 计算页 `(0, 0, 1, 1, 0)`；乘区固定宽 340px |
| **UI 偏好** | `<应用根>/ui_preferences.json`：启动页策略（总是计算页 / 记住上次）、`last_page` |
| **预设 ui_state** | 配装 JSON 可选字段：折叠区展开态、`current_page`（计算页/高级页） |
| **配装预设 v2** | `schema: endfield_loadout_preset_v2`；含 `weapon_normal_levels`、`weapon_special_states[{level, stack}]`；v1 与旧 `ws_*` 导入仍兼容 |
| **敌方参数面板** | `gui/controls/enemy/qt_enemy_panel.py`：插件敌人下拉 + 防御/抗性/无视抗性/失衡易伤系数/失衡状态微调；信号 `enemy_params_changed` 传播完整 dict |
| **敌方参数字段** | 5 个：`enemy_defense`（防御力）、`enemy_resistance`（抗性%）、`ignore_resistance`（无视抗性%）、`imbalance_vulnerability_coeff`（失衡易伤系数）、`is_unbalanced`（是否失衡） |
| **插件敌人解析** | `data/enemy_params.py`：`enemy_damage_context_overrides(enemy_id)` → dict 含全部 5 个敌方参数；`resolve_*` 系列函数按 id 读取单个字段 |
| **总伤结算面板** | `gui/presentation/total_damage_panel.py`：确认后展示各技能段加权总伤明细（技能类型占比 → 段级单次×次数 → 🏆 加权总伤）；`hide_damage()` / `update_from_snapshot()`
| **Web 版框架** | `web/frontend/`（React + TypeScript + Vite + MUI v6 + Zustand + React Flow）+ `web/backend/`（FastAPI）。前端接入 DAG 引擎 API，支持适配器选择、参数表单、结果展示、DAG 可视化 |
| **Upload Script** | `[根]` `github_upload_module.py`（subprocess → `scripts/tools/`）：bump `scripts/_version.py`、pre-commit（最多 2 轮）、仅 add 变更路径、commit + push（`--check` / `--minor` / `--no-bump` / `--tag` / `--no-git-backup`）。**必读** [`docs/上传脚本与-pre-commit.md`](docs/上传脚本与-pre-commit.md)。Minor 前备份 `.git` → `git_backup/snapshots/` |
| **UPLOAD_SUMMARY** | `scripts/_version.py` 底部临时块；顶部 `SUMMARY_BEGIN`/`SUMMARY_END` 禁止为空。Windows 中文 doc 路径：`core.quotepath=false`，勿对 porcelain 转义串用 `Path()` |
| **下载覆盖** | 根目录 `github_download_module.py`；须输入确认词 `覆盖本地`；会丢弃未提交与未跟踪文件 |
| **三目标打包** | `main_build.py --target {calculator|designer|pack-designer}`：计算器/数据设计器/配置包设计器三个 exe |
| **终末地数据设计器** | `designer/designer_main.py` — 三个页签：公式反推（InverseTab）、数据编辑（DataEditorTab）、数据浏览（DataBrowserTab）。独立于计算器主 GUI |
| **DataEditorTab** | `designer/data_editor_tab.py` — 图形化新增/编辑/删除角色、武器、装备，通过 `data.loader` 读写 JSON 并刷新缓存 |
| **数据来源与许可** | GUI 按钮 + `docs/数据来源与许可.md`；软件 AGPL/商业双许可，数据见 `DATA_LICENSE` |
| **仓库维护工具** | `tools/`：仓库级脚本（BWIKI 侦察、审计等），与包内 `games/endfield/scripts/` 区分 |
| **代码结构约束** | 每目录直接子项 **≤ 20（硬顶）**、**目标 ≤ 15**；业务 `.py` **≤ 400 行**（硬顶 500）；见 [`docs/adr/0001-code-layout-constraints.md`](docs/adr/0001-code-layout-constraints.md)、[`docs/代码结构规范.md`](docs/代码结构规范.md) |
| **文档字符串** | 公共 API 与长函数（≥40 行）**必须** Google 风格（中文）；内部 `_` helper **可不写** |
| **BWIKI 侦察** | `tools/bwiki_scout/`：阶段 C 拉取 Wiki 至 `output/raw/`（gitignore）；阶段 B `parse_draft.py` 仅生成对照草案 |
| **BWIKI 同步** | `sync_operators.py` / `sync_weapons.py`：默认预览差异；`--apply` 反推公式后写入 `characters.json`/`weapons.json` 与 `seed_*.py`（以 Wiki 为准） |
| **项目依赖** | 运行时：`PySide6` + `matplotlib`（见 `pyproject.toml`）；开发：`[dev]`→pytest；打包：`[build]`→PyInstaller；布局模块：`release_bundle/`（勿命名 `packaging`） |
| **资源目录** | `resources/` — 业务资源文件（如捐赠二维码 `donation/donation_qr.png`）；打包时 `--add-data` 包含 |
| **捐赠组件** | `utils/donation.py`：所有 GUI 共享的`DonationWidget`+`open_donation_dialog()`；捐赠不构成购买软件对价 |
| **捐赠 widget（布局）** | `type:"widget"` + `widget_type:"donation"` — 可嵌入 .calcpack 布局的捐赠卡片，含自定义文字和图片，随配置包传播 |
| **数据许可** | `DATA_LICENSE`：商业禁止使用本仓库 JSON；须自行从游戏/Wiki 获取 |
| **许可结构** | 软件 AGPL-3.0/商业双许可（`LICENSE`）+ 数据单独许可（`DATA_LICENSE`）；发布包须同时附带 |
| **PySide6 LGPL** | 打包 exe 以动态链接方式使用 Qt，符合 LGPL 要求；须保留 PySide6 版权声明 |
| **OCR 依赖** | `tools/ocr/` 可选依赖 EasyOCR（Apache 2.0）+ TorchVision（BSD-3-Clause，替代原 AGPL-3.0 ultralytics） |
| **Arknights 侦察** | `tools/arknights_scout/`：BWIKI 明日方舟爬虫，拉取全量干员数据至 `output/raw/`（html+wikitext+meta），解析输出至 `output/parsed/`（JSON） |
| **Arknights 适配包** | `framework/adapters/arknights/`：元数据 28 属性 + 5 函数 + 51 节点 DAG 计算图 |
| **方舟 DAG 公式** | 物理 = `max(ATK×倍率-DEF, ATK×倍率×5%)×(1+伤害加成%)`；法术 = `ATK×倍率×(1-RES/100)×(1+伤害加成%)`；真伤 = `ATK×倍率×(1+伤害加成%)` |
| **方舟游戏包** | `games/arknights/`：`calc/dag_adapter/`（ArknightsContextLoader + compute_snapshot_with_dag + SnapshotResult） |
| **方舟 Web API** | `web/backend/api/arknights.py`：3 个端点 `GET /operators` / `GET /operators/{name}` / `POST /compute` |
| **方舟测试** | `games/arknights/tests/`：37 个 pytest（loader 单元 + DAG 端到端 + 真实数据集成） |

## 标准数据录入（四层数据契约）

| 术语 | 含义 |
|------|------|
| **四层数据契约** | 从实体→属性→技能→数值的四层嵌套结构，由 `docs/adr/0005-data-schema-design.md` 定义，`tools/data_pipeline/schema.py` 实现 TypedDict |
| **ETL 工具链** | `tools/data_pipeline/`：CSV/旧JSON → schema 校验 → 标准 JSON 输出；CLI `python -m tools.data_pipeline.cli` |
| **EntitySchema（L1）** | 实体层。必填 `名称`，可选 `_entity_type`（character/weapon/equipment/mount） |
| **属性筛选层（L2）** | 开发者自由平铺的筛选字段（星级、类型、属性等），框架不约束 |
| **SkillSchema（L3）** | 技能层。`名称`（即筛选 key）、`标签`（主动/被动）、`百分比`（倍率是否 ÷100）、`技能类型`（可选默认类型）、`段[]` |
| **SegmentSchema（L4）** | 数值层。`倍率`（int[]）、`伤害类型`（可选，覆盖技能级类型） |
| **百分比标记** | `百分比: true` 表示倍率整数需 ÷100 再用（如 169 → 1.69）；`false` 表示直接使用原始值 |
| **主动 / 被动** | 技能标签。`"主动"` = 倍率类技能（角色的战技/连携技）；`"被动"` = 加成型技能（武器的主能力值+） |
| **伤害类型默认链** | 适配器级默认 → 技能级 `技能类型` → 段级 `伤害类型`；空则继承上层 |
| **迁移器 from_legacy_endfield** | `tools/data_pipeline/transformers/from_legacy_endfield.py`：将旧 `characters.json`/`weapons.json` 自动转换为标准 EntitySchema |
| **校验器 — schema_check** | `tools/data_pipeline/validators/schema_check.py`：检查必填字段、标签合法性、段完整性 |
| **数据沙箱** | `tools/data_sandbox/`：隔离环境中测试自定义游戏数据，不修改真实文件的 CLI 工具集 |
| **Sandbox Validator** | `tools/data_sandbox/validator.py`：使用 `schema_check` 校验 EntitySchema 格式，返回 `ValidationResult` |
| **Sandbox Tester** | `tools/data_sandbox/tester.py`：对实体数据执行健全性测试（命名/技能/倍率），返回 `TestResult` |
| **Sandbox Reporter** | `tools/data_sandbox/reporter.py`：整合校验+测试+差异，生成 Markdown 报告 |
| **Sandbox Diff** | `tools/data_sandbox/sandbox.py` 的 `diff` 子命令：基于 `data_pipeline.diff` 对比自定义与参考数据 |
| **Sandbox CLI** | `python -m tools.data_sandbox.sandbox` 四个子命令：`validate` / `test` / `report` / `diff` |

## 配置包与开发者工具

| 术语 | 含义 |
|------|------|
| **.calcpack** | 游戏配置包，ZIP 格式，含 DAG 公式 + 数据 + UI 布局 + 主题，供用户 ComputeSheet 加载 |
| **`tools/designer/`** | 配置包设计器，独立 GUI：数据录入 + 布局编辑 + 主题编辑 → `.calcpack` 导出 |

## 截图识装管线

| 术语 | 含义 |
|------|------|
| **OCR 管线** | 截图文件夹 → TorchVision 目标检测 → EasyOCR 文字识别 → 模糊匹配 → 一键填入计算器 |
| **TorchVision 目标检测** | `tools/ocr/detector.py`：基于 torchvision Faster R-CNN (MIT/BSD-3-Clause)，输出检测框 |
| **EasyOCR 文字识别** | `tools/ocr/recognizer.py`：在检测区域内做 ch_sim+en 文字识别，附带 `GAME_TERMS` 纠错字典 |
| **OcrMapper** | `tools/ocr/mapper.py`：通过 `difflib.get_close_matches` 对 OCR 文本做模糊匹配，输出角色/武器名称、等级、信赖 |
| **6 类 UI 区域** | `endfield_classes.yaml` 定义：character_panel（角色面板）、weapon_panel（武器面板）、equipment_panel（装备面板）、skill_panel（技能面板）、zone_values（乘区数值）、enemy_panel（敌方面板） |
| **标注工具** | `tools/ocr/label.py`：PySide6 GUI，在截图上拖拽标注 bounding box，导出 COCO 格式训练集 |
| **TorchVision 训练** | `tools/ocr/train.py`：基于 torchvision 对标注数据集 finetune |
| **GAME_TERMS** | `recognizer.py` 内的 31 条游戏术语纠错表（如「秋粟→秋栗」「攻击力→攻击力」），提高 OCR 专有名词准确率 |
| **select_by_name()** | `QtSelectionPanel` 新增方法，按名称级联选择类型/星级/名称 combo，实现一键填入 |
| **截图识装按钮** | GUI 底栏「截图识装」按钮 → 打开检测对话框 → 选文件夹 → TorchVision+OCR → 点击「填入计算器」一键应用 |

## 通用框架（全品类规划）

| 术语 | 含义 |
|------|------|
| **五层架构** | ADR-0010 定义：纯数学内核 → 通用战斗规则引擎 → 通用数据模型 → 游戏适配器 → 表现层 |
| **纯数学内核** | 层1，只做四则运算/百分比/区间/概率/循环，完全不知道游戏对象 |
| **通用战斗规则引擎** | 层2，动态表达式引擎 + 可插拔模块（暴击/命中/护盾/衰减等），乘区顺序配置化 |
| **通用数据模型** | 层3，动态键值对 `{key, value}`，不固定任何游戏专属字段名 |
| **游戏适配器** | 层4，每游戏一个适配包，将游戏数据转换为标准格式，不动内核 |
| **插件化模块** | 层2的子概念，按游戏品类按需加载的规则模块（crit/dodge/shield/distance_decay） |
| **全品类适配** | 从二游扩展到 MMORPG/卡牌/动作/MOBA/FPS/战棋的覆盖能力 |
| **商业双授权** | GPL（个人/非商用免费）+ 商业授权（企业/团队需购买） |
| **社区配置市场** | Web 平台，用户上传/下载/评分 `.calcpack` 适配包，内核 100% 本地计算 |
| **ECA** | Entity-Context-Action 三层设计模式（可选），用于表达任意游戏战斗规则 |
| **属性声明 Schema** | `attr_schema.json`，适配器声明自己的属性结构（名称/类型/来源/默认值），框架据此自动构建 DataContext |
| **CardRPG 适配器** | `framework/adapters/card_rpg/`，经典攻击-防御公式的卡牌RPG示例适配器，证明框架跨品类通用 |
| **DAG 模板库** | `framework/src/calc_framework/dag/templates.py`，可复用的子图模式 registry，内置 5 个通用模板（防御减伤/暴击倍率/钳制/百分比/等级成长），DAG JSON 中用 `"template"` 字段引用 |
| **搜索/枚举引擎** | `framework/src/calc_framework/search/`，通用搜索基础设施：SearchEngine[C, R] ABC / SearchConfig / TopNTracker / SearchCancelToken / run_parallel / SearchResult |
| **SearchEngine[C, R]** | `framework/src/calc_framework/search/engine.py` — 泛型 ABC，子类需实现 `generate_candidates()` / `evaluate()` / `score_key()`；基类提供 `run()` / `estimate_workload()` |
| **SearchConfig** | `top_n` / `max_workers` / `max_seconds` 通用搜索配置 dataclass |
| **EndfieldSearchEngine** | `calculation/search/adapter.py` — 终末地配装搜索适配器，包装 OptimizerTask 评估流水线，提供 `from_job()` 工厂方法 |
| **插件系统** | `framework/src/calc_framework/plugin/`，BasePlugin + PluginRegistry，3 内置插件（暴击/闪避/距离衰减），可注册变量/模板/函数 |
| **发布/分享工具** | `framework/src/calc_framework/publish/`，JSON Schema 校验 + catalog HTML 生成器 |
| **MOBA 适配器** | `framework/adapters/moba/`：通用 MOBA 伤害公式，AD/AP 加成 → 护甲/魔抗减伤 → 暴击判定 → 冷却缩减 → 攻速；含 `percent_of()` / `armor_mult()` 自定义函数 |
| **FPS 适配器** | `framework/adapters/fps/`：通用 FPS 武器伤害公式，基础伤害 × 距离衰减 × 部位倍率 × 穿透减伤 → 实际伤害；含 `le()` / `ge()` / `clamp()` / `lerp()` 自定义函数 |
| **DAGService** | DAG 求值服务的统一入口，通过 `evaluate(context)` 求值，返回 `DAGResult` |
| **DAGResult** | 包含 `outputs`（dict[str, float]）、`node_values`、`execution_order` 的数据类 |
| **注册函数** | 通过 `DAGService.register_function()` 注册自定义函数到沙箱，供 `expr` 节点调用 |
| **theme.json** | 主题定义，`ui/theme.json`：font（族/大小/粗细）、colors（primary/background/text 等）、spacing |
| **布局编辑器画布** | `tools/designer/layout_editor/canvas.py`：QGraphicsView 网格画布，支持网格列数/间距/吸附配置 |
| **碰撞检测** | `tools/designer/layout_editor/collision.py`：QGraphicsItem 矩形重叠实时检测 |
| **开发者 GUI 入口** | `python -m tools.designer`，独立进程，不依赖终末地包 |

## 通用计算框架（calc-framework）

| 术语 | 含义 |
|------|------|
| **框架目录** | `framework/`：独立 pip 包 `calc-framework`，zero 终末地依赖，位于仓库根 |
| **DAG 公式图** | `DAGGraph` — 有向无环图表达的公式网络（nodes + variables + subgraphs + outputs）；建图→拓扑排序→求值 |
| **DAG 节点** | 9 种类型：`const` / `var` / `unary` / `binary` / `condition` / `expr` / `user_input` / `call` / `subgraph` |
| **DAG 变量** | `DAGVariable` — 公式图中变量的元数据（type / source / default / description） |
| **DAG 输出** | `DAGOutput` — 指定图中哪个节点的值作为输出，可选 `format` 格式串（`.4f` / `.1f` / `.0%`） |
| **子图** | `DAGSubgraph` — 可复用的 DAG 片段，通过 `call` 节点在主图中实例化 |
| **DAG 沙箱** | AST 受限求值器（`sandbox.py`）：白名单函数、禁止属性访问/导入/循环；安全执行 `user_input` 节点的 Python 表达式 |
| **拓扑排序** | DAG 求值前的节点依赖排序（`engine.py`）；检测循环依赖 |
| **ComputeSheet** | `calc_framework.ui.compute_sheet.ComputeSheet` — 声明式计算表 QWidget：读 DAG + layout.json → 自动生成输入控件 + 计算/展示输出 |
| **Layout / Section** | `layout.json` 声明式排版：每个 `Section` 含 `name`、`inputs`（变量路径列表）、`outputs`（输出节点列表） |
| **布局编辑器** | `calc_framework.editor.LayoutEditor` — 从 DAG 编排 layout.json 的 API + CLI（`calc-layout`）+ PySide6 GUI |
| **DataContext** | `TypedDict` 定义的数据上下文 schema：`character` / `weapon` / `equipment` / `enemy` / `computed` / `user_input` 六区 |
| **DataContextLoader** | ABC 接口：实现 `load()` 方法，从游戏数据构建符合 schema 的变量字典 |
| **EndfieldContextLoader** | 终末地适配器实现，位于 `games/endfield/calc/dag_adapter/loader.py` |
| **AdapterPackage** | `calc_framework.config.adapter.AdapterPackage` — 从适配器目录加载 DAG + layout + context loader，零自定义缓存 |
| **DAG 适配器 (adapter.py)** | `games/endfield/calc/dag_adapter/adapter.py` — 将 DAG 引擎接入 zone_snapshot 计算链的桥接模块 |
| **控制规格** | `ControlSpec` — 声明输入控件的类型：`QLineEdit` / `QSpinBox` / `QDoubleSpinBox` / `QSlider` / `QCheckBox` / `QComboBox`8，带 min/max/step/choices/default 元数据 |
| **框架测试** | `[框架]` `python -m pytest tests/ -q` → **374 passed**（含 MOBA 8 + FPS 11 + CardRPG 21 适配器集成测试） |
| **包端测试** | `[包]` `python -m pytest tests/ -q` → **553 passed / 1 skipped / 9 subtests passed** |
| **DAG 沙箱限制** | `expr` 节点使用 AST 沙箱，禁止 `IfExp`（Python 三元表达式），只支持基本算术运算和已注册函数调用。条件分支用 `condition` 节点 |
| **`VarNode` 路径解析** | VarNode 通过 `_resolve_path(context, path)` 按点分隔路径在上下文中取值，需要嵌套字典结构 |
| **`AttributeSchema`** | 属性声明 Schema，有效 `source` 只允许 `character/weapon/equipment/enemy/computed`，不支持 `user_input` |
| **`condition` 节点** | DAG 引擎内置条件分支节点，根据 `cond` 节点的真假值选择 `true_val` 或 `false_val` |
