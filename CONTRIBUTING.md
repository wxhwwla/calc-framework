# 贡献指南

> 感谢你考虑为 Calc Framework 项目贡献代码！🎉

本指南帮助你了解如何参与开发、提交 Issue、创建 PR 以及为游戏适配包做贡献。

Calc Framework 是一个多游戏伤害计算框架，包含 PySide6 桌面 GUI、React + FastAPI Web 前端/后端、Python DAG 计算引擎、BWIKI 数据采集工具、AI 计算器生成器以及 Docker 部署支持。

项目概述见 [`README.md`](README.md)，领域术语见 [`CONTEXT.md`](CONTEXT.md)，日常操作命令见 [`docs/操作指令集.md`](docs/操作指令集.md)。

---

## 行为准则

本项目采用简洁的行为准则：**互相尊重，就事论事**。

- 讨论时保持友善和理性
- 承认不同水平——欢迎新贡献者，也尊重资深开发者
- 不接受人身攻击、歧视性言论或恶意挑衅

严重违反者将被暂时或永久封禁。

---

## 快速开始

### 环境要求

| 工具 | 版本要求 |
|------|----------|
| Python | 3.10+（推荐 3.12） |
| Node.js | 18+（仅 Web 前端开发需要） |
| Git | 最新稳定版 |

### 1. 克隆仓库

```bash
git clone git@github.com:wxhwwla/calc-framework.git
cd calc-framework
```

### 2. 创建虚拟环境（重要）

Windows 系统下，**创建 venv 前必须先设置 UTF-8 编码**，否则 pip 安装含 Unicode 字符的包时可能损坏文件：

```powershell
# PowerShell
$env:PYTHONUTF8 = "1"
chcp 65001 > $null

python -m venv .venv
.venv\Scripts\activate
```

```bash
# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. 安装依赖

```powershell
# 安装通用计算框架（可编辑模式）
python -m pip install -e framework

# 安装游戏包（终末地）+ 开发依赖
cd games/endfield
pip install -e ".[dev]"

# 如果需要打包 exe
pip install -e ".[build]"

