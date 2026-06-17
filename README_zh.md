[![GitHub stars](https://img.shields.io/github/stars/wxhwwla/calc-framework?style=social)](https://github.com/wxhwwla/calc-framework)
[![AtomGit stars](https://atomgit.com/wxhwwla/calc-framework/star/badge.svg)](https://atomgit.com/wxhwwla/calc-framework)
[![Game CI](https://github.com/wxhwwla/calc-framework/actions/workflows/ci.yml/badge.svg)](https://github.com/wxhwwla/calc-framework/actions/workflows/ci.yml)
[![Framework CI](https://github.com/wxhwwla/calc-framework/actions/workflows/framework-ci.yml/badge.svg)](https://github.com/wxhwwla/calc-framework/actions/workflows/framework-ci.yml)
[![Web CI](https://github.com/wxhwwla/calc-framework/actions/workflows/web-ci.yml/badge.svg)](https://github.com/wxhwwla/calc-framework/actions/workflows/web-ci.yml)
[![Security Audit](https://github.com/wxhwwla/calc-framework/actions/workflows/security-audit.yml/badge.svg)](https://github.com/wxhwwla/calc-framework/actions/workflows/security-audit.yml)

# Calc Framework — 通用游戏计算框架

> 通用游戏计算框架 · 目前支持《明日方舟：终末地》与《明日方舟》
>
> [:us: English](README.md)

---

## 🚀 快速开始

<table>
<tr>
<td align="center" width="50%">

### 🎮 我是玩家

**直接用计算器——无需安装。**

[**打开 Web 版 →**](https://wxhwwla.pythonanywhere.com)

*或* [下载桌面版](https://github.com/wxhwwla/calc-framework/releases)

> 📖 [玩家手册](docs/player-guide.md)

</td>
<td align="center" width="50%">

### 🔧 我是开发者

**为我的游戏构建计算器，或参与贡献。**

```bash
git clone https://github.com/wxhwwla/calc-framework
cd calc-framework
python scripts/main_launcher.py
```

> 🏗 [快速上手 ↓](#快速上手) · [创建计算器](docs/制造游戏计算器完整流程.md) · [贡献路径](docs/contributor-pathways.md)

</td>
</tr>
</table>

---

## 文档导航

| 文档 | 适合谁 |
|------|--------|
| **本页** | 首次访问、GitHub 首页 |
| [`ARCHITECTURE_zh.md`](ARCHITECTURE_zh.md) ([EN](ARCHITECTURE.md)) | 系统架构概览 |
| [`CONTRIBUTING_zh.md`](CONTRIBUTING_zh.md) ([EN](CONTRIBUTING.md)) | 如何贡献 |
| [`docs/contributor-pathways.md`](docs/contributor-pathways.md) | 玩家 → 贡献者成长路径 |
| [`CONTEXT_zh.md`](CONTEXT_zh.md) ([EN](CONTEXT.md)) | 领域术语表 |
| [`docs/项目目标.md`](docs/项目目标.md) | 项目愿景与路线图 |
| [`docs/操作指令集.md`](docs/操作指令集.md) | 操作命令速查 |
| [`docs/数据来源与许可.md`](docs/数据来源与许可.md) | 许可与数据来源 |
| [`games/endfield/README.md`](games/endfield/README.md) | 终末地包详细说明 |

---

## 目录一览

```
[仓库根]/
├── framework/                    # [框架] calc-framework 通用 pip 包
│   ├── src/calc_framework/       #   DAG 引擎、逆推引擎、数据、UI、搜索、插件
│   └── adapters/                 #   游戏适配器 (endfield/arknights/card_rpg/fps/moba)
├── web/                          # [Web] React + FastAPI 全栈 Web 应用
│   ├── backend/                  #   FastAPI 后端 (/api/*)
│   │   └── api/                  #     路由 + internal/ entity/ search_lib/ 等（会话手册 §4.188）
│   ├── frontend/                 #   React 前端 (TypeScript + MUI + Vite)
│   └── hub/                      #   Calc Hub — 静态市场页面
├── games/                        # [游戏] 游戏适配包
│   ├── endfield/                 #   终末地伤害计算器 (calc + gui + data + tests)
│   └── arknights/                #   明日方舟计算器 (DAG + GUI + tests)
├── docs/                         # 项目文档
├── tools/                        # [工具] 开发工具 (BWIKI侦察、数据管线、OCR、设计器)
├── scripts/                      # [入口] 启动器、打包、开发者工具箱
├── release_bundle/               # 发布布局配置
├── installer/                    # NSIS 安装包
├── .github/                      # CI 工作流、Issue 模板
├── LICENSE · DATA_LICENSE · CONTEXT_zh.md · CONTRIBUTING_zh.md
└── NOTICES.md                    # 第三方声明
```

---

## 快速开始

### 推荐：启动器

```powershell
# 自动发现已安装的游戏适配包
python scripts/main_launcher.py
```

### 直接启动

```powershell
# 终末地计算器
cd games/endfield
pip install -e ".[dev]"
python -m games.endfield.main
```

```powershell
# 开发者工具箱
python scripts/main_dev_toolkit.py
```

### Web 版

```powershell
# 后端
cd web/backend && pip install -r requirements.txt && uvicorn main:app --reload --port 8002

# 前端（新终端）
cd web/frontend && npm install && npm run dev
```

---

## 功能概览

### 终末地伤害计算器

- 角色/武器/装备选择，双页签 GUI（计算页 + 高级页）
- 15 乘区伤害公式，DAG 引擎驱动（框架 ComputeSheet）
- 全量搜索枚举，Top-N 追踪，并行执行，SQLite 断点续跑
- 多技能段级加权总伤，固定配装 0–4 件
- 装备词条解析、优先级排序、无益剪枝
- OCR 截图识装 → 一键填入计算器（TorchVision + EasyOCR）
- 公式反推：数据 → 4 参数成长公式
- 配装预设 JSON 导入/导出、批量对比、伤害仪表盘（matplotlib）
- 生存估算、敌方参数面板、场外 Buff 微调

### 明日方舟计算器

- 按星级/职业/分支筛选干员，技能文本解析
- 物理/法术/真实伤害计算，DAG 引擎驱动
- BWIKI 数据爬取：420+ 干员全量数据
- 28 属性 + 5 自定义函数 + 51 节点 DAG

### 通用框架

- **可视化 DAG 编辑器**：拖拽式节点编辑器（Web: ReactFlow, 桌面: PySide6），无需写代码即可构建伤害公式
- **DAG 引擎**：8 种节点类型（常量/变量/一元/二元/条件/表达式/用户输入/子图调用）、拓扑排序、AST 沙箱、子图展开、块级缓存、增量求值
- **逆推引擎**：`data_to_params()` / `params_to_curve()` — 任意游戏双向公式拟合
- **搜索引擎**：Top-N 枚举、并行执行、取消令牌、SQLite 持久化
- **ComputeSheet**：声明式 UI — 消费 `layout.json` + DAG 变量 → 自动渲染控件
- **插件系统**：注册表模式 + 3 内置插件（暴击/闪避/距离衰减）+ `.calcplugin` 格式
- **AI 配装**：自然语言配装推荐 + 多轮对话 + 语义搜索 + AI 公式解析
- **跨品类验证**：card_rpg (9 节点)、moba (7)、fps (8)、genshin_like (45 节点) 适配器均通过
- **主题管理**：暗色/亮色/高对比度，动态 QSS 生成；Web 端暗/亮切换
- **SaaS API**：API Key 管理 + 速率限制 + 用量统计

### Web 版

| Web 页面 | 桌面对应 | 路由 |
|----------|---------|------|
| 伤害计算器 | `main.py`（桌面）/ FastAPI + React（Web） | `/` |
| 数据设计器 | 开发者工具箱 | `/designer` |
| 配置包设计器 | 开发者工具箱 | `/pack-designer` |
| Calc Hub 市场 | — | `/marketplace` |

Web 版与桌面版共享 `layout.json` / `attr_schema.json` / DAG 文件 / 数据 JSON。一套声明，两端渲染。

---

## 框架 API 速览

```python
from calc_framework.inverse.engine import InverseEngine

engine = InverseEngine()

# 反向：数据 → 4 参数（任何等级数、任何游戏）
params = engine.data_to_params([100, 105, 110, 115, 120])
# GrowthParams(base=100, growth=5, divisor=1, offset=0)

# 正向：4 参数 + 等级 → 曲线
curve = engine.params_to_curve(params, num_levels=90)
# [100.0, 105.0, ..., 545.0]
```

```python
from calc_framework.inverse.schema import GameInverseAdapter, InverseSchema

# 新游戏接入：声明式配置，不写分派代码
class MyGame(GameInverseAdapter):
    @property
    def schemas(self):
        return [InverseSchema(length=60), InverseSchema(length=10)]
    def default_formula(self): return "floor_linear"

adapter = MyGame()
result = adapter.fit(data)  # 自动按长度匹配
```

---

## 测试

```powershell
# 框架测试
cd framework && pytest tests/ -q     # 1160 passed

# 终末地测试
cd games/endfield && pytest tests/ -q  # 1585 passed
```

[![CI](https://github.com/wxhwwla/calc-framework/actions/workflows/ci.yml/badge.svg)](https://github.com/wxhwwla/calc-framework/actions/workflows/ci.yml)

---

## 社区与交流

| 渠道 | 用途 |
|------|------|
| [GitHub Issues](https://github.com/wxhwwla/calc-framework/issues) | Bug 报告 / 功能建议（推荐） |
| [GitHub Discussions](https://github.com/wxhwwla/calc-framework/discussions) | 技术讨论 / 问题求助 |
| QQ 群：`1040157567` | 中文社区（建设中） |
| Discord | 邀请链接建设中 |

---

## 许可证与数据来源

| 内容 | 许可 |
|------|------|
| **软件** | [AGPL-3.0](LICENSE)（默认）或书面商业许可 |
| **游戏数据** | [DATA_LICENSE](DATA_LICENSE) — 商用不可用本仓库数据 |
| **完整说明** | [`docs/数据来源与许可.md`](docs/数据来源与许可.md) |
| **第三方声明** | [`NOTICES.md`](NOTICES.md) |

使用或分发即视为接受相应许可。
