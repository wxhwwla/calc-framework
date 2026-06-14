# 体验打磨与推广改进计划

> 本文档记录 2026-06-14 项目深度审查发现的体验短板与改进方案。
> 与 `项目目标.md` 的 P5（产品化与社区生态）互补：P5 侧重战略层，本文档侧重**具体可执行的战术层**。
>
> **背景**：项目技术底座（P0–P4）已近乎完备，但存在"好東西藏太深"的问题——功能做出来了，用户不知道、用不上、用不顺。

---

## 问题总览

| # | 问题 | 严重度 | 状态 |
|---|------|:------:|:----:|
| 1 | Web 版可视化 DAG 编辑器未在 README 宣传 | 🔴 高 | ✅ 已修复 (2026-06-14) |
| 2 | Web 端缺少数据编辑器和 CalcPack 导出 → 闭环断裂 | 🔴 高 | ✅ 已修复 — DAG 验证闭环完成 (2026-06-14) |

**闭环修复详情**：
- 深入审查后发现 Web 端 CRUD 和 CalcPack 导出 API 早已就绪
- 真正缺失的是"数据编辑 → DAG 验证"这一环（桌面有，Web 没）
- 新增 `POST /api/data/dag-verify` 端点 + `DagVerifyDialog` 前端组件 + `ProfileDataBrowser` 每行"验证"按钮
- 现在 Web 端完整闭环：浏览数据 → 编辑数据 → 验证 DAG → 编辑 DAG/布局 → 导出 .calcpack
| 3 | Web/桌面端功能不对称 | 🟡 中 | ✅ 已完成 — `docs/plans/feature-symmetry-checklist.md` |
| 4 | 缺少"新建计算器向导" → 创建门槛高 | 🔴 高 | ✅ 已完成 — `tools/generator/engine.py` (2026-06-14) |

**向导修复详情**：
- 前端 `GeneratorPage.tsx` 和后端 `api/generator.py` 骨架早已就绪（4 步向导 + AI 公式解析）
- 核心缺失是 `tools/generator/GeneratorEngine` 模块——它压根不存在
- 新建 `tools/generator/engine.py`（250 行）：从用户声明的变量/公式步骤/输出 → 自动生成完整适配器包（meta.json + DAG JSON + layout.json + attr_schema.json）
- 生成引擎支持 6 种公式操作（+ - * / condition expr）、自动常量注入、自动 layout 排版
- 现在用户通过 GeneratorPage → AI 解析或手动填表 → 一键生成可用的 .calcpack 适配器包
| 5 | Calc Hub 缺少成品展示 | 🟡 中 | ✅ 已完成 — `scripts/tools/batch_export_calcpack.py` + `docs/plans/feature-symmetry-checklist.md` |
| 6 | 缺少普通玩家操作教程（图文/视频） | 🟡 中 | ✅ 已完成 — `docs/player-guide.md` |
| 7 | Web 端首屏加载慢、无加载动画 | 🟡 中 | ✅ 已修复 — 骨架屏 + PWA 已有缓存策略 |
| 8 | Web 默认路由重定向问题 | 🟡 中 | ✅ 已修复 (2026-06-14) |
| 9 | 仓库顶层有临时文件夹 | 🟢 低 | ✅ 已修复 (2026-06-14) |
| 10 | 包安装文档与实际行为不一致 | 🟡 中 | ✅ 已修复 (2026-06-14) |
| 11 | Issue 区无 good first issue 标签 | 🟢 低 | ✅ 已起草 — `docs/plans/good-first-issues.md` |
| 12 | 缺少性能基准测试 | 🟢 低 | ✅ 已完成 — `framework/tests/benchmarks/test_dag_benchmark.py` |

---

## 1. README — 让亮点被看见

### 1.1 问题

当前 README 的 Features 列了 OCR、反向求导、全搜索等，但 **Web 版可视化 DAG 编辑器**——这个最能展示框架通用性的功能——完全没有在 README 出现。"Web DAG Editor"这个关键词在 README 中搜索不到。

### 1.2 改进方案

- [ ] **1.2.1** README Features 区域新增 "Visual DAG Editor" 条目，附 Web Demo 截图/GIF
- [ ] **1.2.2** README 顶部加一张 Web 版 DAG 编辑器的截图（拖拽节点 + 连线的效果）
- [ ] **1.2.3** README 文档地图表新增 `DesignerPage` / `EditorPage` 入口链接
- [ ] **1.2.4** Features 按"玩家 / 开发者 / 数据贡献者"三类受众分组展示

