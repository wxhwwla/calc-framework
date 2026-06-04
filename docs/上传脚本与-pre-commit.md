# 上传脚本与 pre-commit（必读）

> **谁应读**：维护者上传 GitHub 前；Agent 改 `scripts/tools/github_upload_module.py`、`scripts/_version.py`、`.pre-commit-config.yaml` 或帮用户排障上传失败时。  
> **命令速查**：[`docs/操作指令集.md`](操作指令集.md) §5。  
> **架构接缝**：[`docs/会话接续手册.md`](会话接续手册.md) §4.149–§4.155。

---

## 1. 日常命令

| 命令 | 用途 |
|------|------|
| `python github_upload_module.py --check` | 仅自检（rebase/merge/断历史），不 commit/push |
| `python github_upload_module.py` | 有业务改动：bump + 总结块 + pre-commit + commit + push |
| `python github_upload_module.py --no-bump` | **补推**（已有未推送 commit，或显式跳过 bump） |
| `python github_upload_module.py --minor` | 第二位 +1；commit 前备份 `.git` → `git_backup/snapshots/` |

**入口**：优先 `[根]/github_upload_module.py`（subprocess → `scripts/tools/github_upload_module.py`，`cwd=仓库根`）。  
**禁止**裸 `git commit` + `git push` 代替上传脚本。

---

## 2. 脚本行为（勿误解为 bug）

| 行为 | 说明 |
|------|------|
| 仅 `git add` 变更路径 | 不用 `git add .`，避免 CRLF 全仓库脏改动被一并提交 |
| 落后 0 时跳过 pull/stash | 已与 `origin/main` 同步时不 pull，避免 Windows 上无意义的 stash |
| pre-commit 最多 2 轮 | 见 §3 |
| push 成功删总结块 | 失败则保留 `_version.py` 底部块；**pre-commit/commit 失败会自动回滚 bump 与总结块** |
| PowerShell 红色 Git 输出 | Git 写 stderr，非失败；看末尾 `[完成]` / exit code |

---

## 3. pre-commit：两种 Failed

### 3.1 可自愈（第 1 轮 Failed → 第 2 轮应 Passed）

钩子 **自动改文件** 后故意返回非零：

- `ruff-format`
- `mixed-line-ending`
- （有时）`trim trailing whitespace` / `fix end of files`

上传脚本会 **重新 `git add` 同一批路径** 再跑第 2 轮。  
**看到 Failed 不等于上传失败**；以第 2 轮全 Passed + `[成功] 推送完成` 为准。

手动提交时若 `mixed-line-ending` Failed：对该文件再 `git add` 一次后重提。

### 3.2 真失败（不会靠第 2 轮解决）

- **`ruff-lint` 行显示 Failed**（如 `F821`/`F822` 未定义名）→ 必须改代码
- 两轮后仍 Failed → `[错误] pre-commit 未通过`

**误判教训（§4.153）**：不能因输出里 **任意位置** 出现 `Failed` 就当作 `ruff-lint` 失败（`ruff-format` / `mixed-line-ending` 也会 Failed）。脚本现 **只检查以 `ruff-lint` 开头且含 Failed 的那一行**。

### 3.3 可自愈 vs 真失败对照

| 输出 | 含义 | 脚本行为 |
|------|------|----------|
| `ruff-lint ... Passed` + `ruff-format ... Failed` | 正常，第 1 轮 | re-add → 第 2 轮 |
| `ruff-lint ... Failed` | 代码错误 | **立即中止**，提示手修 |
| 第 2 轮全 Passed | 成功 | 继续 commit |

本地修复流程：

```powershell
pre-commit run --files <路径1> <路径2> ...
git add <被钩子改动的文件>
python github_upload_module.py
```

---

## 4. `scripts/_version.py` 总结标记（`[SEV-HIGH]`）

| 常量 | 正确写法（模块级） |
|------|-------------------|
| `SUMMARY_BEGIN` | `SUMMARY_BEGIN = _UPLOAD_SUMMARY_BEGIN` |
| `SUMMARY_END` | `SUMMARY_END = _UPLOAD_SUMMARY_END` |

