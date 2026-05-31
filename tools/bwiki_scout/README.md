# BWIKI 侦察与解析草案

从 [终末地 BWIKI](https://wiki.biligame.com/zmd/) 拉取干员 / 武器 / 装备数据，对比本地 `characters.json`、`weapons.json`，并可选择将差异写回正式数据与 seed 脚本。

操作速查见 [`docs/操作指令集.md`](../../docs/操作指令集.md) §9；领域术语见 [`CONTEXT.md`](../../CONTEXT.md)；许可见 [`DATA_LICENSE`](../../DATA_LICENSE)。

## 推荐流程

```
scout.py（拉取/续跑 raw 缓存）
    → compare_stats.py（可选：干员 1–90 级对比报告）
    → parse_draft.py（生成 parsed/equipment.json 草案）
    → sync_all.py（干员+武器+装备一键预览/写入）
```

默认**不**改正式 JSON；只有加 `--apply` 才会覆盖 `characters.json` / `weapons.json` 并更新 `seed_characters.py` / `seed_weapons.py`。

## 阶段 C（侦察）

```powershell
# 仓库根目录
python tools/bwiki_scout/scout.py

# 调试：每类只拉 5 条
python tools/bwiki_scout/scout.py --limit 5
```

输出目录（**保存在本机**，已 gitignore，不进 GitHub）：`tools/bwiki_scout/output/`

详见 **[CACHE.md](CACHE.md)**：续跑规则、备份建议、何时会丢缓存。

| 路径 | 说明 |
|------|------|
| `manifest.json` | 条目列表与来源统计 |
| `raw/<页面>/` | `meta.json`、`wikitext.txt`、`html.html` |
| `reports/summary.md` | 摘要（含 JSON 探测） |
| `reports/schema_diff.md` | 字段结构对照 |
| `reports/names_diff.md` | 名称对齐 |
| `reports/stats_diff.md` | **逐级数值对比**（`*/详细数据` wikitext vs 本地） |
| `reports/samples/` | Wiki / 本地样例 |

## 阶段 B（解析草案）

在阶段 C 完成后：

```powershell
python tools/bwiki_scout/parse_draft.py
```

生成 `output/parsed/operators.json`、`weapons.json`、`equipment.json`（**不覆盖**正式数据文件）。用于粗看模板参数，**不能**替代下面的 `sync_*.py` 写回逻辑。

### 逐级数值对比（详细数据子页）

`scout.py` 会为每名干员额外拉取 **`干员名/详细数据`**（wikitext 模板 `干员/逐级等级`，含 1–90 级攻击力等）。  
已有缓存时只补拉缺失页：

```powershell
python tools/bwiki_scout/scout.py
python tools/bwiki_scout/compare_stats.py   # 仅离线重算报告
```

查看 `output/reports/stats_diff.md`。

## 同步到本地 JSON / seed（以 Wiki 为准）

### Wiki → 本地映射

| 写入目标 | Wiki 来源 | 反推模块 |
|----------|-----------|----------|
| 干员 `力量/敏捷/智识/意志/基础攻击力` | `raw/<干员>/详细数据/wikitext.txt` | `wiki_sync.fit_growth_params_from_curve` |
| 干员 `战技倍率` / `连携技倍率` / `终结技倍率` | `raw/<干员>/html.html` 技能 tab 中「伤害倍率」行 | `skill_tables` + `fit_skill_formula` |
| 武器 `基础攻击力` | `raw/<武器>/wikitext.txt` 的 1 级与满级端点 | `weapon_wiki.fit_weapon_base_atk_from_endpoints` |
| 武器 `normal_skills`（词条 1/2 与无条件第三技能） | `词条1/2rank1–9`；`词条3内容` + `词条3副1rank1–9`（视模板） | 写入 `normal_skills[]`（`zone` 1–3、`effect`、`curve[9]`） |
| 武器 `special_skills`（有条件特殊能力） | `词条3副1–4rank…`（视武器有无无条件第三技能） | 写入 `special_skills[]`（`condition`、`effect`、`curve`、`max_stack`） |

**注意**：`sync_weapons.py` / `add_weapon.py` 仍可能产出 **legacy** 字段（顶层 `xxx+`、`特殊能力1/2`）。正式 `weapons.json` 须为 `normal_skills` + `special_skills`；`--apply` 写回后请执行：

```powershell
python tools/migrate_weapon_skills_schema.py --apply
python -m pytest games/endfield/tests/test_game_data_contract.py -q
```

**武器限制**：须存在 `基础攻击力`、`满级基础攻击力` 与 `词条1rank1` 等字段；仅模板简介、无 rank 表的武器（如部分 Wiki 简页）会跳过。

### 命令

**干员** → `characters.json` + `games/endfield/scripts/seed_characters.py`：

```powershell
python tools/bwiki_scout/sync_operators.py
python tools/bwiki_scout/sync_operators.py --apply
python tools/bwiki_scout/sync_operators.py --apply --only 佩丽卡
python tools/bwiki_scout/sync_operators.py --new          # 本地尚无、且 raw 齐全的新干员
```

**武器** → `weapons.json` + `games/endfield/scripts/seed_weapons.py`：

```powershell
python tools/bwiki_scout/sync_weapons.py
python tools/bwiki_scout/sync_weapons.py --apply
python tools/bwiki_scout/sync_weapons.py --apply --only 逐鳞3.0
python tools/bwiki_scout/sync_weapons.py --new              # 预览：可导入的新武器
python tools/bwiki_scout/sync_weapons.py --new --apply      # 写入 JSON + seed_weapons.py
```

默认只处理 **已在** `characters.json` / `weapons.json` 中的名称（与 Wiki 对比后更新）。加 `--new` 会从 `manifest.json` 并入本地缺失、且 `output/raw` 缓存可反推的条目（武器须含 `词条1rank1` 等成长块）。

**装备** → `games/endfield/character_weapon_equipment/equipment_data/equipments.json`：

Wiki 模板字段：`装备种类`（**护甲 / 护手 / 配件**）、`所属套组`、`装备套组效果`、`主词条` / `属性词条N`。

```powershell
python tools/bwiki_scout/scout.py --only-kind equipment
python tools/bwiki_scout/parse_draft.py
python tools/bwiki_scout/sync_equipments.py
python tools/bwiki_scout/sync_equipments.py --apply
```

**一键同步（干员+武器+装备）**：

```powershell
python tools/bwiki_scout/sync_all.py
python tools/bwiki_scout/sync_all.py --apply
python tools/bwiki_scout/sync_all.py --apply --new
python tools/bwiki_scout/sync_all.py --apply --only-operators 秋栗 --only-weapons 逐鳞3.0
```

## 模块文件

| 文件 | 职责 |
|------|------|
| `scout.py` | 图鉴 + 分类拉取，写入 `output/raw` |
| `parse_draft.py` | 阶段 B 模板参数草案 |
| `compare_stats.py` | 干员详细页 vs 本地 `stats_diff.md` |
| `detail_levels.py` | 解析 `干员/逐级等级` wikitext |
| `skill_tables.py` | 解析干员主页 HTML 技能倍率表 |
| `weapon_wiki.py` | 解析武器 wikitext 与反推 seed 结构 |
| `wiki_sync.py` | 干员/武器同步核心、`seed_*` 读写 |
| `import_targets.py` | manifest → 同步目标（含 `--new`） |
| `equipment_wiki.py` | 装备 wikitext → 本地 JSON（`装备种类` 等与 Wiki 对齐） |
| `sync_operators.py` / `sync_weapons.py` / `sync_equipments.py` | 分项 CLI 入口 |
| `sync_all.py` | 一键串联干员/武器/装备同步 |
| `storage.py` | `raw/` 读写与续跑 |
| `config.py` | 路径、API、本地 JSON 位置 |

## 测试

```powershell
cd games/endfield
python -m pytest tests/test_bwiki_scout.py tests/test_wiki_sync.py -q
```

`test_wiki_sync.py` 使用 `tools/bwiki_scout/output/raw/` 离线样例（如 `秋栗`、`逐鳞3.0`），无网络。

## 说明

- Wiki 数据来自 **MediaWiki API**，通常**不是**现成 JSON 文件。
- 运行时 GUI 仍读**预烘焙**本地 JSON；BWIKI 流程用于录入、校对与批量更新。
- 使用 Wiki 内容须遵守署名、站点条款与 CC 要求；产出受 [`DATA_LICENSE`](../../DATA_LICENSE) 约束（商用不可用本流程数据）。
- 合规说明：[`docs/数据来源与许可.md`](../../docs/数据来源与许可.md)、[`docs/合规自查清单.md`](../../docs/合规自查清单.md)。
