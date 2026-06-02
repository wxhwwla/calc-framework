# ADR-0023：标准化游戏包架构

## 状态

已采纳

## 上下文

项目现有两个游戏实现（终末地 / 明日方舟），它们的包结构严重不对齐：

| 维度 | `games/endfield/`（终末地） | `games/arknights/`（明日方舟） |
|------|-----------|-----------|
| 代码量 | ~320+ 文件 | ~15 文件 |
| 计算引擎 | 自有引擎 `calc/damage/` + DAG 双轨 | 仅 DAG（公式在 `functions.py`） |
| GUI | 模块化 `gui_design/`（60+ 文件） | 单片式 `gui/ArknightsDamageApp.py` |
| 数据加载 | `data_loading/` 全套 | 无 |
| 搜索/装备 | `calc/search/`, `calc/equipment/`, `calc/loadout/` | 无 |

这种不对齐带来三个问题：

1. **新游戏加入无模板** — 无法判断"添加一个新游戏需要哪些文件"
2. **双轨维护成本** — 终末地的本地引擎与 DAG 引擎必须保持计算结果一致，每次公式修改两处
3. **AI Agent 效果差** — Agent 面对两个结构完全不同的游戏包，无法复用模式

## 决策

采用**纯 DAG 适配器架构**作为所有游戏包的标准模板。明日方舟已是此架构的参考实现，终末地逐步迁移对齐。

### 标准游戏包目录结构

```
games/{game}/
├── __init__.py                    # 包初始化，版本号
├── _package_meta.py               # 包元数据（显示名、版本、支持的框架版本）
│
├── calc/
│   └── dag_adapter/               # [必需] DAG 适配器
│       ├── __init__.py            # 导出 DataContextLoader, compute_snapshot_with_dag
│       ├── loader.py              # DataContextLoader 实现（游戏数据 → 标准化 DataContext）
│       └── adapter.py             # compute_snapshot_with_dag() 实现
│
├── data/                          # [可选] 游戏数据（JSON 文件）
│   ├── DATA_README.md             # 数据来源与许可证说明
│   ├── characters.json
│   ├── weapons.json
│   └── ...
│
├── data_loading/                  # [可选] 数据加载层（仅当需要复杂的数据处理管道时）
│   └── loader.py                  # get_*() / reload_*() 接口
│
├── gui/                           # [可选] GUI 应用
│   └── {Game}App.py               # QMainWindow 子类，轻量，依赖 framework ComputeSheet
│
├── tests/                         # [必需] 测试
│   ├── __init__.py
│   ├── conftest.py                # 游戏共享 fixture
│   ├── test_adapter.py            # DataContextLoader 输出验证
│   ├── test_dag_compute.py        # DAG 计算与快照验证
│   └── ...
│
└── framework_bridge.py            # [必需] 框架桥接入口
```

### 框架适配器目录结构

```
framework/adapters/{game}/
├── meta.json                      # 适配器元数据
├── functions.py                   # DAG 自定义函数（所有伤害公式在此）
├── attr_schema.json               # 属性模式定义
├── ui/
│   └── layout.json                # ComputeSheet 布局
└── *.dag.json                     # 预定义 DAG（可选）
```

### 架构原则

1. **纯 DAG 原则**：所有游戏计算逻辑放在 `framework/adapters/{game}/functions.py` 中，不在 `games/` 内保留独立计算引擎
2. **薄游戏包原则**：`games/{game}/` 只做数据加载 + DAG 适配 + 轻量 GUI，不做重型计算
3. **单计算路径**：不允许"本地引擎 + DAG 引擎"双轨并存；所有公式只有一份实现
4. **显式适配器接口**：`DataContextLoader` 是游戏包向框架暴露的唯一契约

### 终末地迁移路线

```
阶段 1（当前） → 阶段 2（对齐结构） → 阶段 3（纯 DAG）
                                    
games/endfield/                     games/endfield/
├── calc/                           ├── calc/
│   ├── damage/         ← 保留       │   └── dag_adapter/  ← 保留
│   ├── equipment/      ← 保留       ├── data/              ← 保留
│   ├── loadout/        ← 保留       ├── data_loading/      ← 保留
│   ├── search/         ← 保留       │
│   ├── manual_buff/    ← 保留       ├── gui/               ← 新建（单片式）
│   ├── skills/         ← 保留       │   └── EndfieldApp.py
│   ├── multiplicative_zones/        │
│   │   └── ...         ← 保留       ├── tests/             ← 保留
│   └── dag_adapter/    ← 保留       └── framework_bridge.py  ← 保留
│
├── data/                ← 保留     阶段 3（纯 DAG 目标）
├── data_loading/        ← 保留      games/endfield/
├── gui_design/          ← 保留      ├── calc/
│                                    │   └── dag_adapter/
└── framework_bridge.py  ← 保留      ├── data/
                                     ├── data_loading/
                                     ├── gui/EndfieldApp.py
                                     ├── tests/
                                     └── framework_bridge.py
```

## 候选方案

详见 `docs/plans/game-architecture-migration-plan.md`。

## 影响范围

| 阶段 | 影响 | 风险 |
|------|------|------|
| 阶段 2（对齐结构） | `games/endfield/` 目录结构调整 | 低 — 纯文件移动 |
| 阶段 3（纯 DAG） | `games/endfield/calc/damage/` → `adapters/endfield/functions.py` | 高 — 双轨一致性验证 |
| GUI 统一 | `gui_design/` → `gui/EndfieldApp.py` | 中 — 功能覆盖验证 |

## 验证标准

1. [ ] `games/arknights/` 和 `games/endfield/` 的顶层目录结构一致
2. [ ] 终末地的 DAG 计算输出与本地引擎计算结果一致
3. [ ] AGPL-3.0 扫描（`python tools/check_code_origin.py --ci`）通过
4. [ ] 全部 1000+ 测试通过
5. [ ] 按标准模板可快速创建第三个游戏包

## 术语表

- **纯 DAG 适配器架构**：游戏包不包含独立计算引擎，所有计算逻辑以 DAG 自定义函数形式放在框架适配器层
- **薄游戏包**：`games/{game}/` 只做数据加载和适配，不做重型计算
- **单计算路径**：游戏只有一个公式实现源头，不存在需要同步的两套代码