字符串值均为 `"# --- BEGIN UPLOAD_SUMMARY ---"` / `"# --- END UPLOAD_SUMMARY ---"`（由 `_UPLOAD_SUMMARY_*` 定义）。

**禁止** `SUMMARY_BEGIN = ""` 或缺少 `SUMMARY_END =` 行 → `ruff-lint` F821/F822（`__all__` 导出未定义名），上传 commit 被取消。

### 4.1 易误判：文档同批 ≠ 文档致错（§4.155）

上传总结常同时列出 `docs/*.md` 与 `scripts/_version.py`。pre-commit 报 **`F822 SUMMARY_END`** 时，根因几乎总在 **`_version.py` 顶部两行赋值**，与 md 正文无关。勿把「刚补了文档就 Failed」理解成 markdown 或 pre-commit 误伤文档。

### 4.2 实现与防护（2026-06-04 §4.155 加固）

| 机制 | 作用 |
|------|------|
| `_UPLOAD_SUMMARY_BEGIN/END` | 读写**底部**总结块，不依赖顶部赋值是否被写坏 |
| `_summary_markers_need_repair()` | 检测空字符串、缺行、非 canonical 赋值 |
| `ensure_summary_marker_assignments()` | 用 `[\r\n]+` regex 整行替换（**CRLF 须一次匹配两行**，旧 `\n` -only 会只删第一行） |
| 调用时机 | import 时；`write_version` 写盘后；`write_summary_block` 开头；上传脚本 **`git add` 前** |

业务逻辑在 `scripts/tools/github_upload_module.py`；根/`scripts/` 下文件仅为 **subprocess 重导向**（禁止 `import *` 包装）。

版本号在 **pre-commit 通过后** 才写入 `_version.py`；pre-commit 或 commit 失败时脚本自动回滚 `_VERSION` 与底部总结块，**修复后直接重跑上传脚本即可**（无需 `--no-bump`）。  
仅当 **commit 已成功、push 失败** 或 **显式跳过 bump** 时用 `--no-bump`。

---

## 5. 入口与 `No module named 'scripts'`

直接运行 `scripts/tools/github_upload_module.py` 时，必须把 **仓库根** 加入 `sys.path`。

- 工具脚本开头：`Path(__file__).parent.parent.parent` 插入 `sys.path`
- 包装器 subprocess 必须 `cwd=仓库根`

---

## 6. Windows / CRLF / 中文路径

| 现象 | 处理 |
|------|------|
| `LF will be replaced by CRLF` | **警告**，可忽略 |
| `git add` 报 pathspec 含 `344/274/232/...` | **中文路径被 `Path()` 误解析**（见下） |
| 全仓库换行符改动 | **不要** `git stash -u` 后 `git add .`；只对变更路径 pre-commit |
| `.pre-commit-config.yaml` 被 stash 带走 | 见 §7 |

### 6.1 中文路径 pathspec 灾难（`[SEV-HIGH]`）

**现象**：

```text
fatal: pathspec '"docs/344/274/232/350/257/235/.../214.md"' did not match any files
```

**根因**：`git status --porcelain` 在 `core.quotepath=true`（默认）时对非 ASCII 路径输出 `\"docs/\\344\\274\\232...\"`。若在解码前对该字符串调用 **`Path()`**，Windows 会把 `\344` 等八进制转义里的 **反斜杠当成路径分隔符**，路径被拆成 `docs/344/274/232/...`。

**脚本防护（2026-06-04 §4.153）**：

| 措施 | 作用 |
|------|------|
| `git -c core.quotepath=false` | `status` / `diff --name-only` 直接输出 UTF-8 中文路径 |
| `_unquote_git_path()` | 对仍带引号的路径做 C 风格八进制解码（**拼 UTF-8 字节**，勿用 `chr()` 拼 Unicode） |
| `_normalize_change_path()` | 规范为 POSIX 相对路径；**禁止**对未解码 porcelain 字符串用 `Path()` |
| `_rel_repo_path()` | 字符串走 `_normalize_change_path`；仅 `Path` 对象才用 pathlib |

