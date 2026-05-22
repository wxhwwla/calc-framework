# 仓库维护工具（`tools/`）

**`[工具]`** 目录：在 **仓库根目录** `[根]` 执行下列命令。

与 **`[包]`** 内 `endfield_damage_calculator/scripts/`（反推 CLI、seed 录入）是两套路径，勿混用。日常命令见 [docs/操作指令集.md](../docs/操作指令集.md) §0、§9。

| 子目录 | 用途 | 典型命令 |
|--------|------|----------|
| `bwiki_scout/` | BWIKI 侦察、对比、同步到本地 JSON/seed | 见下表 |
| `audit/` | 一次性审计 Issue 脚本 | `.\tools\audit\create_audit_issues.ps1` |

**`bwiki_scout/` 常用命令**（均在 `[根]` 执行）：

| 步骤 | 命令 | 说明 |
|------|------|------|
| 拉取/续跑缓存 | `python tools/bwiki_scout/scout.py` | 写入 `output/raw/`；干员含 `*/详细数据` |
| 草案解析 | `python tools/bwiki_scout/parse_draft.py` | 不覆盖正式 JSON |
| 数值对比报告 | `python tools/bwiki_scout/compare_stats.py` | 离线重算 `reports/stats_diff.md` |
| 同步干员（预览） | `python tools/bwiki_scout/sync_operators.py` | 属性 + 技能倍率 |
| 同步武器（预览） | `python tools/bwiki_scout/sync_weapons.py` | 需 Wiki 含 rank 成长块 |
| 写入本地 | 上述命令加 `--apply` | 更新 JSON 与 `seed_characters.py` / `seed_weapons.py` |

- 缓存目录：`tools/bwiki_scout/output/`（已 gitignore，勿提交）
- 详细说明：[bwiki_scout/README.md](bwiki_scout/README.md)、[CACHE.md](bwiki_scout/CACHE.md)

GitHub 上传/下载脚本仍在 `[根]`：`github_upload_module.py`、`github_download_module.py`。