# 回到仓库根目录
cd ../..
```

安装选项说明：

| 选项 | 包含 | 用途 |
|------|------|------|
| `.[dev]` | pytest、pyyaml 等 | 日常开发 |
| `.[build]` | PyInstaller | 打包 exe |
| `.[ocr]` | TorchVision、EasyOCR | 截图识装功能 |

### 4. 安装前端依赖（仅 Web 开发）

```powershell
cd web/frontend
npm install
cd ../..
```

### 5. 运行测试确认环境正常

```powershell
python -m pytest games/endfield/tests/ framework/tests/ games/arknights/tests/ -q
```

测试全部通过即表示环境就绪。

---

## 项目结构概览

```
calc-framework/
├── framework/                      # 通用计算框架（独立 pip 包 calc-framework）
│   ├── src/calc_framework/         #   核心代码
│   │   ├── dag/                    #     DAG 求值引擎（9 种节点、拓扑排序、AST 沙箱）
│   │   ├── data/                   #     数据引擎（DataContext、Schema）
│   │   ├── ui/                     #     声明式 UI（ComputeSheet、CalcPackViewer）
│   │   ├── search/                 #     搜索/枚举引擎
│   │   ├── plugin/                 #     插件系统（暴击/闪避/距离衰减）
│   │   └── config/                 #     适配器管理器
│   └── adapters/                   #   游戏适配器目录（自动发现）
│       ├── endfield/               #     终末地适配器
│       ├── arknights/              #     明日方舟适配器
│       ├── card_rpg/               #     卡牌RPG（验证用）
│       ├── moba/                   #     MOBA 公式（验证用）
│       └── fps/                    #     FPS 公式（验证用）
├── games/                          # 游戏适配包
│   ├── endfield/                   #   终末地伤害计算器
│   │   ├── calc/                   #     计算引擎
│   │   ├── data/                   #     游戏 JSON 数据
│   │   ├── data_loading/           #     数据加载层
│   │   ├── gui/                    #     PySide6 GUI 界面
│   │   ├── tests/                  #     pytest 测试
│   │   └── scripts/                #     包内维护脚本
│   └── arknights/                  #   明日方舟适配包
│       ├── calc/dag_adapter/       #     DAG 适配桥接
│       └── tests/                  #     37 个 pytest
├── web/                            # Web 版（React + FastAPI）
│   ├── backend/                    #   FastAPI 后端
│   │   └── api/                    #     API 路由模块
│   ├── frontend/                   #   React 前端
│   │   └── src/
│   │       ├── pages/              #     页面级组件
│   │       ├── components/         #     通用组件
│   │       ├── store/              #     Zustand 状态管理
│   │       └── api/                #     API 调用封装
│   └── hub/                        #   Calc Hub 静态市场主页
├── tools/                          # 仓库维护工具
│   ├── bwiki_scout/                #   BWIKI 数据侦察与同步
│   ├── data_pipeline/              #   数据 ETL 工具链
│   ├── data_sandbox/               #   数据沙箱（隔离测试）
│   ├── designer/                   #   配置包设计器
│   ├── ocr/                        #   截图识装管线
│   └── generator/                  #   AI 计算器生成器模板
├── scripts/                        # 入口脚本
│   ├── main.py                     #   终末地伤害计算器
│   ├── main_launcher.py            #   统一启动器
│   ├── main_designer.py            #   数据设计器
│   ├── main_build.py               #   多目标打包
│   ├── main_generator.py           #   AI 计算器生成器
│   ├── devtool.py                  #   开发者工具
│   ├── github_upload_module.py     #   GitHub 上传脚本
│   └── github_download_module.py   #   GitHub 下载脚本
├── docs/                           # 项目文档
├── .github/workflows/              # CI 工作流（ci.yml、release.yml 等）
├── Dockerfile                      # Docker 部署
├── docker-compose.yml              # Docker Compose
├── CONTEXT.md                      # 领域术语
├── LICENSE                         # 软件许可证（AGPL-3.0）
└── DATA_LICENSE                    # 数据许可证
```

> **目录约束**：任意目录下直接子项 **≤ 20（硬顶）**、**目标 ≤ 15**；业务 `.py` 文件 ≤ 400 行（硬顶 500）。详见 [`docs/代码结构规范.md`](docs/代码结构规范.md) 和 [`docs/adr/0001-code-layout-constraints.md`](docs/adr/0001-code-layout-constraints.md)。

---

## 开发工作流

### 代码风格

本项目使用 **ruff** 进行 Python 代码格式化与检查：

```powershell
# 检查所有 Python 代码
python -m ruff check games/ framework/src/ tools/ web/backend/
```

代码风格要点见 `.trae/rules/project_rules.md` 中的「Python 代码风格规范」：

- **导入排序**：`future → 标准库 → 第三方 → 框架 → 本地应用` 四组顺序
- **公共 API**：每个 `__init__.py` 必须声明 `__all__`
- **文档字符串**：公共 API 与长函数（≥40 行）用 Google 风格（中文）；内部短 helper 可不写
- **异常层级**：以 `Error` 结尾，基类 + 子类
- **测试命名**：`test_` 前缀

### 类型检查

```powershell
# Python 类型检查
pip install pyright
pyright

# TypeScript 类型检查（仅 Web 前端）
cd web/frontend && npx tsc --noEmit
```

### 运行测试

```powershell
# 全量测试
python -m pytest games/endfield/tests/ framework/tests/ games/arknights/tests/ -q

# 带覆盖率
python -m pytest games/endfield/tests/ --cov=games.endfield --cov-report=term-missing

# 运行特定测试
python -m pytest games/endfield/tests/test_calculation.py -v