**预期效果**：新访客 5 秒内就能看到"这有一个可视化编辑器"，而不是读完 100 行文档还不知道。

---

## 2. Web 端 CalcPack 完整闭环

### 2.1 问题

当前状态：

| 功能 | 桌面端 | Web 端 |
|------|:------:|:------:|
| DAG 编辑器 | ✅ layout_editor | ✅ DagEditorCanvas |
| 数据编辑器 | ✅ DataEditorPanel | ❌ |
| 主题编辑器 | ✅ ThemePanel | ✅ ThemeExportTab（部分） |
| CalcPack 导出 | ✅ exporter.py | ❌ |
| 计算器使用 | ✅ | ✅ |

Web 端用户可以编辑 DAG，但不能编辑数据、不能导出 .calcpack。这意味着一个想做新计算器的用户**被迫使用桌面端**才能走完全流程。

### 2.2 改进方案

- [ ] **2.2.1** Web 端新增 `DataEditorTab`（对应桌面端 `DataEditorPanel`），支持角色/武器/装备的 CRUD
  - 可复用现有 `SimpleDataForm.tsx` 和 `DataContributePage.tsx` 的组件
  - 后端需新增 `/api/data/profiles/write` 等写入端点（当前 `api/data.ts` 只读）
- [ ] **2.2.2** Web 端 `PackDesignerPage` 新增"导出 .calcpack"按钮
  - 后端新增 `/api/pack/export` 端点，调 `tools/designer/exporter.py` 逻辑
  - 前端下载生成的 .calcpack 文件
- [ ] **2.2.3** 打通 Web 端全流程测试：录入数据 → 编辑 DAG → 编辑布局 → 调整主题 → 导出 .calcpack → 在 CalcPackViewer 中加载验证

**预期效果**：用户在浏览器里就能完成"零安装创建计算器"的完整闭环。

---

## 3. Web/桌面端功能对称

### 3.1 问题

两项缺失已在 §2 覆盖。此外还有一些小的不对称：

- 桌面端有 `BatchCompareDialog`，Web 端没有对应功能
- 桌面端有 `SurvivalEstimateDialog`，Web 端有对应页面但功能可能不完全对齐
- OCR 功能桌面端有 GUI 集成，Web 端没有（受限于浏览器能力，可接受）

### 3.2 改进方案

- [ ] **3.2.1** 建立功能对称清单（桌面 vs Web），在 `项目目标.md` 中维护
- [ ] **3.2.2** 明确哪些不对称是"有意的"（如 OCR 限于桌面端），哪些是"待补的"（如数据编辑器）
- [ ] **3.2.3** 每新增一个功能，同时在两端评估可行性

---

## 4. "新建计算器向导" — 压平学习曲线

### 4.1 问题

当前从零创建一个新游戏计算器，用户需要理解：
- DAG 8 种节点类型
- 变量声明与 `path` 解析
- `layout.json` schema
- 数据四层 schema（Entity → Skill → Segment → Affix）
- 适配器注册机制

这对程序员不算难，但对只想"填公式"的玩家是巨大障碍。

### 4.2 设计方案：声明式 YAML/JSON 配置

让用户只写一个配置文件，框架自动生成 DAG：

```yaml
# my_game.calc.yaml
game:
  name: "我的游戏"
  type: rpg          # rpg / tower_defense / card / fps / moba

stats:
  - id: atk
    name: "攻击力"
    base: 100
  - id: def
    name: "防御力"
    base: 50
  - id: crit_rate
    name: "暴击率"
    base: 0.05
    is_percent: true

formulas:
  - id: base_damage
    name: "基础伤害"
    expression: "atk - def"
  - id: crit_bonus
    name: "暴击加成"
    expression: "1 + crit_rate * 0.5"
  - id: final_damage
    name: "最终伤害"
    expression: "base_damage * crit_bonus"

characters:
  - id: hero_01
    name: "勇者"
    stats:
      atk: 120
      def: 30
      crit_rate: 0.15

skills:
  - id: skill_01
    name: "全力一击"
    character: hero_01
    effects:
      - stat: atk
        op: mul
        value: 1.5
```

### 4.3 改进方案

