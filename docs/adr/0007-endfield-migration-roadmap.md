# ADR-0007：终末地计算器→框架迁移路线图

**状态**：已批准  
**日期**：2026-05-28  
**决策者**：维护者  
**影响范围**：`endfield_damage_calculator/calculation/`、`endfield_damage_calculator/gui_design/`、`framework/`

---

## 1. 现状

```
框架 (calc-framework)                终末地计算器
┌──────────────┐                   ┌─────────────────────────┐
│ DAG 引擎     │←──已接──→│ 攻击力链 (ability_bonus +     │
│              │           │         final_attack)         │
│ DataContext  │←──已接──→│ EndfieldContextLoader         │
│ ComputeSheet │──存在但未用──│ endfield_sheet.py           │
│              │           │         (孤立模块)            │
└──────────────┘           │                             │
                           │ 属性乘区 (attribute_zone)    │
                           │ 15 乘区快照 (zone_snapshot)  │
                           │ GUI 面板 (手写)              │
                           │ 搜索/优化 (手写)             │
                           │ 装备系统 (手写)              │
                           └─────────────────────────────┘
```

### 1.1 DAG 覆盖度

`endfield_full.dag.json` 当前覆盖：

| 子图 | 覆盖 | 说明 |
|------|------|------|
| `ability_bonus` | ✅ 完整 | 能力值加成 |
| `final_attack` | ✅ 完整 | 最终攻击力链 |
| `single_hit_damage` | ⚠️ 骨架 | 声明了 15 个乘区参数 + 连乘公式，但各乘区值仍需计算注入 |
| 属性乘区 | ❌ | 力量/敏捷/智识/意志未定义为子图 |
| 防御减伤 | ❌ | 手写 `DefenseReductionZone` |

---

## 2. 迁移阶段

### Phase 1：15 乘区 DAG 完整化（本次推进）

将 15 个伤害乘区的计算逻辑从手写代码迁移为 DAG 子图，覆盖当前 `zone_snapshot.py` 的全部输出。

**具体工作**：

| 乘区 | 当前位置 | 目标 |
|------|---------|------|
| 最终攻击力 | `final_attack_zone.py` | ✅ 已有 DAG 子图 |
| 能力值加成 | `ability_bonus_calc.py` | ✅ 已有 DAG 子图 |
| 属性乘区 | `attribute_zone.py` | ❌ 改为 DAG 子图 |
| 防御减伤 | `base_zone.py` | ❌ 改为 DAG 子图 |
| 暴击乘区 | `zone_snapshot.py` 内联 | ❌ 改为 DAG 子图 |
| 伤害加成乘区 | 同上 | ❌ 改为 DAG 子图 |
| 伤害减免乘区 | 同上 | ❌ 改为 DAG 子图 |
| 提升乘区 | 同上 | ❌ 改为 DAG 子图 |
| 虚弱乘区 | 同上 | ❌ 改为 DAG 子图 |
| 庇护乘区 | 同上 | ❌ 改为 DAG 子图 |
| 脆弱乘区 | 同上 | ❌ 改为 DAG 子图 |
| 易伤乘区 | 同上 | ❌ 改为 DAG 子图 |
| 防御乘区 | 同上（当前是 `defense_reduction` 独立计算） | ❌ 改为 DAG 子图 |
| 失衡乘区 | 同上 | ❌ 改为 DAG 子图 |
| 抗性乘区 | 同上 | ❌ 改为 DAG 子图 |
| 非控制减伤 | 同上 | ❌ 改为 DAG 子图 |
| 连击加成 | 同上 | ❌ 改为 DAG 子图 |
| 特殊乘区 | 同上 | ❌ 改为 DAG 子图 |

**结果**：`zone_snapshot.py` 的旧引擎路径保留作为 fallback，`compute_snapshot_with_dag` 完全用 DAG 求值。

### Phase 2：ComputeSheet 接入主线 GUI

将 `endfield_sheet.py` 真正嵌入主窗口，替换手写的输入控件面板。

| 步骤 | 内容 |
|------|------|
| 2a | 让 `MainWindow` 实例化 `ComputeSheet` 作为右侧面板 |
| 2b | 将角色/武器选择器的变更信号连接 `sheet.rebuild()` |
| 2c | 验证 `layout.json` 覆盖全部输入变量 |
| 2d | 移除旧的手写 `input_panel.py` |

### Phase 3：搜索/优化模块抽象

框架当前无搜索能力。需要将 `calculation/search/` 抽象为框架可选的优化模块。

### Phase 4：数据加载 DAG 化

将角色/武器/装备数据读取路径改为全部通过 `EndfieldContextLoader`，移除 `data/loader.py` 的手写加载。

---

## 3. 本次推进范围（Phase 1）

### 3.1 新增 DAG 子图

| 子图名 | 说明 | 输入来源 |
|--------|------|---------|
| `attribute_zones` | 力量/敏捷/智识/意志最终值 | character 基础 + weapon 加成 |
| `defense_reduction` | 防御减伤率 | enemy.防御, enemy.等级 |
| `crit_zone` | 暴击乘区 = 1 + 暴击率×(暴击伤害 - 1) | character/computed |
| `damage_zones` | 其余 12 乘区聚合 | 全部来自武器技能/computed |

### 3.2 `endfield_full.dag.json` 架构

```yaml
formula.dag.json:
  subgraphs:
    - ability_bonus          # 已有
    - final_attack           # 已有
    - attribute_zones        # 新增
    - defense_reduction      # 新增
    - crit_zone              # 新增
    - damage_bonus_zone      # 新增
    - amplification_zone     # 新增（提升乘区）
    - rest_zones             # 新增（剩余 9 个汇聚）
    - single_hit_damage      # 已有骨架，补全为完整求值
  nodes:
    - (顶层变量节点)
  outputs:
    - (全部乘区中间值 + 最终伤害)
```

### 3.3 适配器改造

`compute_snapshot_with_dag` 从混合模式（DAG + 旧引擎）改为全 DAG 模式：

```
旧: DAG 计算 ability_bonus + final_attack
    + 旧引擎计算 attributes + defense + display details

新: DAG 计算所有乘区
    + 旧引擎仅提供 display formatting（ZoneDisplayLine 文本）
```

---

## 4. 未决定/延后事项

| 事项 | 延后原因 |
|------|---------|
| 搜索/优化模块抽象 | Phase 3，不影响基础功能 |
| 装备系统 DAG 化 | 装备平铺解析当前足够，暂不重构 |
| 多游戏切换 | 待第一个非终末地适配器出现 |
