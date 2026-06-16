# 全量搜索加速 + JSON 曲线压缩 — 实施计划

**状态**：阶段 A/B 代码与测试已完成（2026-06-15）；**2026-06-16 更新**：PyInstaller exe 禁用 ProcessPool；Rust job 批量 + 单 worker 内联 batch 为默认（97w ~1min）。JSON 全库 `--apply`、全量搜索耗时验证由人类本地执行  
**目标**：缩短装备全量遍历耗时；缩小 `characters.json` / `weapons.json` 体积并保持数值一致。

---

## 背景

| 问题 | 根因 |
|------|------|
| 100 万次遍历 ~15 分钟，改线程数无效 | `ThreadPoolExecutor` + CPython GIL，CPU 密集 Python 几乎串行 |
| 框架续跑路径物化全表 | `EndfieldSearchEngine.generate_candidates()` → `list(tasks)` |
| JSON 体积大 | 录入/BWIKI 已用 4 参数公式烘焙，磁盘仍存 90 档数组 |

---

## 阶段 A：搜索性能（P0）

### A1 恢复流式 + 有界并行主路径

| 项 | 内容 |
|----|------|
| **改什么** | `run_search_session` 续跑 → `execute_search_with_resume`；内存 TopN → `run_enumerated_optimizer_parallel` |
| **不再走** | 框架 `SearchSession` → `generate_candidates()` 物化 |
| **保留** | `SearchEngine` 抽象供测试/其他游戏；终末地 GUI/MVP 走端侧流式 |

### A2 多进程并行（绕 GIL）

| 项 | 内容 |
|----|------|
| **改什么** | `run_bounded_parallel(..., parallel_backend="process")` 默认 process |
| **实现** | `calc/search/evaluate/process_worker.py`：进程 initializer + 模块级 `evaluate_optimizer_task` |
| **约束** | `max_workers==1` 或调试时可选 `thread`；Windows 使用 spawn |
| **预估** | 耗时模型 `(组合数 × 单组合秒数) / workers` 在 process 下再次成立 |

### A3 验收

- `games/endfield/tests/calculation/search/run/test_search_session.py` 全过
- `test_search_persistence.py` 续跑一致
- `framework/tests/search/test_parallel.py` 不受影响（框架仍 thread）
- 新增：`test_bounded_parallel.py` — process/thread 结果一致；耗时对比小数据集 skip（spawn 开销）

---

## 阶段 B：JSON 曲线压缩（P1）

### B1 数据契约（双读）

磁盘 JSON 支持两种形态（**向后兼容**）：

```json
{
  "名称": "示例",
  "最大等级": 90,
  "成长参数": {
    "力量": {"base": 21, "growth": 22, "divisor": 98, "offset": 0},
    "战技倍率": [
      {"base": 1.0, "growth": 10, "divisor": 98, "offset": 0, "special": [2.3, 2.5, 2.7]}
    ]
  }
}
```

- **有 `成长参数`**：加载时烘焙为内存数组（`力量`、`战技倍率` 等），运行时逻辑不变。
- **无 `成长参数`**：仍读现有数组（旧文件、人工编辑）。
- **公式**：统一 `FloorFormulaFitter` / `calculate_growth_curve` / `calculate_skill_curve`（与 designe­r/BWIKI 一致）。

### B2 加载接缝

| 文件 | 职责 |
|------|------|
| `data_loading/curve_materialize.py` | `materialize_character_entity` / `materialize_weapon_entity` |
| `data_loading/loader.py` | `get_*()` 返回前对列表内实体 materialize |

### B3 迁移工具（人类执行）

```bash
python tools/compact_game_json.py --dry-run   # 报告拟合误差
python tools/compact_game_json.py --apply     # 写回 JSON（需 git 备份）
```

- 对每个可拟合属性：`InverseEngine.fit` → 写入 `成长参数` → 删除冗余数组
- `max_error` 超阈值（默认 0.05）的实体**保留数组**并打 warning
- **不删除** `等级`/`潜能`/`信赖` 元数据（除非后续单独 ADR）

### B4 验收

- `tools/tests/test_compact_game_json.py` roundtrip
- 随机抽 3 角色：90 级各属性与迁移前 diff ≤ 0.1（人类 `--apply` 后）
- `characters.json` 体积下降可度量（目标 ≥50% 角色块）

---

## 阶段 C：文档同步（完成时）

- `docs/会话接续手册.md` §4
- `docs/算法与架构.md` 搜索执行层图
- `docs/操作指令集.md` 迁移命令
- `CONTEXT.md` 术语：`成长参数`
- `docs/README.md` 索引本计划

---

## 默认决策（无需阻塞）

| 决策 | 选择 | 理由 |
|------|------|------|
| 搜索默认后端（开发） | `process` | 绕 GIL |
| **搜索默认后端（exe）** | **thread + 单 worker 内联 batch** | ProcessPool 闪退；多 worker batch 实测更慢 |
| **桌面「自动」线程** | **1 worker** | Rust job 批量已摊销 FFI |
| JSON 迁移时机 | 提供工具，**本批不自动 commit 全量 JSON** | 避免误 fit；用户本地 `--apply` |
| Web 端 | 加载层烘焙后 API 仍返回数组 | 前端零改动 |
| GPU | 不在本计划 | 依赖 B 完成后仍非搜索瓶颈 |

---

## 待用户确认（可选）

1. **JSON 迁移**：是否希望 Agent 在本仓库直接 `--apply` 并提交缩小后的 `characters.json`？（默认：仅工具 + 双读，人类决定何时 apply）
2. ~~**搜索默认线程**~~：已决 — exe/GUI「自动」= **1 worker**；实验多 worker 设 `CALC_SEARCH_BATCH_POOL=1`（见 `docs/错误集.md`）
