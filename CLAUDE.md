# Calc Framework — 项目规则（完整版）

> 本文件是 Claude Code 全局遵守的项目规则，整合自 `.trae/rules/project_rules.md` 和 `AGENTS.md`。每次新对话自动加载。

---

## 一、会话接续（新对话必读）

**每次新对话开始**（除非用户只问一个与代码库无关的一次性问题），必须先读取：

1. `docs/会话接续手册.md` — 项目状态、架构接缝、近期完成的工作、勿重复做的事
2. `docs/项目目标.md` — 长远愿景和当前焦点

即使对话历史中已有这些文件内容，也必须重新读。如果文件在对话中被更新过，下次改代码前重新读。

### 读完整对话总结

每次新对话开始，**必须先完整阅读系统提供的对话总结（Conversation Summary）**，逐字读完，不能跳过。若总结提到有操作被覆盖/丢失，必须先恢复再开始新操作。

---

## 二、先行阅读（动手前必读）

| 文档 | 何时读 |
|------|--------|
| `docs/操作指令集.md` | 改代码或推 GitHub 前 |
| `docs/上传脚本与-pre-commit.md` | **上传/改上传脚本/pre-commit 排障前必读** |
| `docs/代码结构规范.md` | 结构性重构或新增模块前 |
| `docs/adr/0001-code-layout-constraints.md` | 结构性重构或新增模块前 |
| `docs/错误集.md` | **每次报告 Bug 或问题时**（先查有没有已解决的类似案例） |
| `docs/版本号说明.md` | 修改版本号前 |
| `docs/框架适配新游戏指南.md` | 为另一款游戏创建计算适配包时 |
| `CONTEXT.md` | 领域术语查询 |
| `tools/README.md` | 仓库维护脚本 |

---

## 三、Git 操作 — 全部通过上传脚本

### 核心原则

**所有涉及 git 暂存、提交、推送的操作，都必须通过 `python github_upload_module.py` 进行。**

- Agent **不得**直接执行 `git add`（即使只暂存文件）
- Agent **不得**直接执行 `git commit`
- Agent **不得**直接执行 `git push`
- 工作就绪后，告知用户应执行的命令和当前暂存区状态，由用户运行上传脚本

### 推送（上传）

- **默认由人类执行上传**。Agent **不得**运行上传脚本，除非用户在**当前对话中明确要求**（如"帮我上传""执行上传脚本"）。
- 工作就绪但用户未要求发布时，**停下来**告知用户应执行的命令（`python github_upload_module.py`，可选 `--minor` / `--no-bump` / `--dry-run`）；不得主动执行任何 git 写操作。
- 如果用户明确要求上传，执行：`python github_upload_module.py`（适当时加 `--minor` 或 `--no-bump` 或 `--dry-run`）。
- `_VERSION` 版本号必须通过上传脚本更新，以保证 `please_read_me.py` 和提交信息一致。

### 拉取（下载）

- **不得**执行 `github_download_module.py`，除非用户明确要求丢弃本地工作。
- 该脚本要求输入确认词 **`覆盖本地`**，会执行 `reset --hard` 和 `git clean -fd`。

---

## 四、Agent 禁止的操作（红线）

以下操作**绝对禁止**，除非用户在**当前对话中明确说出"执行"或"删除"等授权用语**：

| 操作 | 原因 |
|------|------|
| **删除 Git 跟踪的文件**（`git rm`、`git rm --cached`） | 永久删除仓库历史中的文件，可能级联删除无关文件 |
| **删除工作区的文件/目录**（`del`、`rm -rf`） | 可能误删重要代码或测试 |
| **丢弃未提交的更改**（`git checkout --`、`git reset --hard`） | 不可逆地丢失未提交的代码 |
| **推送到远程仓库**（`git push`、上传脚本） | 影响其他协作者；除非用户明确要求 |
| **`git add`** | 可能触发 sandbox 同步异常 |

### trae-sandbox 操作红线

Agent 在 sandbox 中只能执行以下 Git **只读**命令：

- `git status` / `git log` / `git diff` / `git show` / `git ls-files` / `git ls-tree`