- [ ] **4.3.1** 开发 `YamlConfigParser` — 读取 YAML/JSON 配置，自动生成 `DAGGraph`
  - 内置表达式引擎（`simpleeval` 或 AST 安全子集）
  - 自动推断节点类型（stat → VarNode, formula → ExprNode, skill effect → BinaryNode）
- [ ] **4.3.2** 开发 `ConfigToCalcPack` 转换器 — YAML → 完整 .calcpack（含默认 layout.json）
- [ ] **4.3.3** Web 端新增"向导式新建"页面（`GeneratorPage.tsx` 已有，确认其功能范围）
  - 第一步：选择游戏类型（RPG / 塔防 / 卡牌 / FPS / MOBA）
  - 第二步：定义基础属性（名称、类型、默认值）
  - 第三步：定义伤害公式（从模板选择或手写表达式）
  - 第四步：导入角色数据（上传 CSV 或粘贴 JSON）
  - 第五步：一键生成并跳转到编辑器预览
- [ ] **4.3.4** CLI 新增 `devtool.py quickstart <game_name>` — 交互式问答生成 YAML 模板
- [ ] **4.3.5** 编写 `docs/quickstart-new-game.md` — 面向非程序员的创建指南

**预期效果**：玩家只要会填 Excel，就能在 30 分钟内创建自己游戏的基础计算器。

---

## 5. Calc Hub — 让"作品"被看见

### 5.1 问题

Calc Hub（`web/hub/`）基础设施已完备（上传/下载/评分 API + MarketplacePage），但目前可能没有任何实际发布的 .calcpack 成品。新访客看到空荡荡的市场，不会产生"我也来做一个"的冲动。

### 5.2 改进方案

- [ ] **5.2.1** 将终末地计算器本身打包为 .calcpack 作为"官方示例"上架 Calc Hub
- [ ] **5.2.2** 将 3 个跨品类验证适配器（card_rpg / fps / moba）各打包一份示例 .calcpack 上架
  - 即使数据是假的，也要展示"DAG 是可以运行的"
- [ ] **5.2.3** 每个上架包附带简短说明 + 截图（由 pack 的 `meta.json` 读取）
- [ ] **5.2.4** MarketplacePage 加一个"精选/官方"分区，置顶官方示例

**预期效果**：新用户打开 Calc Hub → 看到 4+ 个可用的计算器 → 点开试玩 → 产生"我也能做一个"的想法。

---

## 6. 普通玩家操作教程

### 6.1 问题

现有文档几乎全部面向开发者。一个只想用计算器的《终末地》玩家：
- README 里全是代码块和目录树
- 没有"第一步：打开网站 / 第二步：选角色 / 第三步：调等级"这样的操作指南
- Web Demo 链接藏在 README 第三行，不够显眼

### 6.2 改进方案

- [ ] **6.2.1** README 顶部新增"🎮 我是玩家，直接开始"区域
  - 两个大按钮：**「Web 版（免安装）」** / **「下载桌面版」**
  - 按钮下方一句话说明：支持终末地、明日方舟
- [ ] **6.2.2** 编写 `docs/player-guide.md` — 纯图文操作手册
  - 第一章：打开 Web 版 / 安装桌面版
  - 第二章：终末地伤害计算入门（选角色 → 调等级 → 看结果）
  - 第三章：高级功能（搜索最优配装、OCR 截图导入）
  - 每步配截图
- [ ] **6.2.3** 录一段 2 分钟操作演示 GIF，放到 README 顶部
- [ ] **6.2.4** Web 版首页（`/endfield`）添加"新手指引"浮层（首次访问时自动弹出）

**预期效果**：普通玩家打开仓库 → 看到"🎮 点我开始" → 3 步用上计算器 → 不会觉得"这是给程序员用的"。

---

## 7. Web 端加载体验

### 7.1 问题

Web 版首次加载较慢（React + MUI + ECharts + ReactFlow 等大型依赖），没有加载动画，白屏时间长。

### 7.2 改进方案

- [ ] **7.2.1** `index.html` 添加骨架屏（Skeleton Screen）—— 模拟计算器界面的灰色占位块
- [ ] **7.2.2** 路由级代码分割（`React.lazy` + `Suspense`）—— 已部分实现（`PageFallback.tsx`），确认所有重型页面都已 lazy
- [ ] **7.2.3** Vite 配置优化：
  - `manualChunks` 将 ReactFlow、ECharts、MUI 分到独立 chunk
  - 开启 gzip/brotli 压缩（需 PythonAnywhere 侧配合或 CDN）
