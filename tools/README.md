# 仓库维护工具（`tools/`）

**`[工具]`** 目录：在 **仓库根目录** `[根]` 执行下列命令。

与 **`[包]`** 内 `endfield_damage_calculator/scripts/`（反推 CLI、seed 录入）是两套路径，勿混用。日常命令见 [docs/操作指令集.md](../docs/操作指令集.md) §0、§9。

| 子目录 | 用途 | 典型命令 |
|--------|------|----------|
| `bwiki_scout/` | BWIKI 数据侦察：拉取 Wiki、解析草案、对比本地 JSON | `python tools/bwiki_scout/scout.py` |
| `audit/` | 一次性审计 Issue 脚本 | `.\tools\audit\create_audit_issues.ps1` |

- 侦察产出：`tools/bwiki_scout/output/`（已 gitignore，勿提交）
- 模块说明：[bwiki_scout/README.md](bwiki_scout/README.md)

GitHub 上传/下载脚本仍在 `[根]`：`github_upload_module.py`、`github_download_module.py`。