**Agent 勿重复**：在 `_collect_change_paths` / `_stage_upload_changes` 中对含 `\ddd` 的路径直接 `Path(raw)` 或 `.replace("\\", "/")` 而不先 unquote。

### 6.2 commit hook stash 冲突

**现象**：脚本内 pre-commit 已通过，但 `git commit` 报 `Unstaged files detected` / `Stashed changes conflicted with hook auto-fixes`。

**根因**：部分 doc（如 `docs/会话接续手册.md`）**工作区已改但未进 index**；commit 时 pre-commit hook 会 stash 未暂存改动，改文件后 rollback。

**脚本防护**：pre-commit 通过后调用 `_refresh_staging_for_commit()`，合并 `change_paths` + 最新 porcelain + **所有 unstaged 改动** 再 `git add`。

`.ruff.toml` 的 `[lint.per-file-ignores]` 路径须与 **真实路径** 一致（如 `scripts/tools/devtool.py`，不是 `scripts/devtool.py`）。

---

## 7. stash 恢复（PowerShell 须加引号）

| 场景 | 命令 |
|------|------|
| 恢复 **未跟踪** 文件（如 `.pre-commit-config.yaml`） | `git checkout 'stash@{0}^3' -- .pre-commit-config.yaml` |
| 恢复已跟踪文件 | `git checkout 'stash@{0}' -- <路径>` |
| `git checkout stash@{0} -- …` 报 pathspec 不匹配 | 多为未跟踪文件，改用 `^3` 或 `git stash show -p` |

`PRE_COMMIT_ALLOW_NO_CONFIG=1` **仅在** 仓库内根本没有 pre-commit 配置时有用；配置被 stash 走后应 **恢复文件**，不是绕过 hook。

---

## 8. Agent 红线（摘要）

- 默认 **人类** 执行 `python github_upload_module.py`；Agent 不得主动 upload
- sandbox 内 **禁止** `git rm` / `git reset` / `git checkout HEAD --` 等写操作（见 `.cursorrules`）
- 改上传逻辑只改 `scripts/tools/github_upload_module.py`
- 上传失败排障顺序：`--check` → **`ruff-lint` 行** Failed → **`F822 SUMMARY_*` 查 `_version.py` 顶部**（非 doc 问题）→ pathspec `344/274/...` → 修复后重跑；**push 失败** 用 `--no-bump`

---

## 10. 验收：Windows 全流程（2026-06-04）

**已验证 commit** `ad867583`（`v3.21.2: 更新 12 处文件`）→ `main` push 成功。

| 阶段 | 正常日志 | 说明 |
|------|----------|------|
| 同步 | `已与 origin/main 同步，跳过 pull` | 落后 0 不 stash |
| 暂存 | `git add（N 个路径，非全仓库）` | 中文 doc 路径正确 |
| pre-commit 第 1 轮 | `ruff-format` / `trim trailing whitespace` / `mixed-line-ending` **Failed** | 含 `docs/会话接续手册.md` 时控制台可能乱码，**可忽略** |
| pre-commit 第 2 轮 | 全部 Passed | `[信息] pre-commit 第 2 轮已通过` |
| commit 前 | `commit 前 pre-commit` → 全部 Passed | `write_version` + `_refresh_staging` 后再跑一轮，避免 commit hook 换行 Failed |
| commit hook | 再次 pre-commit 全 Passed | 与上一行同步后应一致通过 |
| 结束 | `[成功] 推送完成` + `[完成]` | 唯一成功判据 |

**commit 消息里**可能出现 `create mode ... "docs/\\344\\270\\212..."`（Git 八进制显示），磁盘文件名仍为 `docs/上传脚本与-pre-commit.md`，**属显示 quirks，不是失败**。

**补推**：commit 已成功但 push 失败 → `python github_upload_module.py --no-bump`。

---

## 9. 相关测试

```powershell
python -m pytest games/endfield/tests/tools/test_upload_meta.py games/endfield/tests/tools/test_github_upload_signing.py games/endfield/tests/tools/test_git_backup.py -q
```

---

*最后更新：2026-06-04（§4.155 `_version` F822 / CRLF ensure / 文档同批误判）*