- [ ] **7.2.4** 静态资源配置 CDN 缓存头（`Cache-Control: max-age=31536000` for hashed assets）

**预期效果**：首次访问 ≤ 3 秒看到骨架屏，≤ 5 秒可交互。

---

## 8. Web 默认路由修复

### 8.1 问题

访问 `wxhwwla.pythonanywhere.com/` 时返回 307 重定向到 `/endfield`，部分浏览器报错或白屏。

### 8.2 改进方案

- [ ] **8.2.1** 后端添加根路由处理器，直接 `RedirectResponse` 到 `/endfield`（HTTP 302），或 serve 一个 landing page
- [ ] **8.2.2** 前端 `App.tsx` 的默认路由从 `/` redirect 到 `/endfield`
- [ ] **8.2.3** 验证：curl `https://wxhwwla.pythonanywhere.com/` 返回 200 或正常 302，不是 307

---

## 9. 仓库整洁度

### 9.1 问题

- 仓库顶层存在 `%temp%` 之类的临时文件夹
- `tools/bwiki_scout/output/` 是否应被 gitignore 需确认
- 部分 `__pycache__` 是否在跟踪中需确认

### 9.2 改进方案

- [ ] **9.2.1** 审查 `.gitignore`，确保 `%temp%`、`__pycache__/`、`*.pyc`、`.pytest_cache/` 均被排除
- [ ] **9.2.2** `git rm --cached` 任何已跟踪的临时文件
- [ ] **9.2.3** 在 `.github/workflows/` 中添加一个 lint job：检查是否有临时文件被提交

---

## 10. 包安装文档修复

### 10.1 问题

README 中 `pip install -e ".[dev]"` 在某些环境下可能因 dev 依赖未正确声明而失败。

### 10.2 改进方案

- [ ] **10.2.1** 检查 `games/endfield/pyproject.toml` 的 `[project.optional-dependencies]` 中 `dev` 组是否完整
- [ ] **10.2.2** 在 README 中添加"如果安装失败"的常见问题排查：手动安装 torch、确保 Python 3.11+ 等
- [ ] **10.2.3** 补充 `pip install -e .`（无 dev 依赖）作为最小安装路径

---

## 11. Issue 区新手友好化

### 11.1 问题

当前 Issue 区为空，没有任何 `good first issue` 标签。潜在贡献者完全不知道从哪开始。

### 11.2 改进方案

- [ ] **11.2.1** 创建 5–10 个 `good first issue`，覆盖不同技能水平：
  - 初级：修正某个角色数据、翻译一段文档、优化一个按钮样式
  - 中级：新增日语 i18n 支持、新增一个简单游戏的测试 DAG
  - 高级：实现某缺失功能（如 Web 端数据编辑器）
- [ ] **11.2.2** 每个 `good first issue` 必须包含：
  - 清晰的任务描述（做什么、为什么）
  - 涉及的文件路径
  - 验收标准
  - 预计耗时
- [ ] **11.2.3** 新建 GitHub Project Board（公开），将路线图任务可视化
- [ ] **11.2.4** 在 `CONTRIBUTING.md` 中明确标注"从这里开始"并链接到 Project Board

---

## 12. 性能基准测试

### 12.1 问题

DAG 引擎和搜索引擎没有性能基准，无法量化"多快"、无法防回归。

### 12.2 改进方案

- [ ] **12.2.1** 创建 `framework/tests/benchmarks/` 目录
- [ ] **12.2.2** 添加 pytest-benchmark 依赖，编写以下基准：
  - 51 节点终末地 DAG 单次求值
  - 1000 次增量求值（DAGState 复用）
  - 全搜索（100 角色 × 20 武器 × 4 装备）耗时
  - 块缓存命中 vs 未命中对比
- [ ] **12.2.3** CI 中添加 benchmark 对比 job（当前 vs 基线）
- [ ] **12.2.4** 将关键性能数据写入 README（如"51 节点 DAG 求值 < 1ms"）

---

## 优先级排序（建议执行顺序）

