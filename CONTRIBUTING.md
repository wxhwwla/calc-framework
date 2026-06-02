# 贡献指南

欢迎来到 **终末地伤害计算器** 项目！感谢你愿意花时间让这个工具变得更好。

## 目录

- [开始之前](#开始之前)
- [Issues：报告问题与提出建议](#issues报告问题与提出建议)
- [Pull Requests：提交代码](#pull-requests提交代码)
- [开发环境搭建](#开发环境搭建)
- [代码规范](#代码规范)
- [测试要求](#测试要求)
- [数据贡献](#数据贡献)
- [许可证](#许可证)

## 开始之前

### 需要了解的知识

| 领域 | 最低要求 | 推荐材料 |
|------|---------|---------|
| Python | 基础语法 | Python 官方教程 |
| PySide6 | 了解信号/槽机制 | Qt for Python 文档 |
| DAG 计算 | 了解有向无环图概念 | `docs/框架适配新游戏指南.md` |
| 游戏机制 | 熟悉目标游戏的伤害公式 | 游戏 Wiki |

### 与本项目已有贡献者交流

遇到问题可以先查阅已有文档，或通过 Issues 提问。

## Issues：报告问题与提出建议

### 报告 Bug

1. 使用 **Bug 报告模板** 创建 Issue
2. 尽量提供完整的复现步骤、期望结果与实际结果
3. 如果是计算错误，请附上计算过程截图或日志
4. 标签会自动设置为 `needs-triage`，维护者会尽快确认

### 提出功能建议

1. 使用 **功能建议模板** 创建 Issue
2. 清晰描述"想解决什么问题"而不是"想加什么功能"
3. 如果已有类似 Issue，可以在原 Issue 下补充评论

### 标签说明

| 标签 | 含义 |
|------|------|
| `needs-triage` | 待分类（新 Issue 默认） |
| `needs-info` | 需要更多信息 |
| `good-first-issue` | 适合新贡献者 |
| `help-wanted` | 需要社区帮助 |
| `ready-for-agent` | 适合 AI Agent 处理 |
| `ready-for-human` | 需要人工审查 |
| `bug` | 确认的 Bug |
| `enhancement` | 功能增强 |
| `wontfix` | 暂不处理 |

## Pull Requests：提交代码

### 工作流程

```
Fork → Clone → Branch → Commit → Test → Push → PR → Review → Merge
```

### 步骤详解

1. **Fork 仓库**：点击 GitHub 页面右上角的 Fork 按钮
2. **Clone 到本地**：`git clone https://github.com/你的用户名/endfield_damage_calculator.git`
3. **创建分支**：从 `main` 分支创建特性分支
   - 功能分支：`feat/简短描述`（如 `feat/ak-operator-search`）
   - 修复分支：`fix/简短描述`（如 `fix/skill-multiplier-bug`）
   - 文档分支：`docs/简短描述`（如 `docs/readme-update`）
4. **编码**：遵循代码规范
5. **本地测试**：确保全量测试通过
6. **Push 到远程**：`git push origin 你的分支名`
7. **创建 PR**：在 GitHub 上点击 "New Pull Request"，填写变更说明
8. **等待 Review**：维护者会在 1-3 个工作日内 Review

### PR 规范

| 项目 | 要求 |
|------|------|
| 标题 | 清晰概括变更内容（50 字以内） |
| 描述 | 说明"为什么改"+"怎么改"+"测试验证结果" |
| 改动范围 | 尽量小，一个 PR 只解决一个问题 |
| 测试 | 新增功能必须有对应的测试 |
| 文档 | 用户可见的变更需同步更新相关文档 |
| 类型检查 | TypeScript（Web 端）必须 `tsc --noEmit` 0 错误 |

### Review 流程

1. PR 提交后自动触发 CI
2. 维护者 Review 代码，必要时提出修改意见
3. 所有讨论 resolved 后，由维护者 Merge

## 开发环境搭建

### 基础环境

```bash
# 克隆仓库
git clone https://github.com/your-org/endfield_damage_calculator.git
cd endfield_damage_calculator

# 创建虚拟环境（确保 UTF-8 编码）
$env:PYTHONUTF8 = "1"
chcp 65001 > $null
python -m venv .venv
.venv\Scripts\Activate.ps1

# 安装依赖
pip install -e .                              # 框架 + 游戏包
pip install -e ".[dev]"                       # 开发依赖（pytest 等）
pip install -r web/backend/requirements.txt   # Web 后端
cd web/frontend && npm install && cd ../..    # Web 前端
```

### 运行测试

```bash
# 全量测试
python -m pytest games/endfield/tests/ framework/tests/ games/arknights/tests/ -q

# 某个模块
python -m pytest games/endfield/tests/test_calculation.py -v

# Web 前端类型检查
cd web/frontend && npx tsc --noEmit
```

### 开发者工具箱

```bash
python devtool.py check-deps      # 依赖自检
python devtool.py check-layout    # 代码布局门禁
python devtool.py sync-bwiki      # BWIKI 数据同步
python devtool.py scaffold        # 新游戏适配脚手架
```

## 代码规范

完整的代码规范请阅读 [`.trae/rules/project_rules.md`](.trae/rules/project_rules.md) 中"Python 代码风格规范"部分。

### 快速参考

| 规则 | 说明 |
|------|------|
| 导入排序 | 标准库 → 第三方 → 框架库 → 本地应用，组间空行 |
| 文档字符串 | Google 风格三段式 |
| 类型注解 | 所有公共函数必须有类型注解 |
| 测试覆盖率 | 新代码 >80% 行覆盖 |
| 异常定义 | 继承 `DAGError` 基类，使用关键字参数 |

### Web 前端规范

- 使用 MUI v6 组件，遵循现有的排版模式
- 使用 TypeScript，严格模式
- 新状态用 zustand store，不要 prop drilling
- API 调用放在 `src/api/` 下

## 测试要求

### 什么时候写测试

- 新增功能 → 写功能测试
- 修复 Bug → 先写复现测试，再修代码
- 重构 → 确保现有测试全通过

### 测试运行

```bash
# 全量
python -m pytest games/endfield/tests framework/tests games/arknights/tests -q

# 某个文件
python -m pytest games/endfield/tests/tools/test_bwiki_scout.py -v

# Web 前端
cd web/frontend && npx tsc --noEmit && cd ../..
```

### CI 检查项

| 检查 | 说明 |
|------|------|
| 全量 pytest | 所有测试必须通过 |
| 前端类型检查 | `tsc --noEmit` 0 错误 |
| 代码布局门禁 | `devtool.py check-layout` 必须通过 |
| 许可证扫描 | 新代码不得含有未经授权的第三方代码 |

## 数据贡献

如果你不是开发者，但想贡献游戏数据（角色数值、武器数值等）：

### 简易方式（推荐非技术用户）

1. 打开 Web 版 → 数据贡献页
2. 使用"简易录入"表单填写数据
3. 下载生成的 JSON 文件
4. 在 GitHub 上以 Issue 或 PR 附件形式提交

### 标准方式

1. 使用 `tools/data_sandbox/` CLI 工具在本地验证数据
2. 确保通过 schema 校验：「`python -m tools.data_sandbox.sandbox validate 你的文件.json`」
3. 生成完整报告：「`python -m tools.data_sandbox.sandbox report 你的文件.json -o 报告.md`」
4. 将数据和报告一起提交 PR

### BWIKI 数据维护者

- 运行增量同步：`python devtool.py sync-bwiki --apply --bump-version`
- 运行数据验证：`python devtool.py sync-bwiki --apply --bump-version --verify`
- 手动查看数据版本：`python -m tools.bwiki_scout.bump_data_version`

## 许可证

- 代码部分：AGPL-3.0
- 游戏数据部分：详见 [`DATA_LICENSE`](DATA_LICENSE) 和 [`docs/数据来源与许可.md`](docs/数据来源与许可.md)
- 提交代码即表示你同意将你的贡献以 AGPL-3.0 许可发布
