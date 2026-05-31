# ADR-0016：重命名 adapters/endfield/ → calc_engine/endfield/

## 状态

已批准

## 背景

`adapters/` 目录命名存在严重的语义误导：

- `adapters/endfield/` 包含 **82 个源文件**（伤害引擎、装备系统、配装优化器、乘区系统、搜索流水线、技能系统），是完整的游戏专属计算库。
- 与此同时，`framework/calc_engine/endfield/` 才是真正的框架级薄适配层（仅 `meta.json` + DAG JSON 配置）。
- 两个同名 `endfield` 目录职责截然不同，新开发者难以区分。

## 决策

将 `adapters/endfield/` 重命名为 `calc_engine/endfield/`，同步更新所有内部导入引用和文档。

## 影响范围

| 类型 | 数量 |
|------|------|
| Python 源文件（需更新导入） | 100 个 |
| Markdown 文档 | 10 个 |
| 目录移动 | 1 个（含 82 个 .py 子文件） |

## 实施步骤

### 1. 目录移动
```
adapters/endfield/             →  calc_engine/endfield/
adapters/endfield/calc/        →  calc_engine/endfield/calc/
adapters/endfield/data/        →  calc_engine/endfield/data/
adapters/endfield/data_loading/ → calc_engine/endfield/data_loading/
adapters/endfield/tests/       →  calc_engine/endfield/tests/
```

### 2. 批量导入替换
所有 `adapters.endfield` → `calc_engine.endfield`（保持包查找路径一致）

### 3. 文档更新
- `docs/项目目标.md`
- `docs/会话接续手册.md`
- `docs/数据来源与许可.md`
- `docs/代码结构规范.md`
- `docs/框架适配新游戏指南.md`
- `docs/quickstart.md`
- `framework/README.md`
- ADR-0004 / ADR-0010 / ADR-0013

### 4. CI/CD 路径更新
- `release_bundle/release_layout.py`

## 风险

| 风险 | 级别 | 缓解措施 |
|------|------|---------|
| 导入漏改导致 ImportError | 中 | 全局搜索 + pytest 全量运行验证 |
| git 历史断裂 | 低 | `git mv` 保留文件历史 |
| 外部工具脚本路径失效 | 低 | 更新 `tools/` 下的引用 |
| 第三方包依赖路径 | 低 | 当前无第三方包依赖该路径 |

## 测试验证
1. `pytest calc_engine/endfield/tests/` — 所有适配器测试通过
2. `pytest framework/tests/` — 所有框架测试通过
3. 启动 GUI 验证导入路径正确

## 替代方案

| 方案 | 优点 | 缺点 |
|------|------|------|
| A：不重命名，仅加 README | 零风险 | 命名误导持续存在 |
| **B：完整重命名（选定）** | **语义清晰，一劳永逸** | **侵入性高，但为一次性代价** |
| C：创建别名包（adapters → calc-engine） | 向后兼容 | 额外维护两个命名空间，增加疑惑 |
