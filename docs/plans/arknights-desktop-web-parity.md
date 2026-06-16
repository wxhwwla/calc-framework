# 明日方舟桌面端追赶 Web — 实施计划

> 创建：2026-06-16  
> 状态：**Phase 3 已完成**（ComputeSheet 双向绑定；默认入口仍为 DamageApp）

## 背景

- **Web**：`web/frontend/src/pages/ArknightsComputePage.tsx` — 完整干员筛选、属性展示、技能解析、敌人/加成参数、乘区明细。
- **桌面当前入口**：`games/arknights/main.py` → **`ArknightsDamageApp`**（与 Web 对齐）；`ArknightsApp` 为 ComputeSheet 声明式线，环境变量 `CALC_ARKNIGHTS_GUI=sheet` 可切换。

**结论**：差距主要是 **入口选错了精简壳**，不是 DAG/数据层落后。计算内核两边共用 `compute_snapshot_with_dag` + `operator_catalog`。

## 目标

桌面（含 launcher 嵌入）体验 **≥ Web 当前能力**，保留 PySide6 本地计算（无 HTTP）。

## 阶段

### Phase 1 — 恢复完整桌面入口

| 项 | 说明 | 状态 |
|----|------|:----:|
| 入口 | `main.py` + `launch_adapter_in_process` 改用 `ArknightsDamageApp` | ✅ |
| 嵌入 | `ArknightsDamageApp(embedded=True)` + `show_embedded()` | ✅ |
| 验收 | 干员筛选/详情/技能解析/连发/条件倍率/敌人参数/结果卡片+明细表 | 待人工 |

### Phase 2 — 与 Web 细节对齐

| 项 | Web 参考 | 桌面 | 状态 |
|----|----------|------|:----:|
| 干员搜索 | Autocomplete 子串 | `operator_combo.py` + QCompleter `MatchContains` | ✅ |
| 技能等级 | Lv / 专精 + 快捷 Chip | 滑块 + Lv1-7 / 专1-3 按钮行 | ✅ |
| 信赖/潜能 | API 自动带入 DAG | loader 写入；详情 + 乘区表展示潜能攻击 | ✅ |
| i18n | react-i18n | 桌面中文（与终末地一致） | 跳过 |

### Phase 3 — ComputeSheet 双轨 ✅

| 项 | 说明 | 状态 |
|----|------|:----:|
| 共享模块 | `games/arknights/gui/arknights_compute_sheet.py` | ✅ |
| 持久 sheet | `ArknightsApp` 单次创建 + `evaluated.connect` + 重接「计算」按钮 | ✅ |
| skill_index | 左栏技能选择与 `get_parsed_skill_info` 对齐 | ✅ |
| 可选入口 | `CALC_ARKNIGHTS_GUI=sheet` → `main.py` 启动 `ArknightsApp` | ✅ |
| DamageApp 迁移 | 右栏敌人/信赖/潜能改用 ComputeSheet（技能参数仍手动） | ✅ |

- `ArknightsApp` + `layout.json` 保留为声明式实验线；**默认仍为 DamageApp**。

## 非目标（本计划不做）

- 终末地式全量搜索 / 固定配装（明日方舟暂无）
- 删除 `ArknightsDamageApp.py`（保留作参考与回退）

## 验证清单

- [x] `pytest games/arknights/tests/test_damage_app_embedded.py`
- [x] `pytest games/arknights/tests/test_arknights_compute_sheet.py`
- [ ] `python games/arknights/main.py` — 完整 UI
- [ ] launcher → 明日方舟 — 嵌入无闪窗、启动器保持可见
- [ ] 干员列表 ≥418（标准库）
- [ ] 选干员 → 技能倍率/连发自动填充 → 开始计算 → 四卡片 + 乘区表
- [ ] `pytest games/arknights/tests/` 通过（`test_growth_compact` 除外，预存 import 问题）

## 涉及文件

| 文件 | Phase |
|------|-------|
| `games/arknights/main.py` | 1 |
| `games/arknights/gui/ArknightsDamageApp.py` | 1–2 |
| `games/arknights/gui/operator_combo.py` | 2 |
| `games/arknights/operator_catalog.py` | 2（`DEFAULT_PARSED_DIR` 别名） |
| `framework/.../launcher/runtime.py` | 1 |
| `games/arknights/gui/ArknightsApp.py` | 3 |
| `games/arknights/gui/arknights_compute_sheet.py` | 3 |
| `games/arknights/main.py` | 3（`CALC_ARKNIGHTS_GUI`） |
| `docs/会话接续手册.md` | §4.186 |
