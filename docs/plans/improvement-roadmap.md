# 项目改进路线图（2026-06-09）

> 本文档记录项目当前的不完善之处，按优先级分类，供后续开发参考。
>
> 基于 [`docs/项目目标.md`](../项目目标.md) 的长远愿景和 [`docs/会话接续手册.md`](../会话接续手册.md) 的当前状态综合分析。

---

## 目录

- [总览](#总览)
- [P3：发布与生态缺口](#p3发布与生态缺口)
- [P2：功能与覆盖缺口](#p2功能与覆盖缺口)
- [P1：细节打磨](#p1细节打磨)
- [架构与技术债务](#架构与技术债务)
- [验证记录](#验证记录)

---

## 总览

| 层 | 文档完成度 | 实际状态 | 差距 |
|----|:----------:|:--------:|:----:|
| 乘区层（计算引擎） | ~98% | ✅ 实测 DAG 引擎、搜索、inverse、测试、框架独立 pip 均正常工作 | 无显著差距 |
| 布局层（设计器） | ~98% | ✅ ComputeSheet、布局编辑器、Web 三 GUI 均正常工作 | 无显著差距 |
| 展示层（用户框架） | ~95% | ✅ CalcPackViewer、终末地方舟 GUI、Web 端均正常工作 | 无显著差距 |

**核心结论**：引擎、GUI、Web 三端功能完整可用，架构质量良好。当前主要缺口集中在：
1. **发布流程**（代码签名、自动更新生产验证）
2. **生态建设**（更多游戏 ETL 链路、i18n、测试覆盖）
3. **持续维护**（目录宽度监控、覆盖率保持）

---

## P3：发布与生态缺口

以下为远期（6 个月+）目标中尚未启动的项目。

### 1. 代码签名（D-5）

| 项目 | 说明 |
|------|------|
| **问题** | PyInstaller 打包的 exe 无数字签名，Windows SmartScreen 弹出"Windows protected your PC"警告 |
| **影响** | 新用户首次下载后需要点击"More info → Run anyway"，可能劝退非技术用户 |
| **方案** | 购买 OV/EV 代码签名证书（如 Sectigo、DigiCert），签名 .exe 和 .msi |
| **成本** | OV ~$200-300/年，EV ~$300-500/年 |
| **集成方式** | 在 `release.yml` 或 `main_build.py` 中 post-build 步骤调用 `signtool.exe` |
| **依赖** | 无代码改动，仅 CI/build 脚本变更 |
| **优先级建议** | 用户量增长后（~100+ 日活）可投入 |

### 2. 多语言支持 / i18n（D-6）

| 项目 | 说明 |
|------|------|
| **问题** | 所有 GUI（PySide6 + Web React）和文档仅中文，无 en/ja 等多语言支持 |
| **影响** | 项目面向全球开发者（GitHub 英文社区），中文仅限中文用户群 |
| **方案** | 桌面端：`QM` 文件（PySide6 官方 i18n）；Web 端：`react-i18next` 或 `react-intl` |
| **工作量** | 桌面端 ~2 周（提取 ~300 条字符串 + 翻译）；Web 端 ~2 周（~500 条 + 翻译）；文档 ~1 周 |
| **优先级建议** | 有英文贡献者 / 用户非中文需求时启动，不必提前投入 |

### 3. 自动更新生产验证

| 项目 | 说明 |
|------|------|
| **问题** | `auto_update.py` 已实现（§4.158）但未经过广泛用户测试，可能存在 edge case（如网络中断、磁盘空间不足、杀软拦截） |
| **方案** | 发布 Beta 版给核心用户群测试，收集反馈后修复 edge case |
| **优先级建议** | 下一个 Minor 版本发布前集中测试 |

### 4. PythonAnywhere 一键部署完善

| 项目 | 说明 |
|------|------|
| **问题** | `deploy_pythonanywhere.py` 已实现并验证通过，但缺少从零开始的完整自动化（注册账号 → Token 配置 → Web 应用创建 → 部署的全链路） |
| **方案** | 编写交互式脚本，引导用户完成首次部署 |
| **优先级建议** | 有外部 contributor 需要通过 PA 自托管时再做 |

---

## P2：功能与覆盖缺口

以下为中期（3-6 个月）目标中的未完成项。

### 1. 明日方舟数据管道（data_pipeline 接入） ✅ 已完成（2026-06-09）

| 项目 | 说明 |
|------|------|
| **问题** | 明日方舟爬虫（`tools/arknights_scout/`）已爬取 420 干员的 JSON 数据，但**未接入 `tools/data_pipeline/` 的 EntitySchema 标准格式** |
| **方案** | 编写 `tools/data_pipeline/transformers/from_arknights_scout.py`，将 arknights_scout 的 JSON 转换为 EntitySchema 格式 |
| **完成情况** | 420/422 干员成功转换，16 个空技能干员（机器人等边缘用例）正常跳过。输出 `games/arknights/data/operators_standard.json`。12 个单元测试全部通过 |

### 2. CI 覆盖率门槛偏低

| 项目 | 说明 |
|------|------|
| **问题** | `games/endfield/` 的 CI 覆盖率门槛为 `--fail-under=40`（当前实际 ~64%），`framework/` 全量 ~73% |
| **影响** | 覆盖率降低不影响 CI 通过，长期可能下滑 |
| **方案** | 逐步提升门槛：40 → 50 → 60，配合新增测试 |
| **优先级建议** | 每次 PR 至少新增 10 条覆盖率相关测试，3 轮后可提升到 60 |

### 3. Web 后端测试覆盖 ✅ 已完成（2026-06-09）

| 项目 | 说明 |
|------|------|
| **问题** | `web/backend/` 基本无后端自动化测试（仅 3 个测试文件，覆盖率 ~15%） |
| **方案** | 使用 `fastapi.testclient.TestClient` 对主要 API 端点写集成测试 |
| **完成情况** | 新建 `test_api_integration.py` 含 22 个测试用例，覆盖健康检查/适配器/数据/计算/布局/搜索/方舟/生成器/Hub/OCR/错误处理 11 个模块，全量 26 个测试通过 |

### 4. Web 端 E2E 测试覆盖 ✅ 已完成（2026-06-09）

| 项目 | 说明 |
|------|------|
| **问题** | 仅有 5 个基本 Cypress spec 文件（~30 测试），缺少交互操作和关键页面测试 |
| **方案** | 补充核心功能页面的 E2E 测试，提升覆盖深度和广度 |
| **完成情况** | 新增 6 个 spec 文件共 40+ 测试，覆盖：方舟计算页交互、生成器页面、导航/侧边栏切换、响应式布局、市场/适配器页、PWA manifest；旧 compute 测试增强（交互操作） |

### 5. 目录宽度监控

| 项目 | 说明 |
|------|------|
| **问题** | 部分目录超限或接近上限（`tools/` 31→18 ✅ 已修复，`web/backend/api/` 21，`scripts/` 17），ADR-0001 约束需持续监控 |
| **方案** | 在 CI 中定期运行 `check_layout.py`（当前已在 CI）；2026-06-13 完成 tools/ 拆分（quality/migration/publish 三个子目录，16 个文件移入） |
| **优先级建议** | 新增模块时同步检查；`web/backend/api/` 需通过 FastAPI APIRouter 拆分，风险较高暂缓 |

---

## P1：细节打磨

以下为短期（1-3 个月）内的改进点。

### 1. 多游戏适配器缺少完整 GUI 示例 ✅ 已完成（2026-06-09）

| 项目 | 说明 |
|------|------|
| **问题** | fps/moba/card_rpg 适配器已完成跨品类 DAG 验证，且有 layout.json 和示例 calcpack，但缺少**完整的 GUI 使用示例**和文档化的使用说明 |
| **方案** | 为每品类写一个简短的 README（`framework/adapters/{game}/README.md`），说明如何用 CalcPackViewer 加载和测试 |
| **完成情况** | 三个 README 文件已创建，包含公式说明、变量表、输出说明、代码调用和 CalcPackViewer 使用方式 |

### 2. 框架 pip 包 GUI 限制文档化 ✅ 已完成（2026-06-09）

| 项目 | 说明 |
|------|------|
| **问题** | `calc_framework` 已可通过 pip 独立安装，但 GUI 功能（viewer/launcher）因惰性导入 `utils/`、`tools/` 需完整项目环境，纯 pip 安装后部分功能不可用。此限制仅存在于代码注释中，未对外文档化 |
| **方案** | 在 `framework/README.md` 和 `framework/pyproject.toml` 中明确标注 GUI 功能依赖完整项目环境 |
| **完成情况** | framework/README.md 架构总览下新增注意警示框；pyproject.toml 描述中标注限制 |

### 3. 消除 formula.py 与框架的重复逻辑 ✅ 已完成（2026-06-13）

| 项目 | 说明 |
|------|------|
| **问题** | `games/endfield/calc/damage/formula.py` 的 `calculate_growth_curve`、`validate_attribute_formula` 与框架 `FloorFormulaFitter.compute()`/`validate()` 实现了完全相同的公式；`has_fractional_part`/`infer_decimal_mode` 与框架 `_detect_scale` 重复 |
| **方案** | 三步委托重构：① validate_attribute_formula → _FITTER.validate()；② calculate_growth_curve → _FITTER.compute()；③ infer_decimal_mode → _FITTER._detect_scale() |
| **完成情况** | 三步全部完成，formula.py 减少 ~40 行重复代码，正反向计算共享同一套框架实现。全量测试通过 |

---

## 架构与技术债务

| 项 | 状态 | 说明 |
|:--|:----:|------|
| 双引擎遗留 | ✅ 已消除 | §4.131–4.132 完成全部路径迁移 |
| OCR AGPL 许可 | ✅ 已消除 | §4.161 ultralytics YOLO → torchvision Faster R-CNN |
| 独立入口清理 | ✅ 已完成 | `scripts/` 仅 3 个有效入口（§4.140–4.148） |
| `_version.py` 统一 | ✅ 已完成 | 版本唯一源头（§4.144） |
| 上传脚本全流程 | ✅ 稳定 | 中文 pathspec / ruff-lint 误判 / CRLF F822 已修复（§4.151–4.155） |
| GUI 文件超限 | ⚠️ 持续监控 | `endfield_actions.py` 749 行（超 400 目标，低于 500 硬顶） |
| 目录宽度 | ⚠️ 持续监控 | `scripts/` 17 项接近 20 上限 |
| `games.endfield` 覆盖率 | 🟢 85% | CI 门槛 65%，远超要求 ✅ |
| `framework` 覆盖率 | 🟢 73% | 超过 70% 目标 ✅ |
| `web/backend` 覆盖率 | 🔴 ~15% | 基本无后端测试 |
| Web E2E 测试 | 🔴 少量 | 仅 2 个 spec 文件 |

---

## 验证记录

> 本节记录对项目各部分与文档一致性的实际验证结果。

| 验证项 | 结论 | 日期 | 验证人 |
|--------|:----:|:----:|:------:|
| Web 前端 tsc --noEmit 构建 | ✅ 0 errors | 2026-06-09 | Agent |
| framework pip 独立导入（DAGGraph + evaluate_graph） | ✅ 无报错 | 2026-06-09 | Agent |
| 入口文件一致性（scripts/ 仅 3 有效入口） | ✅ | 2026-06-09 | Agent |
| CI 配置覆盖率门槛 ci.yml fail-under=60 | ✅ 与文档一致 | 2026-06-09 | Agent |
| CI 工作流合规（8 个 workflow） | ✅ 已同步文档 | 2026-06-09 | Agent |
| framework 测试收集（1003 tests, 0 errors） | ✅ | 2026-06-09 | Agent |
| games/endfield 测试收集（1498 tests） | ✅ | 2026-06-09 | Agent |
| 项目目标完成度与实际一致 | ⚠️ 已更新 | 2026-06-09 | Agent |
| 多游戏适配器 README 创建（fps/moba/card_rpg） | ✅ 已完成 | 2026-06-09 | Agent |
| 框架 pip GUI 限制文档化（README + pyproject.toml） | ✅ 已完成 | 2026-06-09 | Agent |
| CI 覆盖率门槛抬升（ci.yml 60→65） | ✅ 已完成 | 2026-06-09 | Agent |
| Web 后端集成测试（22 测试用例，26 全量通过） | ✅ 已完成 | 2026-06-09 | Agent |

---

## 进度记录

| 日期 | 更新内容 | 更新人 |
|:----:|---------|:------:|
| 2026-06-09 | 初始创建：基于项目文档分析的完整改进路线图 | Agent |
| 2026-06-09 | P1 两项完成：多游戏适配器 README + 框架 pip GUI 限制文档化 | Agent |
| 2026-06-09 | P2 两项完成：CI 门槛 60→65 + Web 后端 22 个集成测试 | Agent |
| 2026-06-09 | P2 明日方舟 data_pipeline 接入完成 | Agent |
| 2026-06-13 | ADR-0024 逆推引擎完全抽象化：GrowthParams + GameInverseAdapter + data_to_params/params_to_curve 双向 API | Agent |
| 2026-06-13 | P0-1 消除 formula 重复：validate_attribute_formula → 框架 FloorFormulaFitter.validate() | Agent |
| 2026-06-13 | P0-2 消除 formula 重复：calculate_growth_curve → 框架 FloorFormulaFitter.compute() | Agent |
| 2026-06-13 | P0-3 消除 formula 重复：统一 has_fractional_part / infer_decimal_mode → 框架 _detect_scale | Agent |
| 2026-06-13 | P1 compute() 增强：level_overrides + 修复 is_decimal 缩放 bug；calculate_skill_curve/bonus_attribute 委托框架 | Agent |
| 2026-06-13 | P2 JsonDataLoader[T] 泛型提取 + loader.py 消除 ~80 行重复 | Agent |
| 2026-06-13 | ADR-0025 接口一致性巩固：异常层次/CalcWorker→utils/主题→ThemeManager/semver提取/游戏模板更新 | Agent |
| 2026-06-13 | 代码结构合规：tools/ 31→18项（拆quality/migration/publish），豁免表更新，ci门禁通过 | Agent |
| 2026-06-13 | i18n 阶段1完成（6文档中英分离）+ 阶段2基础设施（Web i18n ~130条，tsc零错误） | Agent |
| 2026-06-13 | 上传脚本修复：develop/main checkout -b 冲突bug + 错误集更新 | Agent |
| 2026-06-13 | develop→main 合并完成（d99fa165，118文件，9535行新增） | Agent |
