# Rust 全批量评估方案

> **目标**：将整个搜索评估循环移到 Rust，消除 Python 逐任务开销，实现 ~5 秒完成 97 万组合遍历。

**当前状态（2026-07-30）**：目录展开 helper + 回归测试已合入；`CALC_RUST_FULL_BATCH=1` 实验开关已加。默认搜索仍走 Tier-3 SoA；全批量接入 runner 仍待下一步。

---

## 1. 当前瓶颈分析

### 1.1 性能现状

| 场景 | 速度 | 时间 |
|------|------|------|
| 首次搜索（新角色） | ~36k/s | ~34s |
| 重复搜索（同角色） | ~30k/s | ~30s |
| 换角色后 | ~7.6k/s | ~75s |

### 1.2 瓶颈分布

```
每个任务 (~30μs):
├─ build_runtime_eval_snapshot (~15μs) [Python]
│   ├─ 缓存查找 (~3μs)
│   ├─ final_attack_details_for_loadout (~10μs) [缓存命中]
│   └─ dict 构建 (~2μs)
├─ 参数 dict 构建 (~8μs) [Python]
├─ evaluate_search_batch_soa (~5μs) [Rust FFI 摊销]
└─ 其他 (~2μs) [Python]
```

**Python 开销占比**：~25μs/任务（83%）
**Rust 开销占比**：~5μs/任务（17%）

### 1.3 根本原因

Python 的 GIL 和逐任务函数调用开销无法通过多线程消除。必须将整个评估循环移到 Rust。

---

## 2. 目标架构

### 2.1 新 Rust 函数签名

```rust
/// 全批量评估：Python 预处理 → Rust 完整评估 → 返回结果
#[pyfunction]
fn evaluate_full_batch(
    // 武器数据（每武器一个）
    weapon_names: Vec<String>,
    weapon_final_attacks: Vec<f64>,
    weapon_effects: Vec<Vec<(String, f64)>>,

    // 装备数据（每装备组合一个）
    equipment_combos: Vec<EquipmentCombo>,

    // 角色数据（全局）
    char_data: CharData,

    // 计算参数（全局）
    calc_params: CalcParams,

    // 搜索配置
    top_n: usize,
) -> Vec<LoadoutResult>
```

### 2.2 数据结构

```rust
/// 装备组合
struct EquipmentCombo {
    chest_name: String,
    gloves_name: String,
    acc_a_name: String,
    acc_b_name: String,
    effects: Vec<(String, f64)>,
    flat_stats: HashMap<String, f64>,
    atk_percent: f64,
}

/// 角色数据
struct CharData {
    name: String,
    level: usize,
    base_attack: f64,
    // ... 其他属性
}

/// 计算参数
struct CalcParams {
    skill_multiplier: f64,
    damage_type: String,
    skill_type: String,
    enemy_defense: f64,
    enemy_resistance: f64,
    // ... 其他参数
}

/// 配装结果
struct LoadoutResult {
    weapon_name: String,
    final_damage: f64,
    loadout_names: HashMap<String, String>,
}
```

### 2.3 Rust 内部流程

```rust
fn evaluate_full_batch(...) -> Vec<LoadoutResult> {
    let mut results = Vec::new();

    for weapon in weapons {
        for equipment in equipment_combos {
            // 1. 计算 final_attack（Rust 内部）
            let final_attack = calculate_final_attack(
                &char_data, weapon, &equipment
            );

            // 2. 合并效果列表
            let effects = merge_effects(&weapon.effects, &equipment.effects);

            // 3. 计算伤害（已有 Rust 实现）
            let damage = evaluate_damage(
                final_attack, &effects, &calc_params
            );

            results.push(LoadoutResult {
                weapon_name: weapon.name.clone(),
                final_damage: damage,
                loadout_names: equipment.names(),
            });
        }
    }

    // 4. 排序返回 TopN
    results.sort_by(|a, b| b.final_damage.partial_cmp(&a.final_damage).unwrap());
    results.truncate(top_n);
    results
}
```

---

## 3. 实施计划

### Phase 1：数据预处理（Python 侧）