**禁止**任何 Git 写操作（`git rm`、`git add`、`git commit`、`git push`、`git reset`、`git checkout`），因为这些操作在 sandbox 中会直接修改真实磁盘文件，且可能因 sandbox 同步异常导致文件丢失。

---

## 五、任务管理

### 任务计划记录

开始任何代码修改、重构或问题修复前，必须将任务计划（任务项、优先级、步骤）写入 `.trae/plans/当前任务计划.md`。任务完成后删除该文件。

### 任务完成收尾协议

任务完成后**必须**执行：

1. **更新 CI 配置** — 如果变更影响测试/依赖/打包/代码结构，同步更新 `.github/workflows/*.yml`
2. **更新文档** — 按需更新 `docs/会话接续手册.md`、`docs/操作指令集.md`、`docs/错误集.md`、`README.md` 等
3. **清理计划文件** — 删除 `.trae/plans/当前任务计划.md`
4. **输出明确的任务总结** — 列出已完成项 + 未完成项 + 暂存区状态
5. **向用户提问后续** — 如"需要上传 GitHub 吗？"

**禁止**：修改代码后不同步更新相关文档和 CI；任务完成不做总结。

### 默认开发流程

功能实现/Bug 修复/代码变更默认走 `design-then-build`：
1. 先与用户沟通厘清设计
2. 再以 TDD 方式实现（测试先行，红-绿-重构）
3. 低风险操作可自动同意
4. 高风险操作（上传脚本、`git push`、破坏性命令）必须先问用户

---

## 六、严重程度标签

所有诊断信息标注以下标签：

| 标签 | 含义 |
|------|------|
| `[SEV-OK]` | 无问题 |
| `[SEV-LOW]` | 外观、风格、轻微重构 |
| `[SEV-MED]` | 逻辑 Bug、遗漏边界情况、潜在回归 |
| `[SEV-HIGH]` | 静默数据丢失、算术溢出、计算结果错误 |

---

## 七、错误集优先查阅规则

当用户报告 Bug 或提出改进请求时：
1. **先查阅** `docs/错误集.md` — 搜索是否已有类似问题记录
2. 如有：参考修复方案
3. 如无：诊断后修复，并将新问题+修复方案追加到错误集
4. 禁止：不查错误集就从头诊断已有记录的问题

---

## 八、并行执行

独立子任务应并行执行：同时运行代码检查 + 更新文档、同时读取多个文件、同时编辑多个独立文件等。**不要将存在依赖关系的操作并行执行。**

---

## 九、代码规范

### 导入排序

四组顺序，组间空行：
```
组 0：from __future__ import annotations
组 1：标准库（json、pathlib、typing 等）
组 2：第三方库（fastapi、pydantic、pytest 等）
组 3：框架库（calc_framework.*）
组 4：本地应用（api.*、games.*、from . import xxx）
```

### 公共 API 声明

每个 `__init__.py` 必须声明 `__all__` 确定公共 API 边界。空包写 `__all__: list[str] = []`。

### 文档字符串（Google 风格，中文）

**必须写**：公共 API、FastAPI 路由、长函数（≥40 行）。**可不写**：`_` 前缀短 helper、≤3 行的 trivial wrapper。

### 异常层级

异常类以 `Error` 结尾，有 docstring，有基类继承层次。特定构造参数用关键字参数（`*` 后）。

### 目录与文件规模

- 目录直接子项 **≤ 20（硬顶）**，目标 ≤ 15
- 单文件 **≤ 400 行**（硬顶 500）

### 编码规范

- 所有 `.py` 文件首行必须有 `# -*- coding: utf-8 -*-`
- 标准文件头：`编码声明 → SPDX-License-Identifier → docstring`
- 文本文件使用 UTF-8（无 BOM）
- venv 创建前必须设置 `$env:PYTHONUTF8 = "1"` 和 `chcp 65001`

---

## 十、GitHub Issues 与 Issue 管理

- Issue 通过 GitHub Issues 跟踪，Web 表单在 `.github/ISSUE_TEMPLATE/`（Bug 报告、功能建议）
- 默认标签：`needs-triage`、`needs-info`、`ready-for-agent`、`ready-for-human`、`wontfix`
- 见 `docs/agents/issue-tracker.md` 和 `docs/agents/triage-labels.md`
