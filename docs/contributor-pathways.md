# 用户 → 贡献者成长路径

> 从"我只是想算个伤害"到"我给这个项目写了核心功能"——每条路都有清晰的下一步。

---

## 三条成长路径

```
                         ┌─────────────────┐
                         │   普通玩家       │
                         │ "我就想算伤害"    │
                         └────────┬────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              ▼                   ▼                   ▼
     ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
     │ 数据贡献者      │  │ 文档/翻译贡献者  │  │ 代码贡献者      │
     │ 改数据/加角色    │  │ 修文档/做翻译    │  │ 写功能/修Bug    │
     └────────┬───────┘  └────────┬───────┘  └────────┬───────┘
              │                   │                   │
              ▼                   ▼                   ▼
     ┌────────────────────────────────────────────────────────┐
     │                  核心维护者                              │
     │      审查 PR、管理 Issue、决定项目方向                    │
     └────────────────────────────────────────────────────────┘
```

---

## 路径 1：数据贡献者（最易入门，无需编程）

### 你能做什么

- 发现角色/武器/装备数据有误 → 修正
- 游戏更新了新角色 → 添加数据
- 游戏平衡性调整 → 更新数值

### 第一步：使用计算器，发现问题

1. 打开 [Web 版计算器](https://wxhwwla.pythonanywhere.com)
2. 正常使用，对比游戏内数据
3. 发现不一致 → 记录下来（角色名、字段名、游戏内实际值、计算器显示值）

### 第二步：提交数据修正

**方式 A：Web 在线提交（推荐，零门槛）**

1. 访问 Web 版 → 左侧导航 →「数据贡献」(`/contribute`)
2. 填写表单：选择实体类型 → 填写字段 → 提交
3. 提交后数据会自动生成标准 JSON，维护者审核后合入

**方式 B：GitHub Issue 反馈**

1. 在 [Issues](https://github.com/wxhwwla/calc-framework/issues) 新建 Issue
2. 标题示例：`[数据] 终末地 - 佩丽卡基础攻击力有误`
3. 内容包含：角色名、字段名、当前错误值、正确值、游戏内截图

**方式 C：直接修改 JSON 文件（需 GitHub 账号）**

1. Fork 本仓库
2. 编辑 `games/endfield/data/characters.json`（或 weapons.json / equipments.json）
3. 提交 PR，标题加 `[data]` 前缀

### 进阶：批量添加数据

当你熟悉数据格式后，可以：
- 使用 `tools/bwiki_scout/` 爬取 BWIKI 数据
- 使用 `tools/data_pipeline/` 清洗为标准格式
- 了解 [数据格式说明](制造游戏计算器完整流程.md)

---

## 路径 2：文档/翻译贡献者

### 你能做什么

- 修正文档中的错误或过时内容
- 补充缺失的翻译（英文/日文）
- 编写教程、使用技巧
- 改进 README 的可读性

### 第一步：找到需要改进的地方

- 阅读 [玩家手册](player-guide.md) — 发现说明不清的地方
- 切换语言看英文翻译 — 发现不通顺或缺失的翻译
- 浏览 [Issues](https://github.com/wxhwwla/calc-framework/issues) 中带 `documentation` 标签的

### 第二步：提交改进

**文档修改**

1. Fork 仓库
2. 编辑对应的 `.md` 文件
3. 提交 PR，标题加 `[docs]` 前缀

**翻译补充**

1. Web 端翻译：编辑 `web/frontend/src/i18n/locales/{locale}.ts`
2. 桌面端翻译：编辑 `framework/src/calc_framework/ui/i18n_data/{locale}.json`
3. 对照中文原文逐条翻译，保持 JSON 结构不变
4. 查看 [good first issue](https://github.com/wxhwwla/calc-framework/issues?q=label%3A%22good+first+issue%22) 中的翻译任务

---

## 路径 3：代码贡献者

### 前置准备

1. **环境搭建**
   ```bash
   git clone git@github.com:wxhwwla/calc-framework.git
   cd calc-framework
   cd framework && pip install -e ".[dev]" && cd ..
   cd games/endfield && pip install -e ".[dev]" && cd ../..
   ```

2. **了解架构**：阅读 [ARCHITECTURE.md](../ARCHITECTURE.md) 和 [CONTEXT.md](../CONTEXT.md)

3. **跑通测试**：`cd games/endfield && pytest tests/ -q`

### 入门任务（5 分钟 → 2 小时）

| 难度 | 任务示例 | 涉及技能 | 从哪里找 |
|:----:|---------|---------|---------|
| ⭐ | 修正角色/武器数据 | 无 | `games/endfield/data/*.json` |
| ⭐ | 补充英文翻译 | 英语 | `web/frontend/src/i18n/locales/en.ts` |
| ⭐⭐ | 优化按钮样式/交互 | React/MUI | `web/frontend/src/components/` |
| ⭐⭐ | 为搜索模块补测试 | pytest | `games/endfield/tests/calculation/search/` |
| ⭐⭐⭐ | Web 端新增小功能 | React+FastAPI | Issues 中 `help wanted` 标签 |
| ⭐⭐⭐ | 为新游戏写适配器 | Python+DAG | 参考 `card_rpg`/`fps`/`moba` 适配器 |

> 💡 查看 [good first issues](https://github.com/wxhwwla/calc-framework/issues?q=label%3A%22good+first+issue%22) 获取更多带详细说明的入门任务。也可参考 [`docs/plans/good-first-issues.md`](plans/good-first-issues.md) 中的 10 个预写任务。

### 中级任务（半天 → 2 天）

- **新增日语支持**：参考现有 `zh-CN`/`en` 翻译文件创建 `ja` 翻译
- **修复已知 Bug**：Issues 中带 `bug` 标签的
- **为 card_rpg 适配器添加更多节点**：扩展示例适配器展示框架能力
- **编写 E2E 测试**：为 Web 端关键流程添加 Playwright 测试

### 高级任务（1 周+）

- **为新游戏创建完整计算器**：使用 Generator 生成骨架 → 补充数据 → 调通 DAG → 上架 Calc Hub
- **优化搜索引擎性能**：并行搜索策略改进、SQLite 索引优化
- **添加新的 DAG 节点类型**：扩展引擎能力（如循环节点、概率节点）

---

## 开发规范速查

在提交 PR 前，请确保：

1. **代码风格**：项目使用 ruff（等价于 black + isort + flake8）
   ```bash
   ruff check . && ruff format .
   ```

2. **测试通过**：
   ```bash
   cd games/endfield && pytest tests/ -q
   ```

3. **提交信息**：使用中文描述，格式为 `类型: 简短说明`
   - `fix: 修正佩丽卡基础攻击力`
   - `feat: Web 端新增批量对比组件`
   - `docs: 更新玩家手册第三章`

4. **分支命名**：`feature/xxx` 或 `fix/xxx`

---



## 从贡献者到维护者

持续贡献高质量 PR、积极参与 Issue 讨论、帮助其他贡献者 review 代码——当你累计合并 **5 个以上 PR** 后，作者会邀请你成为 **Committer**（拥有直接 push 权限）。

成为 Committer 后你可以：
- 直接审核和合并 PR
- 管理 Issue 标签和里程碑
- 参与项目方向讨论

---

> 📧 任何问题随时联系：wxhwwla@gmail.com
>
> 💬 社区讨论：[GitHub Issues](https://github.com/wxhwwla/calc-framework/issues)
>
> 📖 更多文档：[项目目标](项目目标.md) · [贡献指南](../CONTRIBUTING.md) · [架构说明](../ARCHITECTURE.md)
