# Good First Issues — 新手贡献任务

> 本文档包含可直接复制到 GitHub Issues 的新手友好任务。
> 每个任务标注难度、预计耗时、涉及文件和验收标准。
>
> 使用方法：将下方任务逐一创建为 GitHub Issue，添加 `good first issue` 标签。

---

## 初级任务（无需编程经验）

### GFI-01: 修正终末地角色中文译名

**难度**：⭐ | **预计耗时**：15 分钟 | **涉及文件**：`games/endfield/data/characters.json`

部分角色的中文名可能跟游戏内实际显示不一致。检查 `characters.json` 中的 `name` 字段，对照游戏内的实际名称进行修正。

**验收标准**：至少修正 3 个角色名称，附带游戏内截图作为依据。

---

### GFI-02: 翻译 README 中的缺失段落到英文

**难度**：⭐ | **预计耗时**：30 分钟 | **涉及文件**：`README.md`

README.md 中部分中文内容在英文版中缺失或为机器翻译。逐段检查英文翻译质量，修正不通顺之处。

**验收标准**：修正至少 5 处不通顺的英文表达。

---

### GFI-03: 补充 i18n 翻译 — 桌面端 GUI 控件

**难度**：⭐ | **预计耗时**：1 小时 | **涉及文件**：`framework/src/calc_framework/ui/i18n_data/en.json`

桌面端 GUI 的英文翻译目前基础框架已搭好（282 键），但部分控件的实际文案尚未翻译。逐一检查 `zh-CN.json` 中有但 `en.json` 中缺失或标记为 TODO 的键，补充英文翻译。

**验收标准**：至少补充 20 个翻译键。

---

### GFI-04: 添加一个新的武器数据

**难度**：⭐ | **预计耗时**：20 分钟 | **涉及文件**：`games/endfield/data/weapons.json`

按照现有武器 JSON 格式，添加一把新武器的完整数据（基础攻击力曲线、特殊技能等）。

**验收标准**：JSON 格式正确，通过 `pytest games/endfield/tests/data/test_game_data_contract.py` 的数据契约检查。

---

## 中级任务（需要基础编程）

### GFI-05: 优化 Web 端按钮 hover 效果

**难度**：⭐⭐ | **预计耗时**：1–2 小时 | **涉及文件**：`web/frontend/src/components/calculator/*.tsx`

当前部分计算器按钮的 hover 样式使用了默认 MUI 主题，可改进为更贴合项目风格。为 3–5 个按钮组件添加自定义 hover 过渡动画或微交互效果。

**验收标准**：hover 效果流畅，在 Chrome/Edge 上无闪烁，符合 MUI 设计规范。

---

### GFI-06: 新增日语 i18n 基础支持

**难度**：⭐⭐ | **预计耗时**：2–3 小时 | **涉及文件**：`web/frontend/src/i18n/locales/`、`framework/src/calc_framework/ui/i18n_data/`

参考现有的 `zh-CN` 和 `en` 翻译文件，创建日语（ja）翻译骨架：
1. Web 端：创建 `web/frontend/src/i18n/locales/ja.ts`，翻译首屏可见的核心文案（导航栏、按钮、标题，约 30–50 个键）
2. 在语言切换按钮中增加日语选项

**验收标准**：能在 Web 端切换到日语，核心界面正确显示日文。

---

### GFI-07: 为终末地搜索模块添加单元测试

**难度**：⭐⭐ | **预计耗时**：2 小时 | **涉及文件**：`games/endfield/tests/calculation/search/`

当前搜索模块的测试覆盖率尚有余地。选择 `search/plan/` 或 `search/run/` 中未覆盖的分支逻辑，编写 3–5 个新测试用例。

**验收标准**：新增测试通过 `pytest` 且不破坏现有测试。测试覆盖边界条件（空输入、极值、异常路径）。

---

### GFI-08: 编写一个简单的计算器示例（非终末地游戏）

**难度**：⭐⭐ | **预计耗时**：3–4 小时 | **涉及文件**：`framework/adapters/` 中新建目录

使用框架的适配器机制，为一个简单的游戏（如下棋游戏、卡牌对战、或你喜欢的任何游戏）创建一个基础 DAG 计算器：
1. 定义 3–5 个属性
2. 定义 2–3 个伤害公式（使用 DAG JSON）
3. 跑通 `AdapterManager` 的加载和基础求值

参考现有的 `card_rpg`、`fps`、`moba` 适配器。

**验收标准**：适配器能被 `AdapterManager` 自动发现，输入测试数据后输出正确的计算结果。

---

## 高级任务（需要一定的框架理解）

### GFI-09: Web 端数据编辑器 — 基础 CRUD

**难度**：⭐⭐⭐ | **预计耗时**：1–2 天 | **涉及文件**：`web/frontend/src/components/designer/`、`web/backend/api/data.py`

当前 `DesignerPage` 只能浏览数据，不能编辑。新增一个 `DataEditorTab` 组件，支持：
1. 选择数据源（角色/武器/装备）
2. 表格形式展示数据（可编辑单元格）
3. 保存修改到后端（需后端新增 `PUT /api/data/profiles/{type}/{id}` 端点）

**验收标准**：用户可以在 Web 端新增、修改、删除角色数据，刷新后数据保持。

---

### GFI-10: 性能基准 — DAG 引擎 benchmark

**难度**：⭐⭐⭐ | **预计耗时**：1–2 天 | **涉及文件**：`framework/tests/benchmarks/`（新建）

使用 `pytest-benchmark` 为 DAG 引擎编写性能基准测试：
1. 51 节点终末地 DAG 单次求值耗时
2. 1000 次增量求值（DAGState 复用）总耗时
3. 全搜索模拟（100 角色 × 20 武器 × 4 装备）耗时
4. 块缓存命中率对比

**验收标准**：CI 中可运行 benchmark，输出与基线的对比报告。

---

## 如何使用这些 Issue

1. 将每个任务复制为独立的 GitHub Issue
2. 添加标签 `good first issue`（初级/中级）或 `help wanted`（高级）
3. 在 Issue 正文开头标注：**"👋 欢迎贡献！请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)"**
4. 如果有贡献者在 Issue 下留言表示认领，及时回复确认

---

**建议首批发 5 个**（覆盖不同难度）：
- GFI-01（翻译修正）
- GFI-04（新武器数据）
- GFI-06（日语 i18n）
- GFI-07（补充测试）
- GFI-09（Web 数据编辑器）
