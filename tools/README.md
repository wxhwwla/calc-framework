# 仓库维护工具（`tools/`）

**`[工具]`** 目录：在 **仓库根目录** `[根]` 执行下列命令。

与 **`[包]`** 内 `games/endfield/scripts/`（反推 CLI、seed 录入）是两套路径，勿混用。日常命令见 [docs/操作指令集.md](../docs/操作指令集.md) §0、§9。

| 子目录 | 用途 | 典型命令 |
|--------|------|----------|
| `data_sandbox/` | 数据沙箱 — 隔离测试自定义游戏数据 | 见下表 |
| `bwiki_scout/` | BWIKI 侦察、对比、同步到本地 JSON/seed | 见下表 |
| `wiki_scout/` | 模块化 Wiki 数据采集（华法琳 / 无尽的拉格朗日） | `python -m tools.wiki_scout list` |
| `audit/` | 一次性审计 Issue 脚本 | `.\tools\audit\create_audit_issues.ps1` |
| `calc_mcp/` | MCP 计算器构建服务器（供宿主 AI 调用） | `python -m tools.calc_mcp --project-dir .` |

**仓库维护工具**（直接在 `[根]` 执行）：

| 命令 | 用途 | 说明 |
|------|------|------|
| `python tools/quality/check_layout.py` | 仓库布局门禁（目录宽度、文件行数） | 见 `check_layout.py` |
| `python -m tools.quality.search_benchmark` | 搜索性能基准（固定 973,728 组合） | Rust 开/关耗时、内存、TopN、取消/续跑；见 [P3-01 结果](../docs/P3-01-搜索性能基准结果.md) |
| `python tools/quality/run_scancode.py` | 权威许可证/版权扫描（逐个目录，16 进程） | 输出 `scan_report.json` |
| `python tools/quality/check_code_origin.py` | 轻量 AI 代码来源/版权检测 | 1 秒出结果，50 MB 内存 |
| `python tools/quality/generate_secrets_baseline.py generate` | 重建 `.secrets.baseline`（detect-secrets） | CI 与 pre-commit 共用 |
| `python tools/quality/generate_secrets_baseline.py verify` | 校验无新增密钥（Security Audit CI 同款） | 失败时需审查后 regenerate |
| `python tools/quality/npm_audit_gate.py --cwd web/frontend` | npm audit 门禁（过滤已知误报） | Security Audit CI 同款 |
| `python scripts/tools/devtool.py check-origin` | 同上，通过 devtool 入口 | `--ci --skip git-diff` 等参数透明传递 |
| `python -m tools.data_sandbox.sandbox --help` | 数据沙箱 CLI — 隔离测试自定义游戏数据 | 见下表 |

> **两套扫描工具的关系**：`check_code_origin.py` 做快速检查（SPDX/版权头），`run_scancode.py` 做权威审查（1000+ 许可证数据库）。日常用前者，发布前用后者。

**`data_sandbox/` 常用命令**（均在 `[根]` 执行）：

| 命令 | 说明 |
|------|------|
| `python -m tools.data_sandbox.sandbox validate <file>` | 校验 JSON 文件格式是否符合 EntitySchema |
| `python -m tools.data_sandbox.sandbox test <file>` | 运行基本健全性测试（命名/技能/倍率） |
| `python -m tools.data_sandbox.sandbox report <file> [-o output.md]` | 生成完整 Markdown 报告（校验+测试+差异） |
| `python -m tools.data_sandbox.sandbox diff <file> <reference>` | 对比自定义数据与本地参考数据 |

> 所有操作在隔离环境中执行，**不会修改任何真实数据文件**。

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

**`wiki_scout/` 常用命令**（均在 `[根]` 执行）：

| 命令 | 说明 |
|------|------|
| `python -m tools.wiki_scout list` | 列出已注册数据源 |
| `python -m tools.wiki_scout run all` | 抓取并解析全部数据源 |
| `python -m tools.wiki_scout run warfarin --limit 5` | 华法琳 Wiki：终末地干员/武器/装备 |
| `python -m tools.wiki_scout run wjdlglr` | 无尽的拉格朗日 Wiki：225 艘舰船及武器 |
| `python -m tools.wiki_scout fetch <provider> --refresh` | 仅抓取原始响应（写入 `raw.json`） |
| `python -m tools.wiki_scout parse <provider>` | 仅解析已有 `raw.json`（离线） |

- 产物：`tools/wiki_scout/output/<provider>/{raw.json,<provider>.json}`（已 gitignore）
- 新增数据源：`providers/` 下继承 `BaseProvider`（`fetch` + `parse`），用 `@register_provider` 注册，并在 `providers/__init__.py` 导入
- 测试：`python -m pytest tools/tests -q -k wiki_scout`
- 字段口径与扩展说明：[wiki_scout/README.md](wiki_scout/README.md)

GitHub 上传/下载脚本仍在 `[根]`：`github_upload_module.py`、`github_download_module.py`。
