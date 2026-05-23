# MVP 搜索验收说明（实验功能）

> 适用范围：`Slice 1 ~ Slice 10` 对应的 MVP/二期基础能力。  
> 当前实现偏向“可验证主链路”，UI 入口为实验按钮，后续可再做产品化打磨。

## 1. 功能总览

已落地能力：

- 15 乘区单段伤害引擎（默认不暴击，支持期望/必暴）
- 外部效果统一结构（含未知标签兜底记录）
- 装备四格装配与三件套触发（胸甲/护手/配件A/配件B）
- 单技能最优搜索（TopN、候选筛选、基础剪枝）
- 并行执行与 ETA 回调、可取消
- SQLite 续跑与去重恢复
- 结果导出：Top JSON/CSV + 全量 NDJSON
- 多技能加权总伤搜索（默认“当前选中技能=1，其它=0”，全 0 拦截）

## 2. 代码入口

- 单段伤害：`calculation/damage_engine.py`
- 装备模型：`calculation/equipment_system.py`
- 单技能搜索：`calculation/loadout_optimizer.py`
- 并行执行：`calculation/search_runner.py`
- 续跑存储：`calculation/search_persistence.py`
- 导出：`calculation/result_export.py`
- MVP 串联：`calculation/mvp_pipeline.py`
- 多技能：`calculation/multi_skill_optimizer.py`
- GUI 实验入口：`gui_design/gui.py`（按钮：`实验：MVP搜索并导出`）

## 3. GUI 使用步骤（实验入口）

1. 启动 GUI：`python main.py`
2. 选择角色与武器（角色武器类型会自动过滤候选）
3. 点击 `实验：MVP搜索并导出`
4. 选择导出目录
5. 程序优先读取本地标准装备数据 `endfield_damage_calculator/character_weapon_equipment/equipment_data/equipments.json`
6. 若本地标准装备为空，会回退读取 `tools/bwiki_scout/output/parsed/equipment.json` 草案
6. 完成后会弹窗提示：
   - `search_runs.db`（续跑数据库）
   - `mvp_exports/top_results.json`
   - `mvp_exports/top_results.csv`
   - `mvp_exports/all_results.ndjson`

> 建议先执行一次标准化同步，再使用 GUI 搜索：
>
> ```powershell
> python tools/bwiki_scout/parse_draft.py
> python tools/bwiki_scout/sync_equipments.py --apply
> ```

## 4. 命令行验收

在 `[包]` 目录执行：

```powershell
python -m pytest -q
```

当前基线：`194 passed, 9 subtests passed`。

可单测重点模块：

```powershell
python -m pytest tests/test_damage_engine.py -q
python -m pytest tests/test_equipment_system.py -q
python -m pytest tests/test_loadout_optimizer.py tests/test_search_runner.py -q
python -m pytest tests/test_search_persistence.py tests/test_result_export.py -q
python -m pytest tests/test_mvp_pipeline.py tests/test_multi_skill_optimizer.py -q
```

## 5. SQLite 查看建议（仅提供链接，不内置）

- [DB Browser for SQLite](https://sqlitebrowser.org/dl/)
- [SQLite GUI by Anton Zhiyanov](https://antonz.org/sqlite-gui/)

## 6. 已知限制

- GUI 入口目前为“实验模式”，以可用验证优先，尚未做完整交互打磨。
- 装备数据依赖 BWIKI 草案字段质量；若标签不全，需要继续扩充爬虫与映射。
- 并行执行当前使用线程池，后续可按性能评估升级到进程池/混合执行。

