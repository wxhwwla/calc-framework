# Phase 4 — 生态与文档实施计划

> 创建：2026-06-17  
> 来源：[`defect-audit-verification-2026-06-17.md`](defect-audit-verification-2026-06-17.md) §Phase 4  
> 前置：Phase 0–3 ✅ 已全部完成

---

## 背景

Phase 0–3 解决了安全、Web 可靠性、框架质量与 `api/` 目录约束。Phase 4 为**长期生态项**，不要求单次会话全部完成；按步骤交付、每步更新会话手册。

| 编号 | 主题 | 现状 |
|:----:|------|------|
| 16 | 明日方舟 Web/桌面伤害能力 | 桌面与 Web **计算对齐已完成**（见 [`arknights-desktop-web-parity.md`](arknights-desktop-web-parity.md)）；人工验收与打包待勾选 |
| 17 | ADR-0023 数据路径统一 | 终末地 / 明日方舟路径**不一致**（M13）；需先文档化再分步迁移 |
| 18 | 代码签名、Desktop i18n、自动更新 | 见 [`improvement-roadmap.md`](improvement-roadmap.md) |

---

## 步骤总览

| Step | 内容 | 风险 | 状态 |
|:----:|------|:----:|:----:|
| **4.1** | 数据路径规范文档（[`数据路径对照表.md`](../数据路径对照表.md)） | 低 | ✅ |
| **4.2** | 明日方舟人工验收清单 → 自动化探针（`@pytest.mark.real_data`） | 低 | ✅ |
| **4.3** | ADR-0023 数据路径迁移 — 路径常量 + `sync_adapter_snapshots.py` | 中 | ✅ |
| **4.4** | Desktop i18n 逐控件 — 计算页首批（shell + 总伤面板） | 中 | ✅ |
| **4.4b** | Desktop i18n — control_dock / 对话框等剩余 | 中 | ⏳ |
| **4.5** | 代码签名 + 自动更新生产验证 | 高（需证书/环境） | ⏳ |
| **4.6** | 明日方舟 Web 扩展（配装/搜索，**非** parity 计划范围） | 高 | 📋 待规划 |

---

## Step 4.1 — 数据路径规范文档 ✅

**交付**：[`docs/数据路径对照表.md`](../数据路径对照表.md)

**目的**：

- 明确「运行时主数据 / 适配器快照 / scout 产出 / 打包路径」四层关系
- 为 Step 4.3 迁移提供单一事实来源，避免 Agent 或协作者误改路径

**验收**：文档覆盖 endfield + arknights + Web 部署 + PyInstaller 四条链路；与 `operator_catalog.py`、`data_loading/loader.py` 常量一致。

---

## Step 4.2 — 明日方舟验收自动化 ⏳

**来源**：[`arknights-desktop-web-parity.md`](arknights-desktop-web-parity.md) §验证清单（人工）

**计划**：

1. 扩展 `games/arknights/tests/test_data_loading.py`：`TestDataIntegrity.test_standard_library_count`（标准库 ≥ `MIN_PARSED_COUNT`）
2. 可选：`test_damage_app_embedded.py` 冒烟（不启动 GUI 窗口）
3. 文档中将人工项标注「可由 CI / `pytest -m real_data` 替代」

**非目标**：launcher 嵌入闪窗、打包 exe 体积 — 仍须人工或 E2E。

---

## Step 4.3 — ADR-0023 数据路径迁移 ✅

**交付**（2026-06-17）：

- [`utils/game_data_paths.py`](../../utils/game_data_paths.py) — 层 A/B 路径单一常量源
- [`tools/sync_adapter_snapshots.py`](../../tools/sync_adapter_snapshots.py) — endfield / arknights 层 A→B 同步 CLI
- `from_arknights_scout` 输出修正为 `framework/adapters/arknights/data/operators_standard.json`
- `loader.py` / `operator_catalog.py` / `profiles.py` 引用 `game_data_paths`

**数据刷新顺序**（终末地 BWIKI 同步后）：

```powershell
python tools/bwiki_scout/sync_all.py --apply   # 写入 games/endfield/data/
python tools/sync_adapter_snapshots.py --game endfield --apply
```

**明日方舟**：

```powershell
python tools/arknights_scout/sync_operators.py
python tools/compact_arknights_operators.py --apply --write-standard
# 或
python tools/sync_adapter_snapshots.py --game arknights --apply
```

**后续（4.3+）**：评估 `games/arknights/data/` 是否作为层 A 目录（当前仍用 parsed）。

---

## Step 4.4 — Desktop i18n（计算页首批）✅

**交付**（2026-06-17）：

- `desktop.endfield.*` 16 键（zh-CN + en）
- `games/endfield/gui/endfield_shell.py` — 页签、确认按钮、状态文案
- `games/endfield/gui/presentation/total_damage_panel.py` — 总伤结算面板
- `framework/tests/ui/test_i18n_endfield.py`

**后续 4.4b**：`qt_control_dock`、搜索/增强对话框、OCR 等仍含硬编码中文。

---

## Step 4.4b — Desktop i18n 剩余控件 ⏳

见 [`improvement-roadmap.md`](improvement-roadmap.md) §2、`docs/plans/i18n-desktop.md`。

优先：`qt_control_dock.py`、`qt_dialogs.py`、designer 页签。

---

## Step 4.5 — 发布与签名 ⏳

- OV/EV 证书采购与 `scripts/main_build.py` 集成
- `utils/updater.py` 生产环境 HTTPS + 签名校验实测

---

## Step 4.6 — 明日方舟 Web 扩展（远期）📋

**非** [`arknights-desktop-web-parity.md`](arknights-desktop-web-parity.md) 范围（该文档明确不做终末地式全量搜索/固定配装）。

若产品需要，单独立项：Web 配装 schema、`/api/arknights/search` 等。

---

## 验证记录

| 项 | 命令 | 结果 | 日期 |
|----|------|:----:|:----:|
| Step 4.1 文档 | 人工对照源码 | ✅ | 2026-06-17 |
| Step 4.2 干员数量探针 | `pytest games/arknights/tests/test_data_loading.py -k min_parsed -m real_data` | ✅ | 2026-06-17 |
| Step 4.3 路径常量 + sync | `pytest tools/tests/test_sync_adapter_snapshots.py` | ✅ | 2026-06-17 |
| Step 4.4 计算页 i18n | `pytest framework/tests/ui/test_i18n_endfield.py` | ✅ | 2026-06-17 |

---

## 相关文档

- [`docs/会话接续手册.md`](../会话接续手册.md) §4.187–§4.189
- [`docs/数据来源与许可.md`](../数据来源与许可.md)
- [`CONTEXT.md`](../../CONTEXT.md)
