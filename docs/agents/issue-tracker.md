# Issue tracker: GitHub

Issues and PRDs for this repo live as GitHub issues. Use the `gh` CLI for all operations.

## Issue 模板（GitHub Web）

仓库提供表单模板（`.github/ISSUE_TEMPLATE/`）：

| 模板 | 用途 |
|------|------|
| **Bug 报告** | 描述、复现步骤、期望行为、环境（OS / Python / 版本） |
| **功能建议** | 动机、建议方案、优先级 |

在 GitHub 仓库页 **Issues → New issue** 即可选择。新建 Bug 默认带 `needs-triage` 标签。

`config.yml` 中 `blank_issues_enabled: false`，避免空白 Issue；侧边链到操作指令集与会话手册。

### 人类填写建议

- **版本**：窗口标题 `v…`（`please_read_me._EXE_VERSION`）或 pip/上传用 `please_read_me._VERSION`；exe 分发以窗口标题为准
- **全量搜索类 Bug**：是否开启「使用手动次数」、固定配装勾选、武器/装备范围
- **日志**：终端完整 traceback；勿粘贴含个人路径时可打码

### 从命令行创建

```powershell
gh auth login
gh issue create --web
gh issue view 42 --comments
gh issue edit 42 --add-label "ready-for-agent"
```

## Conventions

- **Create an issue**: `gh issue create --title "..." --body "..."`. Use a heredoc for multi-line bodies.
- **Read an issue**: `gh issue view <number> --comments`, filtering comments by `jq` and also fetching labels.
- **List issues**: `gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'` with appropriate `--label` and `--state` filters.
- **Comment on an issue**: `gh issue comment <number> --body "..."`
- **Apply / remove labels**: `gh issue edit <number> --add-label "..."` / `--remove-label "..."`
- **Close**: `gh issue close <number> --comment "..."`

Infer the repo from `git remote -v` — `gh` does this automatically when run inside a clone.

## When a skill says "publish to the issue tracker"

Create a GitHub issue.

## When a skill says "fetch the relevant ticket"

Run `gh issue view <number> --comments`.
