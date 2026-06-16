# MVP 搜索验收说明（实验功能）

> 适用范围：单技能全量遍历、MVP 导出/续跑、并行搜索与装备 BWIKI 同步后的 GUI 入口。  
> 接续上下文见 [`会话接续手册.md`](会话接续手册.md)；操作命令见 [`操作指令集.md`](操作指令集.md) §2.3、§7。

## 1. 功能总览

已落地能力：

- 15 乘区单段伤害引擎（默认不暴击，支持期望/必暴）
- 外部效果统一结构（含未知标签兜底记录）
- 装备四格装配与三件套触发（**护甲 / 护手 / 配件×2**，与 Wiki「装备种类」一致）
- 单技能最优搜索（TopN、候选筛选、基础剪枝）
- **流式任务生成** + **有界并行**（不一次性物化/提交全部 future）
- SQLite 续跑：**批量**标记 `processed`、结束时仅写入 **TopN** 到 `scores`
- 结果导出：Top JSON/CSV（`result_export.py`）
- 多技能加权总伤（快速预览 + **开启手动次数时的全量/MVP TopN**）
- GUI：**预计组合数/耗时**、并行线程与本机 CPU 说明、进度 ETA、取消、结果大窗

## 2. 代码入口

| 模块 | 路径 |
|------|------|
| 单段伤害 | `calculation/damage_engine.py` |
| 装备模型 | `calculation/equipment_system.py` |
| 流式搜索计划 | `calculation/loadout_optimizer.py`（`build_optimizer_search_plan`、`iter_optimizer_tasks`） |
| 有界并行 | `calculation/parallel_search.py` |
| 并行（无续跑） | `calculation/search_runner.py` |
| 续跑存储 | `calculation/search_persistence.py` |
| 工作量/耗时预估 | `calculation/search_estimate.py` |
| 导出 | `calculation/result_export.py` |
| MVP 串联 | `calculation/mvp_pipeline.py` |
| 多技能 | `calculation/multi_skill_optimizer.py` |
| 导出目录 | `gui_design/search_export_paths.py`（`get_application_dir()` → `search_output/`） |
| 并行/进度文案 | `gui_design/search_settings.py` |
| 固定配装 UI | `gui_design/fixed_loadout_controls.py` |
| 多技能全量评分 | `calculation/multi_skill_search_eval.py`、`search_task_evaluator.py` |
| GUI | `gui_design/gui.py`、`gui_layout.py`（双页签：计算页五列 + 高级页三列） |
| 结果大窗 | `gui_design/search_results_view.py` |

## 3. GUI 布局（2026-05-24）

**双页签**：**计算页**（日常选装与乘区）与 **高级页**（全量搜索 / 多技能 / 工具）。

**计算页** — 五列 `APP_COLUMN_WEIGHTS = (0, 0, 1, 1, 0)`，`ZONE_COLUMN_MINSIZE = 340`：

| 列 | 内容 |
|----|------|
| 0 | 角色选择（普通容器；信赖等在「高级参数」折叠内） |
| 1 | 武器选择（普通容器；词条滑块在「高级参数」折叠内） |
| 2 | 角色属性 |
| 3 | 武器属性 |
| 4 | 右侧乘区（**固定宽**）+ 快速「确认选择」/「前往高级页」 |

**高级页** — 原底栏三列：操作（确认、模式、**工具与分享**）| 全量搜索（范围、**固定配装 0–4**、预估、遍历/MVP）| **多技能次数**（**段级** + 手动开关）

## 4. GUI 使用步骤

### 4.1 全量遍历（推荐，弹窗看 TopN）

1. 启动：`python scripts/main_launcher.py`（选终末地，或发布文件夹内 exe）
2. 在 **计算页** 选择角色、武器、技能；点击「确认选择」（乘区下方或高级页均可）
3. 切换到 **高级页**，在 **全量搜索** 区设置：
   - **武器候选范围** / **装备范围**
   - **固定配装**：勾选 0–4 件具体装备；未勾选部位全部遍历
   - （可选）**多技能** 开「使用手动次数」并填段级次数 → TopN 按加权总伤
   - 查看 **预计组合数 / 预计耗时**；阅读 **并行线程** 说明
4. 点击 **`全量遍历（弹窗）`** 或窄屏下的 **`全量遍历`**（无需选手动导出目录）
5. 若预计 ≥ 2 分钟，会弹出确认框
6. 进行中：状态栏显示 `已处理/总数`、剩余与总预计时间；可点 **取消搜索**
7. 结束后弹出约 **920×720** 结果窗；底部可见导出路径

**导出位置（勿再找 C 盘 Temp）：**

| 运行方式 | 路径 |
|----------|------|
| 开发 | `[包]/search_output/full_search_<时间戳>/` |
| 打包 exe | `dist/Game Calc Platform/search_output/full_search_<时间戳>/`（与 exe **同级**） |

