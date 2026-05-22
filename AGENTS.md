# Agent Skills Configuration

## Project operations

Before changing code or pushing to GitHub, read the human operation guide: [`docs/操作指令集.md`](docs/操作指令集.md) (working directories, upload script, versioning). Domain terms: [`CONTEXT.md`](CONTEXT.md). License: [`LICENSE`](LICENSE), [`DATA_LICENSE`](DATA_LICENSE), [`docs/数据来源与许可.md`](docs/数据来源与许可.md).

### Pushing to GitHub (agents)

- **Do not** use bare `git commit` + `git push` to publish changes for the user.
- **Do** run from repo root: `python github_upload_module.py` (add `--minor` or `--no-bump` when appropriate).
- If changes are ready but the user has not asked to push, **stop** and tell them to run the upload script (or ask explicitly before pushing).
- Version bumps for `_VERSION` must go through the upload script so `please_read_me.py` and commit messages stay consistent.
- Upload script may **GPG/SSH-sign** commits when configured; unconfigured commits may lack GitHub **Verified** badge.

### Pulling from GitHub (agents)

- **Do not** run `github_download_module.py` unless the user explicitly asks to discard local work.
- That script requires typing **`覆盖本地`** to confirm; it runs `reset --hard` and `git clean -fd`.

## Agent skills

### Issue tracker

Issues are tracked in GitHub Issues for this repo. See `docs/agents/issue-tracker.md`.

### Triage labels

Using default triage label vocabulary: needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout: one CONTEXT.md + docs/adr/ at repo root. See `docs/agents/domain.md`.
