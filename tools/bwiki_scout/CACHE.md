# BWIKI 本地缓存说明

爬取结果**默认保存在本机**，路径固定为：

```
tools/bwiki_scout/output/
├── manifest.json      # 条目列表、更新时间、缓存统计
├── raw/<页面名>/      # wikitext.txt、html.html、meta.json（可复用）
├── reports/           # 对比报告（每次 scout 会刷新）
└── parsed/            # parse_draft.py 生成的 JSON 草案
```

## 为何不进 Git？

`output/` 已在根目录 `.gitignore` 中忽略（约数 MB～数十 MB 的 Wiki 原文）。原因：

- 避免把第三方 Wiki 全文推上 GitHub（许可与体积）
- 每台维护者机器各保留一份本地缓存即可

**换电脑或删目录后**需要重新跑 `scout.py`；可把整个 `output/` 文件夹复制备份（U 盘、网盘、另一台机器同路径）。

## 如何少爬网？

| 命令 | 是否访问 Wiki API |
|------|-------------------|
| `python tools/bwiki_scout/scout.py` | 仅拉取 `raw/` 里**没有**的页面；已有 wikitext 的页直接读盘 |
| `python tools/bwiki_scout/scout.py --refresh` | **忽略本地缓存**，强制从 Wiki 重新拉取全部页面（耗时较长） |
| `python tools/bwiki_scout/parse_draft.py` | **不访问网络**，只读 `output/raw` + `manifest.json` |
| `python tools/bwiki_scout/compare_stats.py` | **不访问网络**，重算 `reports/stats_diff.md` |
| `python tools/bwiki_scout/sync_operators.py` | **不访问网络**（预览）；`--apply` 写本地 JSON/seed |
| `python tools/bwiki_scout/sync_weapons.py` | **不访问网络**（预览）；`--apply` 写本地 JSON/seed |

再次执行 `scout.py` 时，终端会打印「本地复用 N，新拉取 M」。若条目无变化，M 应为 0，几秒内完成。

## 何时会丢缓存？

- 手动删除 `tools/bwiki_scout/output/`
- `git clean -fdx`（会清掉被 ignore 的文件；日常 `github_download` 的 `git clean -fd` **不会**删 ignore 目录）
- 重装系统未备份该目录

## 查看当前是否有缓存

```powershell
# 仓库根目录
Get-ChildItem tools\bwiki_scout\output\raw -Directory | Measure-Object
Get-Content tools\bwiki_scout\output\manifest.json -Encoding utf8 | Select-Object -First 15
```
