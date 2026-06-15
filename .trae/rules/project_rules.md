# 项目规则

## 目录

- [会话接续](#会话接续)
- [先行阅读](#先行阅读)
- [错误集优先查阅规则](#错误集优先查阅规则)
- [任务完成收尾协议](#任务完成收尾协议)
- [任务计划记录](#任务计划记录)
- [默认开发流程](#默认开发流程)
- [严重程度标签（CVSS 风格）](#严重程度标签cvss-风格)
- [并行执行](#并行执行)
- [推送与拉取 GitHub](#推送与拉取-github)
- [trae-sandbox 操作红线](#trae-sandbox-操作红线)
- [删除前知情协作协议](#删除前知情协作协议)
- [删除操作规范](#删除操作规范)
- [CI 配置](#ci-配置)
- [禁止的操作（红线）](#禁止的操作红线)
- [引用来源](#引用来源)
- [文件编码](#文件编码)
- [Python 模块导入规范](#python-模块导入规范)
- [Python 代码风格规范](#python-代码风格规范)
- [Pyright / Pylance 类型检查注意](#pyright--pylance-类型检查注意)
- [PyInstaller 打包规范](#pyinstaller-打包规范)
- [Web 部署规范](#web-部署规范)
- [许可证扫描与代码来源检查规范](#许可证扫描与代码来源检查规范)
- [文档位置规范](#文档位置规范)
- [开发工作流（完整发布周期）](#开发工作流完整发布周期)
- [规则同步](#规则同步)

## 会话接续

在对本仓库做任何代码修改、重构、或新增功能之前，必须先读取以下文档：

1. `docs/会话接续手册.md` — 了解当前项目状态、架构接缝和近期完成的工作
2. `docs/项目目标.md` — 了解项目的长远愿景和当前焦点

- 即使对话历史中已有这些文件内容，每次新对话也必须重新读取
- 如果文件内容在对话过程中被更新过，下次修改代码前应重新读取

### 读完整对话总结

每次新对话开始时，**必须先完整阅读系统提供的对话总结（Conversation Summary）**，了解之前发生过什么操作、丢失过什么变更、当前项目处于什么状态。

- 即使觉得"看总结就够了"，也必须**逐字读完**，不能跳过
- 若总结提到"有操作被覆盖/丢失"，必须先恢复或重做，再开始新操作
- **禁止**：不看总结，直接开始操作，导致重复同样的错误

## 先行阅读

动手前（改代码、推 GitHub、加模块等），必须阅读以下文档：

| 文档 | 何时读 |
|------|--------|
| [`docs/README.md`](../../docs/README.md) | **文档索引**（查找文档时先看这里） |
| [`docs/项目目标.md`](../../docs/项目目标.md) | **每次对话开始时**（了解长远愿景和当前焦点） |
| [`docs/版本号说明.md`](../../docs/版本号说明.md) | 修改版本号前（了解分类与规则） |
| [`docs/操作指令集.md`](../../docs/操作指令集.md) | 改代码或推 GitHub 前 |
| [`docs/上传脚本与-pre-commit.md`](../../docs/上传脚本与-pre-commit.md) | **上传 / 改上传脚本 / pre-commit 排障前（必读）** |
| [`docs/代码结构规范.md`](../../docs/代码结构规范.md) | 结构性重构或新增模块前 |
| [`docs/adr/0001-code-layout-constraints.md`](../../docs/adr/0001-code-layout-constraints.md) | 结构性重构或新增模块前 |
| [`docs/框架适配新游戏指南.md`](../../docs/框架适配新游戏指南.md) | 为另一款游戏创建计算适配包时 |
| [`docs/错误集.md`](../../docs/错误集.md) | **每次报告 Bug 或问题时**（检查是否有类似已解决案例） |
| [`CONTEXT.md`](../../CONTEXT.md) | 领域术语 |
| [`tools/README.md`](../../tools/README.md) | 仓库维护脚本 |

## 错误集优先查阅规则

当用户报告 Bug、异常行为或提出改进请求时，**必须**：

1. **先查阅 [`docs/错误集.md`](../../docs/错误集.md)**
   - 搜索是否已有类似问题的记录
   - 如有：参考修复方案，判断是否同样适用
   - 如无：诊断后修复，并将新问题+修复方案追加到错误集
2. 修复完成后更新错误集文档
3. 禁止：不查阅错误集就从头诊断已有记录的修复的问题

## 任务完成收尾协议

所有任务项标记为「已完成」后，必须执行以下操作，**不得中途停止**：

1. **更新 CI 配置**：如果本次变更影响了测试流程、依赖、打包方式或代码结构，同步更新 `.github/workflows/*.yml` 和相关测试脚本
2. **更新文档**：如果本次变更影响了功能、结构、配置或操作流程，同步更新以下文件（如适用）：
   - `docs/会话接续手册.md` — 文首日期、§3 目录、§4 近期完成
   - `docs/操作指令集.md` — 新增命令、参数或流程
   - `docs/框架适配新游戏指南.md` — 新增适配包、API 变更
   - `docs/代码结构规范.md` — 新增/删除目录超限记录
   - `docs/错误集.md` — 新增 Bug 修复记录
   - `README.md`（根和 `games/endfield/`）— 功能描述、目录列表
   - `CONTEXT.md` — 新增术语
3. **清理计划文件**：删除 `.trae/plans/当前任务计划.md`
4. **输出明确的任务总结**：列出已完成项 + 未完成项 + 当前暂存区状态
5. **向用户提问后续**：如"需要上传 GitHub 吗？""还有什么需要调整的？"等

**禁止**：任务执行完毕后不做总结就停下等待；或只做了一半编辑就中断输出。

**禁止**：修改代码后不同步更新相关文档和 CI，导致文档与代码不一致。

## 任务计划记录

开始处理任何代码修改、重构、或问题修复前，必须先将本次任务的计划（任务项、优先级、步骤）写入 `.trae/plans/当前任务计划.md`。

处理完毕后，必须删除该计划文件（`rm .trae/plans/当前任务计划.md` 或等价的清理操作），表示任务已完成。

- 若任务分多次对话完成，每次新对话开始时先读取该文件了解进度
- 若计划在执行过程中发生变化，及时更新文件

## 默认开发流程

当用户请求功能实现、Bug 修复或代码变更时，默认走 `design-then-build` 工作流：

1. 先与用户沟通厘清设计（类似 grill-me 风格）
2. 再以 TDD 方式实现（测试先行，红-绿-重构）
3. 低风险操作（测试、代码编辑、安装依赖）可自动同意
4. 高风险操作（上传脚本、git push、破坏性命令）必须先问用户

## 严重程度标签（CVSS 风格）

所有诊断信息必须标注严重程度标签：

| 标签 | 含义 |
|------|------|
| `[SEV-OK]` | 无问题 |
| `[SEV-LOW]` | 外观、风格、轻微重构 |
| `[SEV-MED]` | 逻辑 Bug、遗漏边界情况、潜在回归 |
| `[SEV-HIGH]` | 静默数据丢失、算术溢出、计算结果错误 |

## 并行执行

当一个任务可拆分为多个独立子任务时，应并行执行以缩短耗时。例如：

- 同时运行代码检查 + 更新文档
- 同时读取多个文件进行分析
- 同时搜索多个目录/模式
- 同时对多个独立文件进行编辑
- 同时运行独立的测试套件

始终将独立的工具调用（Read、Grep、Edit、RunCommand 等）合并到一条消息中。**不要将存在依赖关系的操作并行执行。**

## 推送与拉取 GitHub

### 推送（上传）

- **默认由人类执行上传**。发布由维护者在仓库根目录执行 `python github_upload_module.py`。Agent **不得**运行上传脚本，除非用户在**当前对话中明确要求**（如"帮我上传""执行上传脚本"）。
- 工作就绪但用户未要求发布时，**停下来**告知用户应执行的命令（`github_upload_module.py`，可选 `--minor` / `--no-bump` / `--dry-run`）；不得主动上传。
- **不得**使用裸 `git commit` + `git push` 发布变更。
- 如果用户明确要求上传，在仓库根目录执行：`python github_upload_module.py`（适当时添加 `--minor` 或 `--no-bump` 或 `--dry-run`）。
- `_VERSION` 版本号必须通过上传脚本更新，以保证 `please_read_me.py` 和提交信息一致。
- 改上传脚本、`_version.py` 总结标记或排查 pre-commit 失败前，**必须先读** [`docs/上传脚本与-pre-commit.md`](../../docs/上传脚本与-pre-commit.md)。

### 上传与 pre-commit 要点（摘要）

| 项 | 规则 |
|----|------|
| `--dry-run` | 预览模式：展示变更文件与版本计划，不修改/推送 |
| pre-commit 第 1 轮 Failed | `ruff-format` / `mixed-line-ending` 自动改文件属**正常**，脚本会 re-add 后跑第 2 轮 |
| `ruff-lint` 判定 | **仅** `ruff-lint...Failed` 那一行；输出里其他 hook 的 Failed **不算** lint 失败 |
| 中文 pathspec `344/274/...` | 禁止对 porcelain 转义路径用 `Path()`；`core.quotepath=false` + `_unquote_git_path()` |
| commit 前同步 | `_refresh_staging_for_commit()`：合并 change_paths + unstaged，避免 hook stash 冲突 |
| 成功判据 | 以 `[成功] 推送完成` 为准，非 pre-commit 第 1 轮 Failed |
| `ruff-lint` Failed（代码） | **`F822 SUMMARY_*`**：查 `_version.py` 顶部两行（`SUMMARY_BEGIN = _UPLOAD_SUMMARY_*`），**非 md 致错**；禁止 `SUMMARY_BEGIN=""`；ensure 在 import / `write_version` 后 / `git add` 前；CRLF 须 `[\r\n]+` regex（§4.155） |
| 文档同批误判 | 总结块同时列 doc 与 `_version.py` 时，F822 根因在标记赋值，勿归因于「刚补文档」 |
| 入口 | subprocess + `cwd=仓库根`；禁止 `import *` 包装 |
| commit 失败 | 版本可能已 bump → `--no-bump` 补推 |
| push 失败 | 脚本自动回滚 `_VERSION` 到推送前值；commit 保留，修复后 `--no-bump` 补推 |
| stash 未跟踪文件 | PowerShell：`git checkout 'stash@{0}^3' -- <文件>` |

全文见 [`docs/上传脚本与-pre-commit.md`](../../docs/上传脚本与-pre-commit.md)。

### 拉取（下载）

- **不得**执行 `github_download_module.py`，除非用户明确要求丢弃本地工作。
- 该脚本要求输入确认词 **`覆盖本地`**，会执行 `reset --hard` 和 `git clean -fd`。

## trae-sandbox 操作红线（关键教训）

**背景**：`trae-sandbox` 是 Agent 命令的执行环境。实验已证明：sandbox 中的 Git 写操作（`git rm`、`git add`、`git reset` 等）**会直接影响真实磁盘上的文件**。

**关键结论（2026-05-30 两轮实验证实）**：

1. ❌ 之前"文件没丢、只是 sandbox 幻觉"的结论是**完全错误的** — 用户从真实终端确认文件确实从磁盘上消失了
2. ✅ **sandbox 中的 `git rm` 会删除真实磁盘上的文件**
3. ✅ **实验证明：sandbox `git rm` 会额外删除磁盘上所有与被删文件 basename 相同的文件**（同名不同路径）
4. ❌ 在测试仓库中，sandbox `git rm` 12 个文件 → 额外删除了 12 个同名子目录文件
5. ❌ 在真实项目中，多次 sandbox Git 写操作累积叠加，导致数百个文件丢失
6. ✅ 恢复方式：在真实终端执行 `git checkout HEAD -- .` 即可从最新提交还原全部文件

### 根本规则：Agent 绝不执行 Git 写操作

**Agent 在 sandbox 中只能执行以下 Git 命令：**

- `git status`（查看状态）
- `git log`（查看历史）
- `git diff`（查看差异）
- `git ls-tree` / `git ls-files`（只读查询）
- `git show`（查看提交内容）

**禁止执行的 Git 写操作（即使是用户授权的）：**

| 命令 | 禁止原因 |
|------|----------|
| `git rm` | 会删除真实磁盘文件，且可能级联删除无关文件 |
| `git rm --cached` | 会触发 sandbox 同步异常，导致大量文件丢失 |
| `git reset HEAD` | 无参数时更改索引状态，trigger sandbox 同步 |
| `git checkout HEAD -- <path>` | 恢复操作。由用户在真实终端执行 |
| `git add` | 更改索引，可能触发 sandbox 同步异常 |
| `git commit` | 不允许在 sandbox 中提交 |

### 替代流程

需要执行任何 Git 写操作时：

1. Agent **在 sandbox 中运行 `git status --short` 获取当前状态**（只读，安全）
2. Agent 告知用户要执行的操作和精确命令
3. **用户在真实终端执行操作**
4. 用户将输出粘贴回来供 Agent 分析
5. Agent 验证结果

### 特例（仅限新文件创建）

以下操作在 sandbox 中允许：
- `mkdir`、`Set-Content`（创建新文件/目录）
- `git add` 新文件到暂存区（仅当文件是刚创建的且无风险）
- 读写非 Git 跟踪的文件（如 `tests/` 中无 git 索引的文件）

---

## trae-sandbox 环境幻觉防护（已废除）

~~之前的「trae-sandbox 环境幻觉」结论是错误的。sandbox 视图与真实视图不一致是因为文件已经被删除了，而不是"幻觉"。~~

---

## 删除前知情协作协议

**双方约定**：在任何涉及删除/丢弃/恢复文件的操作之前，必须执行以下流程：

### 用户承诺

1. 先执行 `git status`（必要时加 `git diff --cached --stat` 查看暂存区）
2. 将输出**完整截图或粘贴**给 Agent，确保 Agent 对当前 Git 状态完全知情
3. 明确说出期望的操作目标（如"删这 12 个旧文件""恢复丢失的测试文件"）

### Agent 承诺

1. 收到用户的 `git status` 截图/粘贴后，先逐行分析：
   - 暂存区有什么（`M` / `A` / `D` / `R`）
   - 工作区有什么修改（` M` / ` D` / `??`）
   - 是否有未跟踪文件（`??`）
   - 是否有文件丢失（` D` = 磁盘删除但 Git 跟踪）
2. 如实向用户报告发现的**所有异常状态**（如大量 ` D`、未预期的暂存变更等）
3. 在用户确认知情且同意继续之前，**不得执行任何删除/恢复/丢弃操作**
4. 最终执行前，将操作清单写入 `.trae/plans/当前任务计划.md` 供用户复核

### 例外情况

以下情况可跳过此流程：
- 只是创建新文件，不涉及删除/移动/修改已有文件
- 用户明确说"不用检查了，直接执行"

---

## 删除操作规范

在向用户提议删除任何文件前，必须遵循以下步骤：

### 单个/少量文件

1. 确认该文件确实没有被任何其他代码引用（搜索 `grep`/`SearchCodebase` 确认 import、引用、测试依赖）
2. 将删除操作写入 `.trae/plans/当前任务计划.md`
3. 告知用户：要删什么、为什么可删（附上"无引用"的证据）、影响范围
4. **等待用户明确授权后才能执行**

### 批量文件（3 个以上）

对于批量删除（如整个目录、一组文件），**必须反复确认每个文件**的依赖关系：

1. 逐一检查每个文件是否被其他模块引用：
   - 搜索 import 路径
   - 搜索测试文件中的引用
   - 搜索文档中的引用
   - 搜索配置文件中的路径引用
2. 将完整的依赖分析结果写入 `.trae/plans/当前任务计划.md`
3. 告知用户完整清单，包括每个文件的依赖分析结论
4. **等待用户明确授权后才能执行**

## CI 配置

修改 CI 工作流（`.github/workflows/*.yml`）前，必须读取当前所有 workflow 文件，确保理解测试流程、覆盖率门槛和触发器路径。

## 禁止的操作（红线）

以下操作**绝对禁止**，除非用户在**当前对话中明确说出"执行"或"删除"等授权用语**：

| 操作 | 举例 | 原因 |
|------|------|------|
| **删除 Git 跟踪的文件** | `git rm`、`git rm --cached` | 永久删除仓库历史中的文件，无法恢复 |
| **删除工作区的文件/目录** | `del`、`rm -rf`、删除测试文件 | 可能误删重要代码或测试 |
| **丢弃未提交的更改** | `git checkout --`、`git reset --hard` | 不可逆地丢失未提交的代码 |
| **推送到远程仓库** | `git push`、上传脚本 | 影响其他协作者 |
| **删除 git 快照目录** | `rm -rf git_backup/snapshots` | 丢失 Minor 上传前的本地 `.git` 恢复副本 |
| **提交 git 快照** | `git add git_backup/snapshots` | 体积巨大；快照已在 `.gitignore` 中排除 |

### git_backup/（Minor 上传前本地 .git 快照）

- **触发**：`python github_upload_module.py --minor` 或交互选 **M** 时，commit 前自动复制 `.git` → `git_backup/snapshots/`
- **说明**：`git_backup/README.md`（恢复步骤、磁盘占用、`--no-git-backup` 跳过方式）
- **勿提交** `snapshots/` 到 GitHub
- **不能代替 push**：远程 GitHub/Gitee 仍是主副本
- **Agent 不得擅自删除** `git_backup/snapshots/`；删前须人类确认

任何涉及上述操作的提议，必须先写入 `.trae/plans/当前任务计划.md`，然后在对话中明确告知用户并等待授权。**用户未授权前，不得执行任何一行相关命令。**

### git checkout -- <path> 恢复操作的特殊约束

当需要执行 `git checkout -- <path>` 来恢复被误删的文件时，**必须先执行以下检查**：

1. **检查暂存区**：运行 `git diff --cached --stat -- <path>` 确认该路径下**没有已暂存的变更**
2. 如果存在已暂存变更（如搬迁、删除、重命名），`git checkout --` 会**覆盖/撤销这些变更**
3. **必须告知用户**："该路径下有 N 个已暂存变更，`git checkout --` 会将其覆盖。是否确认？"
4. **等待用户明确授权后再执行**

**禁止**：在不检查暂存区的情况下，直接跑 `git checkout -- <path>` 恢复文件。

## 引用来源

本规则整合自：
- [`AGENTS.md`](../../AGENTS.md) — 会话接续、项目操作、推送/拉取、默认工作流
- 用户指令 — 任务计划记录、CI 配置、删除操作规范、禁止的操作红线
- 2026-05-30 复现实验 — trae-sandbox 环境幻觉防护（`git rm` 触发 stat 缓存导致虚假 ` D`）

## 文件编码

本项目所有文件使用 **UTF-8 编码（无 BOM）**。

### venv 创建编码保护

**在创建或重建 venv 之前**，必须确保终端/进程编码为 UTF-8，否则 `pip install` 可能将含 Unicode 字符的包文件写入为 GBK 损坏版本。

```powershell
# 必须：设置 UTF-8 模式
$env:PYTHONUTF8 = "1"
chcp 65001 > $null

# 验证
python -c "assert __import__('sys').getfilesystemencoding()=='utf-8'"

# 然后创建 venv
python -m venv .venv
```

- Python ≥ 3.12 的 `python -m venv` 自动继承 UTF-8 模式，但 `chcp 65001` 保证终端不会用 GBK 解释 pip 的输出
- 系统 Python（`E:\python\`）与 `.venv` 用不同解释器时尤其注意检查编码

### 文件头编码声明

所有 **`.py` 文件**必须在文件首行（第 1 行）添加显式编码声明：

```python
# -*- coding: utf-8 -*-
```

**标准文件头模板**（`.py` 文件）：

```python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""模块一句话描述。"""

from __future__ import annotations
...
```

- `# -*- coding: utf-8 -*-` 必须是文件**第 1 行**（Python 解析器仅在第 1–2 行识别编码声明）
- 第 2 行：`# SPDX-License-Identifier: AGPL-3.0`
- 第 3 行起：模块 docstring（可选，按代码规范 §3-16）
- 编码声明只适用于 `.py` 文件；JSON/TS/MD/YML 无等价机制，通过 `.editorconfig` 和扫描命令保证

**新增文件必须遵守此模板。旧文件无需批量追回**（Python 3 默认即为 UTF-8，加声明的目的是防编辑器/终端以 GBK 误读）。

### 写文件规则

1. **始终使用 `encoding='utf-8'` 打开文本文件**
2. **不得写入 BOM（Byte Order Mark）** — BOM 会导致 Python 3 语法错误（`invalid non-printable character U+FEFF`）
3. **写入方式**：
   ```python
   with open(path, 'w', encoding='utf-8') as f:
       f.write(content)
   ```
4. **从 git 恢复文件**：使用 Python 读取 git 对象以避免 shell 编码转换：
   ```python
   import subprocess
   content = subprocess.check_output(['git', 'show', f'HEAD:{path}'])
   with open(path, 'wb') as f:
       f.write(content)
   ```

### 文本文件类型清单

以下文本文件类型必须使用 UTF-8 编码（无 BOM）：

| 扩展名 | 典型用途 | 编码损坏后果 |
|--------|----------|-------------|
| `.py` / `.pyw` | Python 源码 | `SyntaxError`、`ModuleNotFoundError` |
| `.json` | 游戏数据、配置文件 | `json.JSONDecodeError`，GUI 数据加载失败 |
| `.md` | 文档 | 文档中文字符显示为乱码 |
| `.html` / `.xml` | Web 页面、数据文件 | 浏览器解析错误 |
| `.yml` / `.yaml` | CI 配置、项目配置 | CI 解析失败 |
| `.ts` / `.tsx` / `.js` | TypeScript/React 源码 | 编译错误、运行时错误 |
| `.css` | 样式表 | 样式不生效 |
| `.sh` / `.bat` / `.ps1` | Shell 脚本 | 中文字符显示为乱码（不影响执行） |
| `.toml` | 项目元数据 | `tomllib.TOMLDecodeError` |
| `.spec` | PyInstaller 打包配置 | 打包解析失败 |
| `.nsi` | NSIS 安装脚本 | 安装程序文字乱码 |
| `.gitignore` / `.editorconfig` / `.cursorrules` | 仓库/编辑器配置 | 规则不生效 |
| `.cfg` / `.conf` / `.ini` | 应用程序配置 | 配置读取失败 |
| `.txt` | 发布说明、NOTICES | 用户阅读困难 |

### 编码问题诊断

| 症状 | 原因 | 修复 |
|------|------|------|
| Python `SyntaxError: invalid non-printable character U+FEFF` | `.py` 文件开头有 BOM | 删除前 3 字节 `\\xef\\xbb\\xbf` |
| Python `SyntaxError: unterminated triple-quoted string` | `.py` 中文注释/字符串被 GBK 解码写入，字符损坏 | 从 git 恢复原始文件 |
| 文件内容出现 `\ufffd` 或 `U+FFFD` | 任何文本文件编码损坏 | 从 git 恢复或手动重建含中文的部分 |
| `json.JSONDecodeError` / `tomllib.TOMLDecodeError` | `.json` / `.toml` 被 GBK 编码损坏 | 从 git 恢复原始文件 |
| Vite/tsc 构建报 `SyntaxError`（含中文字符） | `.ts` / `.tsx` 源码被损坏 | 从 git 恢复 |

### 扫描命令

**仅扫描项目源码**（排除 `dist/`、`node_modules/`、`.venv/`、`.git/`、`__pycache__/`）：

```bash
# 1. 检查 BOM（所有文本文件类型）
python -c "
import glob, os
SKIP_DIRS = {'dist','node_modules','.venv','.git','__pycache__'}
EXTENSIONS = {'*.py','*.pyw','*.json','*.md','*.html','*.xml','*.yml','*.yaml',
              '*.ts','*.tsx','*.js','*.css','*.sh','*.bat','*.ps1','*.toml',
              '*.spec','*.nsi','*.gitignore','*.cfg','*.conf','*.ini','*.txt',
              '*.mdc','*.cursorrules'}
found = []
for ext in EXTENSIONS:
    for f in glob.glob(f'**/{ext}', recursive=True):
        parts = os.path.normpath(f).split(os.sep)
        if not any(s in parts for s in SKIP_DIRS):
            with open(f,'rb') as fh:
                if fh.read(3) == b'\\xef\\xbb\\xbf':
                    found.append(f)
[print(f) for f in sorted(found)]
if not found: print('无 BOM 文件')
"

# 2. 检查无法以 UTF-8 解码的文本文件（非 .py）
python -c "
import glob, os
SKIP_DIRS = {'dist','node_modules','.venv','.git','__pycache__'}
EXTENSIONS = {'*.json','*.md','*.html','*.xml','*.yml','*.yaml',
              '*.ts','*.tsx','*.js','*.css','*.sh','*.bat','*.ps1','*.toml',
              '*.spec','*.nsi','*.gitignore','*.cfg','*.conf','*.ini','*.txt',
              '*.mdc','*.cursorrules'}
found = []
for ext in EXTENSIONS:
    for f in glob.glob(f'**/{ext}', recursive=True):
        parts = os.path.normpath(f).split(os.sep)
        if not any(s in parts for s in SKIP_DIRS) and os.path.getsize(f):
            try:
                with open(f,'r',encoding='utf-8') as fh:
                    fh.read()
            except UnicodeDecodeError:
                found.append(f)
[print(f) for f in sorted(found)]
if not found: print('UTF-8 解码全部通过')
"

# 3. 检查无法以 UTF-8 解码 / AST 解析失败的 Python 文件
python -c "
import glob, ast, os
SKIP_DIRS = {'dist','node_modules','.venv','.git','__pycache__'}
decode_fail = []
ast_fail = []
for f in glob.glob('**/*.py', recursive=True):
    parts = os.path.normpath(f).split(os.sep)
    if any(s in parts for s in SKIP_DIRS) or not os.path.getsize(f):
        continue
    try:
        with open(f,'r',encoding='utf-8') as fh:
            src = fh.read()
    except UnicodeDecodeError:
        decode_fail.append(f)
        continue
    try:
        ast.parse(src)
    except SyntaxError:
        ast_fail.append(f)
[print(f'DECODE_FAIL: {f}') for f in decode_fail]
[print(f'SYNTAX_ERROR: {f}') for f in ast_fail]
if not decode_fail and not ast_fail:
    print('Python 源码全部通过')
"

# 4. 检查 JSON 文件是否可解析（排除空文件）
python -c "
import glob, json, os
SKIP_DIRS = {'dist','node_modules','.venv','.git','__pycache__'}
fail = []
for f in glob.glob('**/*.json', recursive=True):
    parts = os.path.normpath(f).split(os.sep)
    if any(s in parts for s in SKIP_DIRS) or not os.path.getsize(f):
        continue
    try:
        json.loads(open(f,'r',encoding='utf-8').read())
    except json.JSONDecodeError as e:
        fail.append((f, str(e)))
[print(f'JSON_ERROR: {f}: {e}') for f,e in fail]
if not fail: print('JSON 文件全部通过')
"

### 已知的编码损坏文件

以下文件有历史编码损坏（BOM 或 GBK→UTF-8 双重编码），需从 git 的 fc183cf4 (v3.13.0) 版本恢复：
- ~~`framework/tests/graph_editor/test_graph_editor_widget.py`~~ ✅ 已从 v3.13.0 恢复
- ~~`framework/tests/graph_editor/test_node_operations.py`~~ ✅ 已从 v3.13.0 恢复
- ~~`framework/tests/graph_editor/test_node_panel.py`~~ ✅ 已从 v3.13.0 恢复
- ~~`framework/tests/graph_editor/test_package_manager.py`~~ ✅ 已从 v3.13.0 恢复
- ~~`framework/tests/graph_editor/test_ports_and_wire.py`~~ ✅ 已从 v3.13.0 恢复
- ~~`framework/tests/graph_editor/test_prop_panel.py`~~ ✅ 已从 v3.13.0 恢复

恢复命令：`python -c "import subprocess; [open(f,'wb').write(subprocess.check_output(['git','show','fc183cf4:framework/tests/graph_editor/'+f])) for f in ['test_graph_editor_widget.py','test_node_operations.py','test_node_panel.py','test_package_manager.py','test_ports_and_wire.py','test_prop_panel.py']]"`

上述 6 个文件编码已修复（2026-05-31），不再属于损坏文件。

---

## Python 模块导入规范（显式导入原则）（2026-06-01 新增）

### 核心原则

每个 Python 文件必须通过**显式、可追溯的 import 路径**被其他模块引用。禁止依赖"恰好就在 `sys.path` 上"的隐式导入。

此原则源于 PyInstaller 打包实战教训：命名空间包（无 `__init__.py` 的目录）的隐式导入在冻结环境下会 `ModuleNotFoundError`。

### 规则

| # | 规则 | 正确做法 | 错误做法 |
|---|------|----------|----------|
| 1 | **包内模块使用相对导入** | `from . import _path_setup` | `import _path_setup`（隐式裸导入） |
| 2 | **包内模块间交叉引用用相对导入** | `from .main import app` | `from main import app`（当作顶层模块导入） |
| 3 | **入口脚本用绝对导入** | 被 `python xxx.py` 运行的入口点，用 `import main` + `sys.path` 显式设置 | `from . import main`（相对导入在 `__main__` 中失效） |
| 4 | **包目录必须有 `__init__.py`** | `web/backend/__init__.py` 存在 | `web/backend/` 无 `__init__.py`（命名空间包） |
| 5 | **禁止依赖 `sys.path` 隐式发现** | 导入某个模块前，确保其所在包已通过 `sys.path` 显式添加 | 假设"上级目录已在 `sys.path` 中" |
| 6 | **`sys.path` 操作集中管理** | 所有路径设置在 `_path_setup.py`，其他模块只需 `from . import _path_setup` | 每个模块各自 `sys.path.insert` |

### 何时用「相对导入」vs「绝对导入」

| 场景 | 导入方式 | 示例 |
|------|----------|------|
| 同一包内：A.py 导入 B.py | `from . import B` 或 `from .B import func` | `from . import _path_setup` |
| 同一包内子包：`api/compute.py` 导入 `main.py` | `from ..main import app` | `from ..main import app` |
| 同一包内兄弟子包：`api/compute.py` 导入 `api/search.py` | `from .search import search_operator` | `from .search import search_operator` |
| 入口脚本（`__main__`） | 绝对导入 + 显式 `sys.path` | `import main`（配合 `_path_setup` 或入口点路径设置） |
| 跨包导入（如 `calc_engine` 导入 `calc_framework`） | 绝对导入（需 `_path_setup` 或 pip 安装） | `from calc_framework.logging import get_logger` |

### 检查方式

```bash
# 搜索文件中是否有可疑的「裸 import 非标准库模块」——即 import xxx 且目录下恰好有 xxx.py
# 手动检查：搜 import 语句，确认每个非 stdlib 的 import 都有包路径
python -c "
import ast, glob, sys
stdlib = set(sys.stdlib_module_names) if hasattr(sys, 'stdlib_module_names') else {}
for f in glob.glob('web/backend/**/*.py', recursive=True):
    with open(f) as fh:
        tree = ast.parse(fh.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split('.')[0]
                if top not in stdlib and top != 'web':
                    print(f'{f}: bare import {alias.name}')
"
```

注：`run_packaged_main.py` 是 PyInstaller 入口点，它使用 `import main`（绝对导入）是正确的——它是被 `python run_packaged_main.py` 直接运行的，不在任何包内。

---

## Python 代码风格规范（2026-06-01 新增）

### 1. 导入排序（Import Ordering）

所有 `.py` 文件的 import 语句必须按以下**四组**顺序排列，组间用空行分隔。每组内按字母顺序排序（合理范围内）。

```
组 0：from __future__ import annotations  （如使用，必须是文件第一个 import）
组 1：标准库（json、pathlib、typing 等）
组 2：第三方库（fastapi、pydantic、pytest 等）
组 3：框架库（calc_framework.*）
组 4：本地应用（api.*、games.*、from . import xxx）
```

```python
# ✅ 正确
from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

from calc_framework.logging import get_logger

from . import _path_setup
from api.compute import router

# ❌ 错误：std 和 third-party 混在一起
import json
from fastapi import APIRouter
from pathlib import Path
```

例外：`from . import _path_setup` 在 `web/backend/main.py` 中放第一行（因必须最先执行路径设置）。

### 2. 公共 API 声明（`__all__`）

每个 `__init__.py` 必须声明 `__all__` 来确定模块的公共 API 边界。禁止隐式 exports。

```python
# ✅ 正确
from .ability_bonus_calc import AbilityBonusZone
from .base_zone import BaseZone

__all__ = [
    "AbilityBonusZone",
    "BaseZone",
]

# ✅ 空包
__all__: list[str] = []

# ❌ 错误：没有 __all__，所有模块级名字对外部可见
from .internal_helper import _helper_func, PublicFunc
```

**规则**：
- `__all__` 写在文件末尾，import 语句之后
- 元素是字符串字面量（不是变量引用）
- 排序：先类，后函数，按字母顺序
- 空包必须写 `__all__: list[str] = []`

### 3. 文档字符串格式（Google 风格，中文）

**必须写** docstring 的情况：

- **公共 API**：被其他模块/包 import 的模块、类、函数；`__all__` 中导出的符号
- **Web / FastAPI**：路由 handler、对外 Pydantic 模型（类 docstring）
- **长函数**：函数体（不含 docstring）约 **≥ 40 行**，或分支多、职责不直观

**可不写** docstring 的情况：

- 模块内 **`_` 前缀**短 helper，名称已自解释
- ≤ **3 行**有效代码的 trivial wrapper
- 测试里极小的局部 helper（酌情）

**酌情**：其余内部私有函数——逻辑一眼能懂可不写；算法、边界条件或非 obvious 行为建议写。

```python
def setup_logging(level: str | int | None = None) -> None:
    """全局初始化框架日志系统。

    可在应用入口调用一次。后续重复调用无副作用。

    参数:
        level: 日志级别（"DEBUG" / "INFO" / "WARNING"
               或 logging.DEBUG）。

    Raises:
        ValueError: 日志级别无效。
    """
```

**格式**（与上例一致）：

- 第一行：简短描述（句号结尾，≤80 字符）
- 空一行后：详细描述（可选）
- 段落头：`参数:`、`返回:`、`Raises:`（缩进 4 空格；**中文**）
- 简单公共函数可用单行：`"""获取当前版本号。"""`
- 模块 docstring：放在 `# SPDX-License-Identifier` 之后，第一个 import 之前

**注意**：docstring 与 `#` 行注释不同；本仓库 Agent 默认仍**不主动加 `#` 行注释**（除非用户要求）。

### 4. 自定义异常层级

```python
# ✅ 正确模式
class DAGError(Exception):
    """DAG 引擎所有异常的基类。"""

class DAGCompileError(DAGError):
    """编译期错误。"""
    def __init__(self, message: str, *, node_id: str | None = None) -> None:
        super().__init__(message)
        self.node_id = node_id

# ❌ 错误：没有基类、没有 docstring、没有关键字参数
class BadFormatError(Exception):
    pass
```

**规则**：
- 异常类以 `Error` 后缀结尾（`DAGError`、`SchemaError`）
- 必须有文档字符串描述
- 特定构造参数使用**仅限关键字参数**（`*` 后）
- 异常放在专用 `errors.py` 模块中，或与使用处紧邻
- 层次结构：一个基类 + 若干子类

### 5. Pydantic 模型命名（Web 后端）

```python
# ✅ 正确
class SnapshotRequest(BaseModel):
    char_name: str
    weapon_name: str
    char_level: int = 90
    enemy_defense: float = 100.0
    extra_crit_rate: float = 0.0

class EvaluateResponse(BaseModel):
    outputs: dict[str, float]
    execution_order: list[str]

# ❌ 错误：命名不清晰
class Req(BaseModel):
    name: str

class Res(BaseModel):
    result: dict
```

**规则**：
- 请求体模型：`<名词>Request`
- 响应模型：`<名词>Response`
- 路由装饰器使用 `response_model=` 参数
- 模型定义在路由模块顶部（路由函数之前）

### 6. HTTP 错误码语义（Web 后端）

| 状态码 | 使用时机 | 消息格式 |
|--------|----------|----------|
| 400 | 验证失败、计算错误、无效输入 | `"detail": "验证失败: {原因}"` |
| 404 | 资源不存在（角色、武器、适配器） | `"detail": "角色不存在: {name}"` |
| 409 | 创建时资源已存在 | `"detail": "角色 '{name}' 已存在"` |
| 500 | 服务器内部错误、JSON 解析失败 | `"detail": "服务器内部错误: {exc}"` |

```python
# ✅ 正确
if not char_data:
    raise HTTPException(status_code=404, detail=f"角色不存在: {req.char_name}")

# ❌ 错误：状态码语义错误
if not char_data:
    raise HTTPException(status_code=400, detail="找不到")

# ❌ 错误：无 detail 消息
raise HTTPException(404)
```

### 7. 测试组织规范

**函数命名**：
```python
# ✅ 正确
def test_single_weapon_search():
def test_empty_result_returns_none():

class TestEngine:
    def test_default_config(self):
    def test_custom_timeout(self):

# ❌ 错误
def single_weapon():       # 缺 test_ 前缀
def test():                # 描述性不足
```

**Fixture 组织**（三级层次）：
```
包级 conftest.py          → 全局 fixture（如 _reset_global_calculation_cache）
测试目录 conftest.py      → 目录共享 fixture（如 fixtures_dir）
测试模块内函数            → 单模块独有 fixture
```

**慢测标记**：
- `pytest.mark.slow` — 耗时 > 5 秒的测试
- `pytest.mark.integration` — 依赖外部系统（文件 I/O、DB）
- `pytest.mark.real_data` — 使用真实游戏 JSON 数据
- 慢测文件在包级 `conftest.py` 中通过 `_SLOW_FILES` 集合自动注册

**测试命令规范**：
- 所有 `pytest` 调用**必须去掉 `-q`**，保留默认进度条输出（点号 `...` + 百分比），让用户能判断"卡住"还是"仍在跑"
- 禁止使用 `| Select-Object -Last N` 管道截断 pytest 输出，因为测试跑完前不会显示任何输出
- 少量测试（单个文件，< 50 个用例）可以直接 block；大量测试用 `--timeout=N` + 异步运行
- 禁止 `-q --tb=short` 后用 `Select-Object` 截断导致白屏等待

```powershell
# ✅ 正确：保留进度输出，全量跑完可见
python -m pytest games/endfield/tests/ -v

# ✅ 正确：单个文件快速验证
python -m pytest games/endfield/tests/tools/test_github_upload_signing.py -v

# ❌ 错误：截断输出导致看不到进度
python -m pytest games/endfield/tests/ -q | Select-Object -Last 20
```

### 8. GUI 测试窗口清洁规范

**原则**：测试中打开的每个 GUI 窗口必须保证在测试结束时关闭，否则会阻塞测试流程。

**具体规则**：

| # | 规则 | 正确做法 | 错误做法 |
|---|------|----------|----------|
| 1 | **`show()` 后必须 `close()`** | 调用 `w.show()` 后，在函数末尾调用 `w.close()` | 只 `show()` 不 `close()`，窗口卡死 |
| 2 | **用 try/finally 或 fixture 确保异常时也关闭** | `try: w.show(); ... finally: w.close()` | 测试中途 assert 失败，跳过 `close()` |
| 3 | **CI 中使用 offscreen 模式** | `QT_QPA_PLATFORM=offscreen` 环境变量 | 弹出真实窗口阻塞 CI 流程 |
| 4 | **不创建不关闭的模态对话框** | mock `exec()` / `show()` 调用 | 真实弹出模态对话框阻塞测试 |

```python
# ✅ 正确：show 后 close
w = GraphEditorWidget()
w.add_graph_node(...)
w.show()
try:
    item = w.find_node_item("n")
    assert item is not None
finally:
    w.close()

# ✅ CI 安全：QT_QPA_PLATFORM=offscreen
# powershell: $env:QT_QPA_PLATFORM="offscreen"; pytest ...
# bash: QT_QPA_PLATFORM=offscreen pytest ...

# ❌ 错误：窗口打开后永不关闭
w = GraphEditorWidget()
w.show()
item = w.find_node_item("n")
assert item is not None
# ← w.close() 缺失，窗口卡死
```

### 9. 目录与文件规模（ADR-0001，2026-06-03 修订）

| 项 | 规则 |
|----|------|
| 目录宽度 | 直接子项 **≤ 20（硬顶）**；**目标 ≤ 15**（16–20 时应规划拆分） |
| 文件长度 | 业务 / GUI / 计算 `.py` **≤ 400 行**（硬顶 500） |
| 门禁 | `python tools/check_layout.py --max-lines 400`（默认 `--max-items 20`） |

全文见 [`docs/adr/0001-code-layout-constraints.md`](../../docs/adr/0001-code-layout-constraints.md)、[`docs/代码结构规范.md`](../../docs/代码结构规范.md)。

---

## Pyright / Pylance 类型检查注意（2026-06-04 新增）

### 1. `# type: ignore` 在多行函数调用中的位置

**规则**：`# type: ignore[code]` 必须放在**实际产生错误的行**上。Pyright 不会将调用行的 `# type: ignore` 传播到后续参数行。

```python
# ❌ 错误：ignore 在调用行，对参数行无效（Pyright 仍报错）
result = SearchRunner.run(  # type: ignore[arg-type]
    base_context=object(),   # ← Pyright 在此行报错
    weapons=[],
    config=object(),         # ← Pyright 在此行报错
)

# ✅ 正确：ignore 放在每个参数行
result = SearchRunner.run(
    base_context=object(),  # type: ignore[arg-type]
    weapons=[],
    config=object(),        # type: ignore[arg-type]
)
```

### 2. 循环导入 + `from __future__ import annotations` + dataclass

当以下三个条件同时满足时，Pyright 无法解析 dataclass 的 `__init__` 形参名，导致调用处报"没有名为"（`call-arg`）错误：

1. **A 模块** 是 `@dataclass`，且使用了 `from __future__ import annotations`
2. **B 模块** 从 A 导入该 dataclass 并构造它
3. **A 模块** 在文件底部 re-export B 中的函数（形成 A → B → A 循环）

**修复方式（二选一）**：

```python
# 方案 1（推荐）：打破循环导入
# A.py 底部的 re-export 改为注释，B.py 从 B 自己的路径导入
# A.py
# ── 删掉 re-export，改为注释 ──
# from .B import helper_func  # 删除这行，其他模块直接 import 自 B

# B.py
from .A import MyDataclass  # 单向导入，无循环
```

```python
# 方案 2（仅适用于测试文件）：在调用行加 # type: ignore[call-arg]
state = LoadoutState(  # 每行都加，不只在调用行
    char_data={...},  # type: ignore[call-arg]
)
```

**永久修复**：优先方案 1 打破循环依赖，让 Pyright 能完整解析类签名。

---

## PyInstaller 打包规范（2026-06-01 新增）

### 入口点处理

PyInstaller 打包后，Python 模块导入路径与源码环境不同。入口点必须：

1. **不用命名空间包**：避免 `import web.backend.main`，改为 `import main` 并直接把模块目录加入 `sys.path`
2. **`onedir` 模式下**：
   - `sys._MEIPASS` = exe 所在目录（不是 `_internal/`）
   - 编译后的模块在 `_internal/` 下
   - 数据文件（`--add-data`）在 `sys._MEIPASS` 下
   - 入口点必须将 `_internal/web/backend` 加入 `sys.path`
3. **路径检查**：`Path(_p).is_dir()` 确认目录存在后再加入 `sys.path`

### 数据文件

- 游戏 JSON 数据通过 `stage_release_folder`（`release_layout.py`）复制到 exe 旁
- 前端 dist/ 通过 `--add-data "web/frontend/dist;web/frontend/dist"` 内嵌
- 不要用 `--add-data` 添加 Python 源码（会被 PyInstaller 自动编译），只用它添加纯数据文件

### 构建命令

```powershell
# 推荐：用 main_build.py（支持 incremental build）
python main_build.py --target local-backend

# 直接 pyinstaller
pyinstaller --onedir --console --name "exe名称" `
  --paths framework/src --paths games --paths web/backend `
  --add-data "web/frontend/dist;web/frontend/dist" `
  --add-data "games/endfield;games/endfield" `
  --hidden-import calc_framework --hidden-import games.endfield `
  web/backend/run_packaged_main.py

# 一键构建
python web/build_local_backend.py
```

### 避免的陷阱

| 问题 | 原因 | 正确做法 |
|------|------|----------|
| `import web.backend.main` 失败 | `web` 不是标准 Python 包（无 `__init__.py`），PyInstaller 冻结导入系统无法处理 | `import main` + 把 `_internal/web/backend` 加入 `sys.path` |
| `--onefile` 启动慢 | 每次运行需解压到临时目录 | 改用 `--onedir` |
| 数据文件找不到 | `get_resource_path` 用 `sys.executable.parent` 找 exe 旁文件，但 onefile 模式下数据在 `sys._MEIPASS` | `--onedir` 模式无此问题；或用 `stage_release_folder` 放 exe 旁 |

---

## Web 部署规范（2026-06-01 新增）

### 前端下载按钮

MUI `<Button href="/api/...">` 渲染为 `<a>` 标签，会被 React Router 拦截，导致页面刷新而非下载：

```tsx
// ❌ 错误：被 React Router 拦截
<Button href="/api/download/client">下载</Button>

// ✅ 正确：用 onClick 直接导航
const handleDownload = () => { window.location.href = "/api/download/client"; };
<Button onClick={handleDownload}>下载</Button>
```

### 静态文件下载优先

如果下载文件不依赖后端逻辑，优先用**静态文件**方式，不走后端 API：

```tsx
// ✅ 更好：文件放在 web/frontend/public/ 中，Vite 构建时复制到 dist/
const handleDownload = () => { window.location.href = "/local-backend.zip"; };
```

### 部署脚本必须包含后端文件

`deploy_pythonanywhere.py` 的 `--all` 模式必须同时上传：
1. 前端 dist/ 文件（已有 `_upload_dist_files`）
2. 后端 Python 文件（`_upload_backend_files`）
3. 本地后端 zip（`_upload_local_backend_zip`，如果有）

**不要假设后端代码已通过 git 部署到服务器**。部署脚本应主动上传所有变更文件。

### HTTP 响应头规范

所有下载响应必须使用：
- **ASCII-only 文件名**：中文文件名在 `Content-Disposition` 中可能被编码损坏
- **`Response(content=bytes)`**：不要用 `StreamingResponse(BytesIO)`，WSGI 环境下不稳定
- **`Content-Length`**：必须设置，浏览器依赖它显示下载进度
- **同步 `def`**：PythonAnywhere WSGI 下避免 `async def`（除非用 ASGI）

```python
# ❌ 错误：async + StreamingResponse + 中文文件名
@app.get("/api/download/file")
async def download():
    buf = BytesIO()
    ...
    return StreamingResponse(buf, headers={"Content-Disposition": "attachment; filename=中文.zip"})

# ✅ 正确：sync + Response + ASCII 文件名
@app.get("/api/download/file")
def download():
    content = Path("file.zip").read_bytes()
    return Response(
        content=content,
        media_type="application/zip",
        headers={
            "Content-Disposition": 'attachment; filename="file.zip"',
            "Content-Length": str(len(content)),
        },
    )
```

---

## 许可证扫描与代码来源检查规范（2026-06-02 更新）

### 扫描工具

| 工具 | 用途 | 安装 |
|------|------|------|
| `scancode-toolkit` | 深层许可证/版权/来源检测（权威） | `pip install scancode-toolkit` |
| `check_code_origin.py` | 快速 SPDX/版权/许可证头检查（轻量） | 无需安装 |
| `pip-licenses` | Python 依赖许可证清单 | `pip install pip-licenses` |

### 扫描策略

**不要用 `--ignore` 模式扫描整个仓库根目录**——scancode 的 `--ignore` 会触发极其缓慢的预扫描过滤阶段（大项目耗时 10+ 分钟），且容易意外匹配过多文件。

**正确做法：只指定源代码目录作为输入路径**，不使用 `--ignore`。

内存注意：scancode 默认启动 CPU 线程数个并行进程（本机 24 线程），每个进程加载一次许可证数据库（~150 MB），峰值内存可能达到 3.6 GB。已在脚本中限制 `--processes 16`（物理核心数），峰值约 2.4 GB。

### 命令示例

```bash
# [推荐] 权威扫描（逐个目录扫描，安全稳定）
python tools/run_scancode.py

# [推荐] 快速 AI 代码来源检查（1 秒出结果，50 MB 内存）
python tools/check_code_origin.py

# 依赖许可证检查（轻量）
pip-licenses --with-system --format=markdown

# 代码重复检查 (jscpd)
npx jscpd --pattern "**/*.py" --ignore "**/node_modules/**" --ignore "**/__pycache__/**" --ignore "**/dist/**" --ignore "**/build/**" --ignore "**/.venv/**"
```

### 游戏包架构标准（框架优先原则）

所有游戏包（`games/{game}/`）必须严格遵循以下架构规则。

#### A. 计算层 — 纯 DAG 适配器架构

- 所有计算逻辑在 `framework/adapters/{game}/functions.py` 中，以 DAG 可调用函数注册
- `games/{game}/` 是薄包，只做数据加载 + DAG 适配 + 轻量 GUI
- 不允许"本地引擎 + DAG 引擎"双轨并存
- DAG 定义在 `framework/adapters/{game}/dag/{game}_full.dag.json` 中

#### B. GUI 层 — ComputeSheet 声明式面板

- 主窗口必须继承 `QMainWindow`，使用 `ComputeSheet` + 游戏特有选择面板
- 所有输入/输出面板通过 `layout.json` 声明，由 `ComputeSheet.widget` 自动生成
- `layout.json` 必须使用 `user_input` 源（source）变量 + `user_context_overrides` 映射到 DAG context
- 禁止手写大量 QGroupBox/QGridLayout 替代 ComputeSheet

#### C. 框架桥接层

- 每个游戏包必须有 `framework_bridge.py`，集中管理所有 `calc_framework.*` 导入
- GUI 层不得直接 `from calc_framework` 导入，必须通过 `framework_bridge.py` 间接访问

#### D. 参考实现

- 终末地（`games/endfield/`）和明日方舟（`games/arknights/`）均已对齐框架规范
- 新游戏适配时以 `docs/game-template/` 为模板，参照终末地/方舟的具体实现
- 迁移路线图见 `docs/plans/game-architecture-migration-plan.md`

### 两套工具的适用场景

| 场景 | 推荐工具 | 原因 |
|------|----------|------|
| 日常快速检查 AI 有无抄袭 | `check_code_origin.py` | 1 秒，50 MB 内存，只查源代码 |
| 发布前权威审查 | `run_scancode.py` | 内置 1000+ 许可证数据库，逐个目录安全扫描 |
| 收到他人 PR 时审查 | `check_code_origin.py --ci` | 支持 CI 模式 |
| 合规审计/法律需求 | `run_scancode.py` | 输出完整 JSON 报告供存档 |

### 内存与性能说明

- **波浪式内存**：scancode 用多进程并行扫描，每批文件处理完释放内存再处理下一批，形成内存波浪（20%→100%→20%）。这是正常的多进程模式，不是泄漏。
- **本机配置**：Intel Core i7-14650HX（8 P-core + 8 E-core = 16 物理核 / 24 线程），`--processes 16` 用满所有物理核。
- **规避方案**：如果内存吃紧，可临时改为 `--processes 2`（内存 ~300 MB 稳定，速度慢一些）。

---

## 文档位置规范（2026-06-03 新增）

### 核心原则

**所有项目文档集中存放在 `docs/` 目录下。** 除非有特殊理由（如下文列出的例外），不得在 `docs/` 外创建文档文件。

### 文档目录结构

```
docs/
├── README.md                   # 文档索引
├── 项目目标.md                  # 长远愿景与当前焦点
├── 会话接续手册.md              # 项目状态、架构接缝、近期完成（当前月）
├── 会话接续手册-2026-05.md      # 2026 年 5 月历史归档
├── 操作指令集.md                # 人类操作指南
├── 代码结构规范.md              # 目录布局约束
├── 框架适配新游戏指南.md         # 新游戏适配指引
├── 制造游戏计算器完整流程.md      # GUI 功能流程
├── 数据来源与许可.md             # 数据来源与许可信息
├── GUI使用说明.md                # GUI 操作说明
├── 用户计算器创建手册.md          # 用户创建计算器手册
├── 算法与架构.md                 # 算法架构说明
├── 依赖说明.md                   # 依赖管理说明
├── 快速上手.md (quickstart.md)   # 快速开始
├── PythonAnywhere-部署指南.md    # Web 部署
├── 框架对齐分析.md               # 架构对齐分析
├── 代码规范-ruff修复模式.md       # Ruff 代码规范
├── MVP搜索验收说明.md             # MVP 验收
├── 商业许可要点.md               # 商业许可提纲
├── 合规自查清单.md               # 发布前合规检查
├── 商业许可要点.md               # 商业许可
├── migration-pyside6.md         # PySide6 迁移记录
├── CONTRIBUTORS.md              # 贡献者列表
├── AI-计算器生成指南.md           # AI 生成指引
├── AI-Prompt模板.md              # Prompt 模板
├── nga-46094556-终末地机制对照与待办.md  # 机制对照
├── adr/                         # 架构决策记录（23 份）
│   ├── 0001-code-layout-constraints.md
│   ├── 0002-migrate-to-pyside6.md
│   ├── 0002-formula-graph-editor.md
│   ├── 0003-generic-calc-framework.md
│   ├── ...
│   └── 0023-standardized-game-package-architecture.md
├── agents/                      # Agent 运行相关文档
│   ├── domain.md
│   ├── triage-labels.md
│   ├── issue-tracker.md
│   └── encoding-corruption-handling.md
├── plans/                       # 长期计划
│   └── game-architecture-migration-plan.md
└── game-template/               # 游戏模板文档
    └── README.md
```

### 根目录和子包中的文档文件

以下文档文件**不在** `docs/` 下，但有明确的用途，不应移入 `docs/`：

| 文件 | 用途 | 不移入的原因 |
|------|------|-------------|
| `README.md`（根） | 项目总述、快速链接 | GitHub 仓库首页必须 |
| `CONTEXT.md`（根） | 领域术语表 | 被多个 Agent 技能/规则引用 |
| `CONTRIBUTING.md`（根） | 贡献指南 | GitHub 标准惯例 |
| `AGENTS.md`（根） | Agent 技能配置 | Agent 工具链必须 |
| `NOTICES.md`（根） | 法律声明 | 根目录惯例 |
| `games/*/README.md` | 游戏包说明 | 各游戏包自包含 |
| `framework/README.md` | 框架说明 | 框架包自包含 |
| `tools/README.md` | 工具目录说明 | 工具目录自包含 |
| `tools/bwiki_scout/README.md` | BWIKI 工具说明 | 工具子包自包含 |
| `tools/bwiki_scout/CACHE.md` | 缓存说明 | 工具子包自包含 |

### 禁止行为

- **禁止**在 `docs/` 之外创建新的 `.md` 文档文件，除非有上述"不移入"的充分理由
- **禁止**将 Agent 技能定义文件（`.agents/skills/`、`.trae/skills/`）当作项目文档管理——它们是 AI 工具配置，不属于项目文档
- **禁止**保留临时 lint 报告（如 `ruff_*.txt`）、一次性分析输出等**产物文件**在仓库中

### 清理规则

以下文件类型不属于项目文档，不得提交到仓库：

| 类型 | 举例 | 处理方式 |
|------|------|----------|
| 临时 lint 报告 | `ruff_*.txt`、`_ruff_report.txt` | 立即删除 |
| 一次性分析输出 | 扫描报告、临时 diff | 用后即删 |
| 构建产物文档 | `build/*.md`、`dist/*.md` | 在 `.gitignore` 中排除 |

## 开发工作流（完整发布周期）

当一个开发周期从开始到交付时，按以下步骤执行。**每一步完成后确认，再进入下一步。**

### 阶段一：规划与目标

1. **设定目标** — 明确本次要做什么（功能实现 / Bug 修复 / 重构 / 文档）。写入 `.trae/plans/当前任务计划.md`。
2. **确认范围** — 确认只做计划中的事，不扩展范围。
3. **先行阅读** — 按「先行阅读」规则读取所需文档。

### 阶段二：实现

4. **实现目标** — 按 `design-then-build` 工作流（先 grill-me 厘清设计，再 TDD 实现）。默认低风险操作自动同意，高风险操作问用户。

### 阶段三：文档同步

5. **更新文档** — 按「任务完成收尾协议」更新受影响的文档。**在代码改完之后先更新文档，不要等最后。**

### 阶段四：验证

6. **确认测试** — 运行全量测试确认 pass：
   ```bash
   python -m pytest games/endfield/tests/ framework/tests/ games/arknights/tests/ -v
   ```
   - 如有新增模块，编写对应测试，确保新代码有 >80% 行覆盖
7. **确认依赖打包** — 如果新增了 pip 依赖：
   - 更新对应 `pyproject.toml` 的 `[project.dependencies]`
   - 确认依赖已在 `setup.cfg` / `requirements*.txt` 中声明

### 阶段五：入口与配置

8. **集中使用入口** — 检查所有入口脚本：
   - `scripts/main.py`（终末地计算器）
   - `scripts/main_arknights.py`（明日方舟）
   - `scripts/main_designer.py`（数据设计器）
   - `scripts/main_build.py`（打包）
   - `scripts/启动本地服务器.bat`（Web 本地）
   - 确认新增功能有对应的入口，入口使用 `_path_setup` 模式

### 阶段六：Bug 检查

9. **本地 Bug 检查**：
   - **Web 端**：运行 `cd web/frontend; npx tsc --noEmit` 确认 0 类型错误；运行 `npm run lint` 确认 0 lint 错误
   - **桌面端**：启动对应 GUI，手动检查核心功能是否正常
   - **打包检查**：如果改动了打包逻辑，运行 `python scripts/main_build.py --target {目标}` 确认能成功
10. **检查忽略文件** — 检查 `.gitignore` 是否遗漏了不应该提交的产物（`dist/`、`build/`、`*.spec`、`.venv/`、`__pycache__/`、`*.log` 等）

### 阶段七：全量更新

11. **全量更新文档** — 重新检查所有受影响的文档是否与代码一致：
    - `docs/会话接续手册.md` — 文首日期、§3 目录、§4 近期完成
    - `docs/操作指令集.md` — 新增命令、参数或流程
    - `docs/框架适配新游戏指南.md` — 新增适配包、API 变更
    - `docs/代码结构规范.md` — 新增/删除目录超限记录
    - `docs/制造游戏计算器完整流程.md` — GUI 功能变化
    - `README.md`（根和各 `games/*/`）— 功能描述、目录列表
    - `CONTEXT.md` — 新增术语
12. **打包与 Web 更新**：
    - 需要发布本地 exe：运行 `python scripts/main_build.py --target {目标}`
    - Web 有变更：确认前端已 build 通过（`npm run build`），后端依赖已锁
13. **删除计划文件** — 删除 `.trae/plans/当前任务计划.md`

### 阶段八：发布

14. **输出任务总结** — 列出已完成项 + 未完成项 + 当前暂存区状态
15. **向用户提问后续** — "需要上传 GitHub 吗？"等
16. **用户执行上传** — 默认由用户在仓库根目录执行 `python github_upload_module.py`（可选 `--minor` / `--no-bump`）。Agent **不得**主动执行上传。

---

## 规则同步

本仓库存在多个规则/配置文件的 Agent 使用：

| 文件 | 用途 | 适用环境 |
|------|------|----------|
| `.trae/rules/project_rules.md` | 主规则文件（最完整） | Trae IDE |
| `.cursorrules` | Cursor 兼容规则 | Cursor IDE |
| `AGENTS.md` | 项目级 Agent 技能配置 | Trae / Cursor / 通用 |

### 同步规则

1. **主文件**：`.trae/rules/project_rules.md` 是权威源（最完整、最新）。
2. **修改规则时**：
   - 先在 `project_rules.md` 中写入修改
   - **立即同步**到 `.cursorrules` 中对应的章节（保持相同内容的版本一致）
   - `AGENTS.md` 是轻量入口指引，不是完整规则副本。仅同步 Agent 行为相关的顶级规则（会话接续必读文档、上传/下载策略等）。`AGENTS.md` 应引用 `project_rules.md` 作为详细规则来源，而非复制全部内容。
3. **不同步的内容**：
   - 环境特定的编码规则（如 trae-sandbox 保护规则只适用于沙箱环境）
   - IDE 特性的配置
4. **同步检查**：每次更新 `project_rules.md` 后，检查 `.cursorrules` 是否过时，若有过时则立即同步。
5. **违反后果**：不同步导致两个 IDE 下 Agent 行为不一致，责任归属于修改规则时未同步的人。

---

## 引用来源

本规则整合自：
- [`AGENTS.md`](../../AGENTS.md) — 会话接续、项目操作、推送/拉取、默认工作流
- 用户指令 — 任务计划记录、CI 配置、删除操作规范、禁止的操作红线
- 2026-05-30 复现实验 — trae-sandbox 环境幻觉防护（`git rm` 触发 stat 缓存导致虚假 ` D`）
- 2026-06-01 实践经验 — PyInstaller 命名空间包处理 + Web 部署端点与前端下载规范
- 2026-06-01 显式导入原则 — 从 PyInstaller 命名空间包故障归纳，确立包内相对导入/入口绝对导入/包目录必须含 `__init__.py` 等规则
- 2026-06-01 代码风格规范 — 归纳代码库实际使用的 7 条未文档化约定（导入排序、__all__、Google 风格文档字符串、异常层级、Pydantic 模型命名、HTTP 错误码语义、测试组织规范）
- 2026-06-01 开发工作流 — 完整发布周期 16 步流程（目标→实现→文档→验证→入口→Bug检查→全量更新→发布）
- 2026-06-01 规则同步 — .trae/rules/project_rules.md / .cursorrules / AGENTS.md 三文件同步约定
