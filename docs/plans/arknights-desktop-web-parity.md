# 明日方舟桌面端追赶 Web — 实施计划

> 创建：2026-06-16  
> 状态：**已收尾**（功能对齐完成；人工验收待 2026-06-17）

## 背景

- **Web**：`web/frontend/src/pages/ArknightsComputePage.tsx` — 完整干员筛选、属性展示、技能解析、敌人/加成参数、乘区明细。
- **桌面默认入口**：`games/arknights/main.py` → **`ArknightsDamageApp`**（与 Web 计算能力对齐）。
- **声明式实验线**：`ArknightsApp` + `CALC_ARKNIGHTS_GUI=sheet` 可选启动。

**结论**：计算内核两边共用 `compute_snapshot_with_dag` + `operator_catalog` + `skill_parser`；桌面 GUI 已与 Web 参数语义对齐。

## 目标

桌面（含 launcher 嵌入）体验 **≥ Web 当前能力**，保留 PySide6 本地计算（无 HTTP）。

## 阶段（全部完成）

### Phase 1 — 恢复完整桌面入口 ✅

| 项 | 说明 |
|----|------|
| 入口 | `main.py` + launcher 使用 `ArknightsDamageApp` |
| 嵌入 | `embedded=True` + `show_embedded()` |

### Phase 2 — 与 Web 细节对齐 ✅

| 项 | Web | 桌面 |
|----|-----|------|
| 干员搜索 | Autocomplete 子串 | `operator_combo.py` + QCompleter |
| 技能等级 | Lv / 专精 Chip | 滑块 + Lv1-7 / 专1-3 |
| 信赖/潜能 | API 带入 | loader + ComputeSheet + 乘区表 |
| i18n | react-i18n | 跳过（桌面中文） |

### Phase 3 — ComputeSheet 双轨 ✅

- `arknights_compute_sheet.py` 共享模块
- `ArknightsApp` 持久 sheet + `evaluated` 信号
- `CALC_ARKNIGHTS_GUI=sheet` 可选入口

### Phase 4 — 功能对齐收尾 ✅

| 项 | 说明 |
|----|------|
| ATK%/伤害% 单位 | 改为 DAG **百分点制**（与 Web `handleCompute` 一致）；`merge_atk_percent_bonus()` |
| DamageApp 右栏 | `layout_for_damage_app()`：额外加成 + 敌人 + 信赖/潜能，全走 ComputeSheet |
| 总伤害倍率 | 技能参数区展示 `倍率 × 连发`（同 Web） |
| 真伤输出键 | 修复 `真伤伤害`（非 `真实伤害`） |
| trust/pot 覆盖 | `compute_snapshot_with_dag` + loader 支持 override |

## 非目标（本计划不做）

- 终末地式全量搜索 / 固定配装
- 删除 `ArknightsApp.py` / `ArknightsDamageApp.py` 双轨
- Web 级 i18n、布局像素级复刻
- 异常/元素伤害真实计算（两边均为占位表）

## 验证清单

### 自动化（已通过）

- [x] `pytest games/arknights/tests/test_damage_app_embedded.py`
- [x] `pytest games/arknights/tests/test_arknights_compute_sheet.py`
- [x] `pytest games/arknights/tests/test_web_parity_params.py`
- [x] `pytest games/arknights/tests/test_operator_combo.py`

### 人工（待 2026-06-17）

- [ ] `python games/arknights/main.py` — 完整 UI
- [ ] launcher → 明日方舟 — 嵌入无闪窗、启动器保持可见
- [ ] 干员列表 ≥418（标准库） — **部分自动化**：`pytest -m real_data -k min_parsed` 断言 ≥ `MIN_PARSED_COUNT`（100）；完整 418 仍依赖 parsed 或标准库体量
- [ ] 选干员 → 技能倍率/连发自动填充 → 开始计算 → 四卡片 + 乘区表
- [ ] `pytest games/arknights/tests/` 全量（`test_growth_compact` 预存 import 问题除外）
- [ ] 重新打包 `python scripts/main_build.py --target launcher`

## 涉及文件

| 文件 | Phase |
|------|-------|
| `games/arknights/gui/ArknightsDamageApp.py` | 1–4 |
| `games/arknights/gui/arknights_compute_sheet.py` | 3–4 |
| `games/arknights/gui/ArknightsApp.py` | 3 |
| `games/arknights/gui/operator_combo.py` | 2 |
| `games/arknights/calc/dag_adapter/adapter.py` | 3–4 |
| `games/arknights/calc/dag_adapter/loader.py` | 3–4 |
| `games/arknights/main.py` | 1, 3 |
| `framework/.../launcher/runtime.py` | 1 |
| `docs/会话接续手册.md` | §4.186 |
