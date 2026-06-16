# 明日方舟桌面端追赶 Web — 实施计划

> 创建：2026-06-16  
> 状态：**进行中**（Phase 1）

## 背景

- **Web**：`web/frontend/src/pages/ArknightsComputePage.tsx` — 完整干员筛选、属性展示、技能解析、敌人/加成参数、乘区明细。
- **桌面当前入口**：`games/arknights/gui/ArknightsApp.py` — 2026-06-02 框架对齐 MVP；ComputeSheet 未双向绑定，计算参数未接满。
- **桌面完整版（仓库内）**：`games/arknights/gui/ArknightsDamageApp.py` — 与 Web 功能对齐，但未接入 launcher / `main.py`。

**结论**：差距主要是 **入口选错了精简壳**，不是 DAG/数据层落后。计算内核两边共用 `compute_snapshot_with_dag` + `operator_catalog`。

## 目标

桌面（含 launcher 嵌入）体验 **≥ Web 当前能力**，保留 PySide6 本地计算（无 HTTP）。

## 阶段

### Phase 1 — 恢复完整桌面入口（当前）

| 项 | 说明 | 状态 |
|----|------|:----:|
| 入口 | `main.py` + `launch_adapter_in_process` 改用 `ArknightsDamageApp` | ✅ |
| 嵌入 | `ArknightsDamageApp(embedded=True)` + `show_embedded()` | ✅ |
| 验收 | 干员筛选/详情/技能解析/连发/条件倍率/敌人参数/结果卡片+明细表 | 待人工 |

### Phase 2 — 与 Web 细节对齐（后续）

| 项 | Web 参考 | 桌面待办 |
|----|----------|----------|
| 干员搜索 | Autocomplete | 已有可编辑 ComboBox，可加强模糊匹配 |
| 技能等级显示 | Lv / 专精 | 已有 |
| 信赖/潜能 | API 自动带入 | 桌面从 JSON 读取，核对 loader 是否写入 DAG |
| i18n | react-i18n | 桌面暂中文（与终末地一致） |

### Phase 3 — ComputeSheet 双轨（可选，低优先级）

- `ArknightsApp` + `layout.json` 保留为声明式实验线。
- 待 Phase 1/2 稳定后，再决定是否把 DamageApp 右栏迁回 ComputeSheet（需双向绑定 + evaluated 信号）。

## 非目标（本计划不做）

- 终末地式全量搜索 / 固定配装（明日方舟暂无）
- 删除 `ArknightsDamageApp.py`（保留作参考与回退）

## 验证清单

- [x] `pytest games/arknights/tests/test_damage_app_embedded.py`
- [ ] `python games/arknights/main.py` — 完整 UI
- [ ] launcher → 明日方舟 — 嵌入无闪窗、启动器保持可见
- [ ] 干员列表 ≥418（标准库）
- [ ] 选干员 → 技能倍率/连发自动填充 → 开始计算 → 四卡片 + 乘区表
- [ ] `pytest games/arknights/tests/` 通过（`test_growth_compact` 除外，预存 import 问题）

## 涉及文件

| 文件 | Phase 1 |
|------|---------|
| `games/arknights/main.py` | 改入口 |
| `games/arknights/gui/ArknightsDamageApp.py` | embedded 模式 |
| `framework/.../launcher/runtime.py` | 嵌入类名 |
| `games/arknights/gui/ArknightsApp.py` | 文档注明暂缓 |
| `docs/会话接续手册.md` | §4.186 |
