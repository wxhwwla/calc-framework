# 仓库清理计划：.gitignore / .gitattributes 与误上传文件

> 编写日期：2026-06-15
> 状态：已完成

## 背景

对 `.gitattributes` 和 `.gitignore` 进行全面审查，发现以下问题：

### 发现问题清单

| # | 问题 | 严重程度 | 说明 |
|---|------|----------|------|
| 1 | `tools/arknights_scout/output/` 下 **1273 个文件**被跟踪 | 🔴 高 | `.gitignore` 已声明忽略，但文件在规则添加前已被跟踪，仍留在仓库中 |
| 2 | `ui_preferences.json`（根目录）被跟踪 | 🟡 中 | 运行时用户偏好配置，不应提交 |
| 3 | `games/endfield/ui_preferences.json` 被跟踪 | 🟡 中 | 同上 |
| 4 | `.trae/rules/project_rules.md` 被跟踪 | 🟢 低 | `.trae/` 在 `.gitignore` 中但文件已跟踪 |
| 5 | `.gitattributes`：缺少 `*.wasm linguist-vendored` | 🟢 低 | 638KB 的 WASM 二进制文件未排除在语言统计外 |
| 6 | `.gitignore`：`debug.log` 重复于 `*.log` | 🟢 低 | 纯冗余，`*.log` 已覆盖 |

## 处理方案

### 1. `tools/arknights_scout/output/` — 1273 个文件的 git 跟踪移除

- 执行 `git rm --cached -r tools/arknights_scout/output/`
- 保留本地文件，仅从 git 索引中移除
- 加入 `.gitignore` 的规则 `tools/arknights_scout/output/` 已存在，移除索引后不会再被误添加

### 2. `ui_preferences.json` × 2

- 执行 `git rm --cached ui_preferences.json`
- 执行 `git rm --cached games/endfield/ui_preferences.json`
- `.gitignore` 的 `ui_preferences.json` 规则已存在

### 3. `.trae/rules/project_rules.md`

- 执行 `git rm --cached .trae/rules/project_rules.md`
- `.gitignore` 的 `.trae/` 规则已存在

### 4. `.gitattributes` 补充

- 添加 `*.wasm linguist-vendored` 防止 WASM 影响 GitHub 语言统计

### 5. `.gitignore` 清理

- 删除冗余的 `debug.log` 行（已被 `*.log` 覆盖）

## 执行结果

全部在 2026-06-15 完成。

| # | 操作 | 状态 | 影响文件数 |
|---|------|------|-----------|
| 1 | `git rm --cached tools/arknights_scout/output/` | ✅ 已完成 | 1273 个文件从跟踪移除 |
| 2 | `git rm --cached ui_preferences.json` | ✅ 已完成 | 1 个文件 |
| 3 | `git rm --cached games/endfield/ui_preferences.json` | ✅ 已完成 | 1 个文件 |
| 4 | `git rm --cached .trae/rules/project_rules.md` | ✅ 已完成 | 1 个文件 |
| 5 | `.gitattributes` 添加 `*.wasm linguist-vendored` | ✅ 已完成 | — |
| 6 | `.gitignore` 移除冗余 `debug.log` | ✅ 已完成 | — |

总计从 git 跟踪中移除 **1276 个文件**（1273 + 1 + 1 + 1）。

### 变更清单

```
.gitignore
  - debug.log       # 移除冗余行（*.log 已覆盖）
.gitattributes
  + *.wasm linguist-vendored binary  # 新增 WASM 二进制标记
git rm --cached
  - tools/arknights_scout/output/    # 1273 个爬虫输出文件
  - ui_preferences.json              # 运行时用户偏好
  - games/endfield/ui_preferences.json
  - .trae/rules/project_rules.md     # IDE 配置
```

### 验证

- `git ls-files tools/arknights_scout/output/` → 0 files tracked ✅
- `git ls-files ui_preferences.json` → 0 files tracked ✅
- `git ls-files games/endfield/ui_preferences.json` → 0 files tracked ✅
- `git ls-files .trae/rules/project_rules.md` → 0 files tracked ✅