**目标**：在 Python 侧预处理所有数据，转换为 Rust 可接受的格式。

**任务**：
1. 预处理武器数据（名称、基础攻击、效果列表）
2. 预处理装备数据（名称、效果、flat_stats、atk_percent）
3. 预处理角色数据（名称、等级、基础属性）
4. 预处理计算参数（技能倍率、敌方属性等）

**预期工作量**：1-2 天

### Phase 2：Rust 核心函数

**目标**：实现 Rust 侧的完整评估函数。

**任务**：
1. 实现 `calculate_final_attack` 函数
   - 从武器数据提取基础攻击
   - 计算能力值加成
   - 应用装备 flat_stats 和 atk_percent
   - 返回最终攻击力

2. 实现 `merge_effects` 函数
   - 合并武器效果和装备效果
   - 处理效果类型转换

3. 实现 `evaluate_damage` 函数
   - 复用现有的 `eval_single` 函数
   - 应用 15 乘区计算

4. 实现 `evaluate_full_batch` 函数
   - 遍历所有武器+装备组合
   - 调用上述函数
   - 排序返回 TopN

**预期工作量**：3-5 天

### Phase 3：Python 集成

**目标**：将 Rust 函数集成到 Python 搜索流程中。

**任务**：
1. 在 `rust_bridge.py` 中添加 `evaluate_full_batch` 包装函数
2. 修改 `task_batch.py` 使用新函数
3. 添加降级路径（Rust 不可用时使用 Python）

**预期工作量**：1-2 天

### Phase 4：测试与验证

**目标**：确保功能正确性和性能提升。

**任务**：
1. 单元测试：验证 Rust 函数输出与 Python 一致
2. 集成测试：验证搜索流程完整工作
3. 性能测试：对比优化前后速度
4. 边界测试：验证极端情况（空数据、大量组合等）

**预期工作量**：1-2 天

---

## 4. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Rust 实现错误 | 计算结果不正确 | 与 Python 版本逐值对比验证 |
| 性能提升不明显 | 投入产出比低 | 先做 POC 验证，再决定是否继续 |
| 代码复杂度增加 | 维护成本上升 | 充分文档化，保持降级路径 |
| 与现有代码冲突 | 功能回归 | 保持向后兼容，渐进式迁移 |

---

## 5. 成功标准

| 指标 | 当前 | 目标 |
|------|------|------|
| 首次搜索时间 | ~34s | <10s |
| 重复搜索时间 | ~30s | <5s |
| 换角色后搜索 | ~75s | <10s |
| 内存占用 | ~200MB | <500MB |

---

## 6. 依赖项

- Rust 工具链（已安装）
- PyO3 绑定（已配置）
- 现有 Rust 扩展（`rust_search`）

---

## 7. 时间线

| 阶段 | 预计时间 | 状态 |
|------|----------|------|
| Phase 1：数据预处理 | 1-2 天 | ⬜ |
| Phase 2：Rust 核心函数 | 3-5 天 | ⬜ |
| Phase 3：Python 集成 | 1-2 天 | ⬜ |
| Phase 4：测试与验证 | 1-2 天 | ⬜ |
| **总计** | **6-11 天** | ⬜ |

---

## 8. 备选方案

如果 Rust 全批量方案太复杂，可以考虑以下备选方案：

### 方案 A：优化 Python 预处理
- 减少 dict 构建开销
- 使用更高效的数据结构
- 预期提升：1.5-2x

### 方案 B：多进程并行
- 使用 ProcessPoolExecutor
- 绕过 GIL 限制
- 预期提升：2-4x（取决于 CPU 核心数）

### 方案 C：缓存策略优化
- 使用更简单的缓存键
- 预热更多组合
- 预期提升：1.5-2x

---

## 9. 决策点

**是否继续？**

- ✅ 如果目标是 <10 秒 → 必须做 Rust 全批量
- ⚠️ 如果目标是 <30 秒 → 可以尝试备选方案
- ❌ 如果目标是 <5 秒 → Rust 全批量是唯一选择

**建议**：继续实施 Rust 全批量方案，因为这是唯一能达到 <10 秒目标的方法。
