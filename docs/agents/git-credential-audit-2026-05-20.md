# Git 凭据历史复查（2026-05-20）

## 检查项

| 检查 | 结果 |
|------|------|
| `git remote -v` 是否含 Token | 否，当前为 `git@github.com:wxhwwla/endfield_damage_calculator_2.0.git` |
| 历史提交是否含 `ghp_` / `github_pat_` | 未发现（`git log -S` 无匹配） |
| 工作区是否存在 `git_key.txt` | 否（且已列入 `.gitignore`） |

## 建议

- 若曾在其他克隆或 fork 中将 PAT 写入 remote 并推送，应在 GitHub **Settings → Developer settings** 撤销该 PAT。
- 推送脚本已入库且默认 SSH，勿再把 Token 写入 remote URL。