# Web E2E 测试
cd web/frontend && npm run cypress:run
```

### 前端构建检查

```powershell
cd web/frontend
npx tsc --noEmit    # 类型检查
npm run build       # 构建
```

### CI 工作流

本项目配置了多个 GitHub Actions 工作流：

| 工作流 | 触发条件 | 作用 |
|--------|----------|------|
| `ci.yml` | push/PR 到 main | 终末地方舟测试 + ruff lint + 覆盖率门槛 60% |
| `framework-ci.yml` | push/PR 到 main | 框架层 374 测试 + 跨品类适配器验证 |
| `release.yml` | `v*` 标签推送 | 打包 exe + 创建 GitHub Release |
| `layout-sync.yml` | PR 涉及 layout 文件 | 验证布局同步一致性 |
| `code-origin-check.yml` | 每周一 | AI 代码来源/版权扫描 |
| `web-e2e.yml` | push/PR 到 main | Cypress E2E 测试 |

提交 PR 前，确保 CI 全部通过。

---

## 做出修改

### 分支命名

```text
feature/xxx        # 新功能
fix/xxx            # Bug 修复
refactor/xxx       # 重构
docs/xxx           # 文档变更
chore/xxx          # 构建/CI/工具
```

建议分支名用英文，简短描述即可。例如：`fix/search-panel-crash`、`feature/add-moba-adapter`。

### 提交信息

本项目使用上传脚本管理版本号和提交信息，通常不建议直接 `git commit`。但如果需要手动提交：

```
<类型>: <简短描述>

<可选详细说明>
```

示例：

```
fix: 修复全量搜索面板在高分辨率下布局错位

