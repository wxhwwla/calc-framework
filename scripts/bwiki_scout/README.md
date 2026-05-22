# BWIKI 侦察与解析草案

从 [终末地 BWIKI](https://wiki.biligame.com/zmd/) 拉取干员 / 武器 / 装备数据，对比本地 `characters.json`、`weapons.json`，并生成阶段 B 解析草案。

操作速查见 [`docs/操作指令集.md`](../../docs/操作指令集.md) §9；许可见 [`DATA_LICENSE`](../../DATA_LICENSE)。

## 阶段 C（侦察）

```powershell
# 仓库根目录
python scripts/bwiki_scout/scout.py

# 调试：每类只拉 5 条
python scripts/bwiki_scout/scout.py --limit 5
```

输出目录（已 gitignore）：`scripts/bwiki_scout/output/`

| 路径 | 说明 |
|------|------|
| `manifest.json` | 条目列表与来源统计 |
| `raw/<页面>/` | `meta.json`、`wikitext.txt`、`html.html` |
| `reports/summary.md` | 摘要（含 JSON 探测） |
| `reports/schema_diff.md` | 字段结构对照 |
| `reports/names_diff.md` | 名称对齐 |
| `reports/samples/` | Wiki / 本地样例 |

## 阶段 B（解析草案）

在阶段 C 完成后：

```powershell
python scripts/bwiki_scout/parse_draft.py
```

生成 `output/parsed/operators.json`、`weapons.json`、`equipment.json`（**不覆盖**正式数据文件）。

## 测试

```powershell
cd endfield_damage_calculator
python -m pytest tests/test_bwiki_scout.py -q
```

## 说明

- Wiki 数据来自 **MediaWiki API**，通常**不是**现成 JSON 文件。
- 阶段 B 当前仅做模板参数抽取，等级曲线等仍需后续映射规则。
- 使用 Wiki 内容须遵守署名、站点条款与 CC 要求；产出受 [`DATA_LICENSE`](../../DATA_LICENSE) 约束（商用不可用本流程数据）。
- 合规说明：[`docs/数据来源与许可.md`](../../docs/数据来源与许可.md)、[`docs/合规自查清单.md`](../../docs/合规自查清单.md)。
