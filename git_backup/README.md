# 本地 `.git` 快照备份

上传脚本在 **Minor 级别上传**（`--minor` 或交互输入 `M`）时，会在 commit 之前把仓库根目录的 `.git` 复制到本目录下的 `snapshots/`。

## 何时自动备份

| 触发 | 是否备份 |
|------|----------|
| `python github_upload_module.py --minor` | 是 |
| 交互上传时选择 **M / minor** | 是 |
| 默认 Patch（回车） | 否 |
| `--no-bump` 纯补推 | 否 |
| `--no-git-backup` | 否（显式跳过） |

## 目录结构

```text
git_backup/
├── README.md          ← 本说明（纳入 Git）
└── snapshots/         ← 快照（不纳入 Git，见 .gitignore）
    └── 20260603T120000Z_v3.20.5_minor/
        ├── MANIFEST.json
        └── .git/        ← 完整复制
```

默认最多保留 **5** 份 Minor 快照，超出时删除最旧的。

## 恢复步骤（误删工作区 `.git` 时）

1. **关闭** Cursor / IDE（避免占用 `.git` 文件）
2. 删除仓库根目录下损坏或空的 `.git` 文件夹
3. 从 `snapshots/` 中选最新一版，将其中的 `.git` **整目录复制**回仓库根
4. 在仓库根执行 `git status` 确认正常
5. 若仍缺远程引用：`git fetch origin main`

`MANIFEST.json` 里记录了备份时的 `_VERSION` 与 `HEAD` commit，便于核对。

## 红线（必读）

| 禁止 | 原因 |
|------|------|
| **不要把 `snapshots/` 提交到 GitHub** | 体积巨大，且含完整对象库；已在 `.gitignore` 排除 |
| **不要用备份代替 push** | 远程 GitHub/Gitee 仍是协作与灾备主副本；备份仅救本地 |
| **Agent 不得擅自删除 `snapshots/`** | 等同丢弃本地 Git 历史缓存；删前须人类确认 |
| **不要在备份进行中强行杀上传脚本** | 可能留下不完整快照目录，可手动删掉该子目录后重跑 |
| **不要用 `github_download_module.py`（覆盖本地）时期望备份能回滚未 push 改动** | 下载脚本会 `reset --hard`；未 push 的 commit 只能靠快照或 stash |

## 磁盘占用

快照约为 `.git` 体积的 **1 倍/次**（Minor 上传才写）。仓库历史越大，单次备份越大。请定期确认磁盘空间；旧快照由脚本自动裁剪至 5 份。

## 跳过备份

```powershell
python github_upload_module.py --minor --no-git-backup
```

仅当你确认磁盘不足或已有其他备份（如 `git bundle`）时使用。