- 修复 QSplitter 初始比例计算
- 增加最小宽度保护
```

> 完整发布流程见 [`docs/操作指令集.md`](docs/操作指令集.md) 和 [`scripts/please_read_me.py`](games/endfield/please_read_me.py) 中的 `UPLOAD_WORKFLOW`。

### 保持专注

每个 PR 只做一件事。如果你的修改涉及多个不相关的问题，请拆分为多个 PR。

---

## 新增游戏适配器

本框架通过适配器系统支持多款游戏。新增游戏适配器的推荐方式：

### 方式一：使用 AI 生成器（推荐给新手）

```powershell
python scripts/main_generator.py
```

此交互式工具引导你完成：选模板 → 填写游戏信息 → 生成适配器骨架 → 预览导出。

### 方式二：手动脚手架

参考模板目录 `docs/game-template/` 和已有适配器实现：

1. 在 `framework/adapters/` 下创建游戏目录
2. 编写 `meta.json`（适配器元信息）
3. 编写 DAG 公式定义（`<game>.dag.json`）
4. 编写 `attr_schema.json`（变量属性描述）
5. 编写 UI 布局（`ui/layout.json`）
6. 实现自定义纯函数（`functions.py`，可选）
7. 添加游戏数据文件（`data/`，可选）

详细步骤见 [`docs/框架适配新游戏指南.md`](docs/框架适配新游戏指南.md)。

### 架构原则

- **纯 DAG 适配器架构**：所有计算逻辑在 `framework/adapters/{game}/functions.py` 中以 DAG 可调用函数注册
- **薄游戏包**：`games/{game}/` 只做数据加载 + DAG 适配 + 轻量 GUI
- **单计算路径**：一个公式只有一个实现源头，不存在需要同步的两套代码

---

## 提交变更

### PR 检查清单

提交 PR 前，请确认以下项目：

- [ ] 代码通过 ruff lint：`python -m ruff check games/ framework/src/`
- [ ] Python 类型检查通过：`pyright`
- [ ] 全量测试通过：`python -m pytest games/endfield/tests/ framework/tests/ games/arknights/tests/ -q`
- [ ] 新代码有对应的单元测试
- [ ] Web 前端（若有改动）：`cd web/frontend && npx tsc --noEmit && npm run build` 通过
- [ ] 未违反目录超限规则（子项 ≤ 20，目标 ≤ 15）
- [ ] 未违反文件长度规则（业务 `.py` ≤ 400 行，硬顶 500）
- [ ] 新 `__init__.py` 声明了 `__all__`
- [ ] 遵循显式导入原则（包内相对导入，包目录有 `__init__.py`）
- [ ] 文档已同步更新（如有影响）

### CI 要求

- 所有 CI 工作流必须通过
- 覆盖率不得显著下降（CI 门槛 60%）
- 新增依赖须经许可证检查（禁止 GPL-3.0、SSPL 等传染性许可）

### PR 流程

1. Fork 本仓库
2. 创建你的特性分支（`git checkout -b feature/xxx`）
3. 提交修改（注意：大改动建议先开 Issue 讨论）
4. 推送到你的 Fork（`git push origin feature/xxx`）
5. 在 GitHub 上创建 Pull Request
6. 等待 Review 和 CI 通过

---

## Bug 报告与功能建议

我们使用 [GitHub Issues](https://github.com/wxhwwla/calc-framework/issues) 跟踪问题。

### Bug 报告

提交 Bug 报告时，请尽量提供：

1. **复现步骤**：详细的操作步骤，他人可按此复现
2. **期望行为**：正常情况下应发生什么
3. **实际行为**：实际发生了什么
4. **环境信息**：操作系统、Python 版本、项目版本（窗口标题中的版本号）
5. **截图/日志**：终端报错或截图

Bug 报告模板位于 `.github/ISSUE_TEMPLATE/bug_report.yml`，填写时会自动引导。

### 功能建议

提交功能建议时，请说明：

1. **问题或动机**：现在哪里不方便？你想达成什么目标？
2. **建议方案**：你期望产品如何表现？
3. **备选方案**（可选）：考虑过哪些替代做法？

功能建议模板位于 `.github/ISSUE_TEMPLATE/feature_request.yml`。

### 标签说明

| 标签 | 含义 |
|------|------|
| `needs-triage` | 待分拣（新 Issue 默认） |
| `needs-info` | 需要更多信息 |
| `ready-for-agent` | 可由 AI Agent 处理 |
| `good-first-issue` | 适合新贡献者的友善问题 |
| `help-wanted` | 需要帮助 |
| `wontfix` | 决定不修复 |

---

## 文档

项目的所有文档位于 `docs/` 目录，使用 Markdown 格式。

### 文档修改守则

- 改代码后同步更新相关文档——**不要等最后**
- 文档使用 UTF-8 编码（无 BOM）
- 如果你新增了一个功能，记得更新对应的文档

### 关键文档

| 文件 | 内容 | 何时更新 |
|------|------|----------|
| [`docs/会话接续手册.md`](docs/会话接续手册.md) | 架构状态、近期完成 | 每次完成功能后 |
| [`docs/操作指令集.md`](docs/操作指令集.md) | 日常命令 | 新增命令或参数时 |
| [`docs/代码结构规范.md`](docs/代码结构规范.md) | 目录/文件约束 | 结构性变更时 |
| [`docs/框架适配新游戏指南.md`](docs/框架适配新游戏指南.md) | 适配器开发 | API 变更时 |
| [`CONTEXT.md`](CONTEXT.md) | 领域术语 | 新增术语时 |
| [`README.md`](README.md) | 项目门面 | 功能/结构有显著变化时 |

### 文档风格

- 中文撰写（与项目用户群体一致）
- 如果某个指代另一份文件的说明，使用**相对链接**（如 `[docs/操作指令集.md](docs/操作指令集.md)`）
- 代码块标注语言（`python`、`powershell`、`bash` 等）

---

## 许可与合规

- **软件**：默认 AGPL-3.0，可申请**商业许可**（见 [`LICENSE`](LICENSE)）
- **游戏数据**：单独许可（[`DATA_LICENSE`](DATA_LICENSE)），**商用不可用本仓库数据**
- 发布时须同时附带 `LICENSE`、`DATA_LICENSE` 和 `NOTICES.md`
- 新增依赖前检查其许可证：禁止 GPL-3.0-only / SSPL / 无许可证依赖
- 详情见 [`docs/数据来源与许可.md`](docs/数据来源与许可.md) 和 [`docs/合规自查清单.md`](docs/合规自查清单.md)

---

## 常见问题

**Q：我不会 Python，能参与贡献吗？**

可以！你可以帮助完善文档、报告 Bug、提供游戏数据、参与讨论。Web 前端的 TypeScript 也欢迎贡献。

**Q：我想适配一款新游戏，从哪开始？**

推荐使用 `python scripts/main_generator.py` 交互式生成器，或阅读 [`docs/框架适配新游戏指南.md`](docs/框架适配新游戏指南.md)。

**Q：每次提交都要跑全量测试吗？**

PR 阶段 CI 会运行全量测试，本地开发时你只需要运行与你改动相关的测试即可。

**Q：如何提交大改动？**

建议先开 Issue 说明改动方案，获得反馈后再开始编码，避免做了大量工作后发现方向不对。

---

再次感谢你的贡献！🎉