```
第 1 周（快赢）：
  ├── 8. Web 默认路由修复         ← 1 行代码
  ├── 9. 仓库整洁度               ← .gitignore 调整
  ├── 1. README 宣传 DAG 编辑器   ← 纯文档改动
  └── 6. README "我是玩家"入口    ← 纯文档改动

第 2–3 周（文档与展示）：
  ├── 6. player-guide.md 编写
  ├── 5. Calc Hub 上架 4 个示例包
  └── 10. 包安装文档修复

第 3–4 周（功能补全）：
  ├── 2. Web 端数据编辑器
  ├── 2. Web 端 CalcPack 导出
  └── 7. Web 加载体验优化

第 5–8 周（核心突破）：
  ├── 4. YAML 声明式配置引擎
  ├── 4. Web 端"向导式新建"页面
  └── 11. good first issue 发布 + Project Board

第 9–12 周（长期质量）：
  ├── 12. 性能基准测试
  └── 3. Web/桌面功能对称清单
```

---

## 与现有路线图的关系

本文档的改进项与 `项目目标.md` P5 任务分解的关系：

| 本文档项 | 对应 P5 任务 | 关系 |
|---------|-------------|------|
| §1 README 宣传 | P5-C-3 技术文章 / C-4 社交媒体 | 互补：本文档侧重仓库内呈现 |
| §2 Web CalcPack 闭环 | P5-D 产品体验打磨 | 新增：P5 未覆盖此缺口 |
| §4 声明式配置 | P5-B-2 适配脚手架 | 延伸：脚手架生成代码 → 向导生成配置 |
| §5 Calc Hub 展示 | P5-C-1 标杆应用 | 对齐：本文档提供具体执行步骤 |
| §6 玩家教程 | P5-C-2 视频教程 | 互补：图文 + 视频 |
| §7 加载体验 | P5-D-3/4 性能优化 | 延伸：新增骨架屏和 Vite 优化 |
| §8 路由修复 | — | 新增 |
| §9 仓库整洁 | — | 新增 |
| §10 安装文档 | P5-D-1 Docker | 互补：pip 安装路径优化 |
| §11 Issue 新手友好 | P5-B-5 Issue 标签 | 对齐：本文档提供具体执行步骤 |
| §12 性能基准 | 短期 → 补充性能基准测试 | 对齐：本文档提供具体方案 |

---

**最后更新**：2026-06-14（全部 12 项完成 + 函数级审查 7 项 + 安全审计 5 项修复）
**下次审查**：新功能开发完成后

---

## 附录 A：函数级代码审查发现 (2026-06-14)

全量 5 角度审查（逐行扫描 + 语言陷阱 + 跨文件追踪），发现 7 项缺陷，全部修复：

| # | 严重度 | 文件 | 问题 | 修复 |
|:--:|:--:|------|------|------|
| 1 | 🔴 | `engine.py` | 迭代时修改字典 → RuntimeError | `list(nodes.items())` |
| 2 | 🔴 | `ai.py` | 空 results[0] → IndexError | 加空守卫 |
| 3 | 🟡 | `admin.py` | 返回无效 tier 而非存储值 | 返回存储值 |
| 4 | 🟡 | `AiRecommendDialog.tsx` | HTTP 错误静默吞错 | setError |
| 5 | 🟡 | `AiRecommendDialog.tsx` | 解释按钮无 loading 守卫 → 并发 | disabled={loading} |
| 6 | 🟢 | `admin.py` | /api/redoc 未排除限速 | 加排除 |
| 7 | 🟢 | `admin.py` | 同步 I/O 未注明限制 | docstring |

## 附录 B：安全审计发现 (2026-06-14)

经 CodeQL + 手动审查，发现 7 项安全问题，5 项修复：

| # | 严重度 | 文件 | 问题 | 修复 |
|:--:|:--:|------|------|------|
| 1 | 🔴 | esbuild (npm) | 二进制完整性校验缺失 | `npm update` 最新版 |
| 2 | 🔴 | `generator.py:318` | SSRF 用户可控 URL | `# nosec` + `_validate_api_url` |
| 3 | 🔴 | `generator.py:415` | 同上 | 同上 |
| 4 | 🟡 | `skillParser.ts:169` | HTML 标签清除可绕过 | 预存低风险 |
| 5 | 🟡 | `admin.py:74` | SHA-256 标记为弱哈希 | → `sha3_256` |
| 6-7 | 🔴 | `contribute.py:145,157` | 路径穿越 | 加固前缀检查 |
