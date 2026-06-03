# Agent Skills Configuration

## Session continuity (new conversations)

**At the start of every new conversation** on this repo (unless the user only asks a one-off question unrelated to the codebase), read these two documents first:

1. [`docs/会话接续手册.md`](docs/会话接续手册.md) — architecture seams, recent completed work, commands, what not to redo
2. [`docs/项目目标.md`](docs/项目目标.md) — long-term vision and current focus areas

If the user @-mentions either file, treat it as mandatory context before any code change.

**Layout constraints:** Before structural refactors or adding modules, read [`docs/代码结构规范.md`](docs/代码结构规范.md) and [`docs/adr/0001-code-layout-constraints.md`](docs/adr/0001-code-layout-constraints.md) (≤10 items per directory, ~400 lines per file).

## Project operations

Before changing code or pushing to GitHub, read the human operation guide: [`docs/操作指令集.md`](docs/操作指令集.md) (`[根]` / `[工具]` / `[包]` directories, upload script, versioning). **Upload / pre-commit troubleshooting:** [`docs/上传脚本与-pre-commit.md`](docs/上传脚本与-pre-commit.md) (**required**). Domain terms: [`CONTEXT.md`](CONTEXT.md). Repo maintenance scripts live under [`tools/`](tools/README.md) (not package `scripts/`). License: [`LICENSE`](LICENSE), [`DATA_LICENSE`](DATA_LICENSE), [`docs/数据来源与许可.md`](docs/数据来源与许可.md).

### Pushing to GitHub (agents)

- **Default: the human runs upload.** Publishing is done by the repo maintainer locally with `python github_upload_module.py` from repo root. Agents **must not** run the upload script unless the user **explicitly asks in that conversation** (e.g. “帮我上传”“执行上传脚本”).
- When work is ready but the user has not asked to publish, **stop** and tell them which command to run (`github_upload_module.py`, optional `--minor` / `--no-bump`); do not upload on your own initiative.
- **Do not** use bare `git commit` + `git push` to publish changes.
- If the user explicitly requests upload, run from repo root: `python github_upload_module.py` (add `--minor` or `--no-bump` when appropriate).
- Version bumps for `_VERSION` must go through the upload script so `please_read_me.py` and commit messages stay consistent.
- Upload script may **GPG/SSH-sign** commits when configured; unconfigured commits may lack GitHub **Verified** badge.
- **Mandatory:** [`docs/上传脚本与-pre-commit.md`](docs/上传脚本与-pre-commit.md) — pre-commit two-round behavior, `_version` SUMMARY markers, stash/CRLF, `--no-bump` retry, **ruff-lint line-only detection**, **Windows 中文 pathspec（禁止 Path(porcelain)）**.

### Pulling from GitHub (agents)

- **Do not** run `github_download_module.py` unless the user explicitly asks to discard local work.
- That script requires typing **`覆盖本地`** to confirm; it runs `reset --hard` and `git clean -fd`.

## Agent skills

### Issue tracker

Issues are tracked in GitHub Issues for this repo. Web forms: `.github/ISSUE_TEMPLATE/`（Bug 报告、功能建议；默认 `needs-triage`）. See `docs/agents/issue-tracker.md` and `docs/agents/triage-labels.md`.

### Triage labels

Using default triage label vocabulary: needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout: one CONTEXT.md + docs/adr/ at repo root. See `docs/agents/domain.md`.

### Default development workflow

**When the user requests feature implementation, bug fixes, or code changes**, default to the `design-then-build` workflow:
1. First interview the user to clarify the design (grill-me style)
2. Then implement with TDD (test-first, red-green-refactor)
3. For non-risky operations (tests, code edits, dependency installs), auto-consent
4. For high-risk operations (upload scripts, git push, destructive commands), ask user first