内含 `search_runs.db`、`mvp_exports/` 等。

### 4.2 MVP 搜索并导出（要文件时用）

1. 同上配置范围与并行（在 **高级页**）
2. 点击 **`MVP搜索导出`**（窄屏下 **`MVP导出`**）
3. 选择目录（对话框默认打开 `search_output/`）；**取消选择**则自动在 `search_output/mvp_search_<时间戳>/` 创建
4. 完成后弹窗 + 写入 `search_runs.db`、`mvp_exports/top_results.json` 等

### 4.3 并行线程怎么选？

- **自动 (1 线程)**（默认）：Rust job 批量已摊销 FFI，**单 worker 内联 batch 最快**（实测 97 万组合约 1 分钟）
- 本机会显示 **物理核心 / 逻辑线程**；下拉仍可选手动数字，但在 job 批量路径下 **有效 worker 仍为 1**（避免 GIL/锁导致更慢）
- 实验多 worker：`CALC_SEARCH_BATCH_POOL=1` 环境变量（可能更慢，仅供对比）
- 组合规模 ≈ `武器数 × 护甲 × 护手 × 配件²`；建议先用 **当前武器** + **仅套装装备** 试跑

### 4.4 装备数据

「单技能遍历(快速预览)」仅在右栏**采样**（每部位约 2 件），**不是**全量。

全量前请保证 `equipments.json` 三部位非空（打包发布已随包复制该文件）：

```powershell
# [根]
python tools/bwiki_scout/sync_equipments.py --apply
```

## 5. 命令行验收

在 `[包]` 目录：

```powershell
python -m pytest tests/ -q
```

当前基线见 [`docs/会话接续手册.md`](会话接续手册.md) §5（全量 **393 passed**, 9 subtests）。

重点模块：

```powershell
python -m pytest tests/test_damage_engine.py tests/test_equipment_system.py -q
python -m pytest tests/test_loadout_optimizer.py tests/test_streaming_optimizer.py -q
python -m pytest tests/test_search_runner.py tests/test_search_persistence.py -q
python -m pytest tests/test_search_estimate.py tests/test_frozen_search_export_paths.py -q
python -m pytest tests/test_mvp_pipeline.py tests/test_search_settings.py -q
```

## 6. 打包发布

```powershell
cd games/endfield
python build.py
```

产出 `dist/终末地伤害计算器/` 须整夹分发，内含：

- `终末地伤害计算器.exe`
- `character_weapon_equipment/**`（含 **`equipments.json`**）
- `发布说明.txt`（含 `search_output/`、并行线程说明）
- 首次搜索后生成 **`search_output/`**（与 exe 同级）

详见 [`操作指令集.md`](操作指令集.md) §7、[`数据来源与许可.md`](数据来源与许可.md) §七。

## 7. SQLite 查看（仅链接）

- [DB Browser for SQLite](https://sqlitebrowser.org/dl/)
- [SQLite GUI by Anton Zhiyanov](https://antonz.org/sqlite-gui/)

## 8. GUI 已接入 vs 仅后端

| 能力 | GUI | 说明 |
|------|-----|------|
| 单段 15 乘区 | 是 | 「单段伤害计算」 |
| 乘区快照 | 是 | 「乘区快照」 |
| 单技能快速预览 | 是 | 采样，非全量 |
| 单技能全量 + 弹窗 | 是 | 「全量遍历(弹窗结果)」 |
| 预计组合数/耗时 | 是 | 「计算与搜索」列 |
| 并行线程 + CPU 说明 | 是 | 默认自动=1 worker；显示物理核心/逻辑线程 |
| Top 条数 / 取消 / ETA | 是 | 同列 |
| MVP 导出 + 续跑 | 是 | 「实验：MVP搜索并导出」 |
| 导出到 search_output | 是 | 开发/打包均非 C 盘 Temp |
| 多技能加权全量 | 是 | 开「使用手动次数」后全量/MVP 按 Σ(单段×次数) |
| 固定配装 0–4 | 是 | 高级页勾选部位 + 选装备 |
| 暴击模式 | 否 | 搜索固定不暴击 |
| 敌方防御/抗性等 | 否 | 后端 `DamageContext` |
| 全量 Top 分项伤害 | 否 | 弹窗仅显示加权总伤/单段伤害数值 |

## 9. 已知限制与反馈

- 实验入口；敌方面板、全量结果分项展示等未做完
- **Bug / 建议**：GitHub **Issues → New issue**（模板见 [`.github/ISSUE_TEMPLATE/`](../.github/ISSUE_TEMPLATE/) 与 [`agents/issue-tracker.md`](agents/issue-tracker.md)）
- 耗时预估为粗估（含批量写库经验值），跑起来后「剩余时间」更准
- 续跑时 `get_processed_keys` 仍会一次加载已处理 key 集合（超大续跑可再优化）
- 装备数据质量依赖 BWIKI 同步与 `infer_equipment_slot` 规则
