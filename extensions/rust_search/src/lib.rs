// SPDX-License-Identifier: AGPL-3.0
//! Rust 加速扩展 — Calc Framework 全量搜索热路径。
//!
//! 本扩展通过 PyO3 向 Python 暴露高性能的伤害计算函数，
//! 用于替代纯 Python 实现的 `evaluate_search_damage` 及其 15 乘区函数。
//!
//! # 设计原则
//!
//! - **保留 Python 降级路径**：Rust 扩展不可用时自动 fallback 到 Python 版
//! - **逐组合验证**：Python 与 Rust 版输出逐值对比，误差 ≤ 1e-9
//! - **渐进式迁移**：先从纯算术的 15 乘区开始，逐步扩展

mod evaluate;
mod inverse;
mod zones;

use pyo3::prelude::*;

/// 15 乘区连乘计算最终伤害。
///
/// 与 `framework/adapters/endfield/functions.py::compute_15_zone_damage` 完全一致。
#[pyfunction]
#[pyo3(signature = (
    final_attack,
    skill_multiplier = 1.0,
    base_damage_bonus = 0.0,
    crit_rate = 0.05,
    crit_damage = 0.5,
    crit_mode = "non_crit",
    damage_type_bonus = 0.0,
    damage_reduction = 0.0,
    amplification = 0.0,
    weakness = 0.0,
    shelter = 0.0,
    fragile = 0.0,
    vulnerability = 0.0,
    enemy_defense = 100.0,
    defense_change = 0.0,
    is_true_damage = false,
    imbalance_coeff = 1.3,
    is_unbalanced = false,
    enemy_resistance = 0.0,
    ignore_resistance = 0.0,
    non_control_reduction = 0.0,
    combo_bonus = 0.0,
    special = 1.0,
))]
fn compute_15_zone_damage(
    final_attack: f64,
    skill_multiplier: f64,
    base_damage_bonus: f64,
    crit_rate: f64,
    crit_damage: f64,
    crit_mode: &str,
    damage_type_bonus: f64,
    damage_reduction: f64,
    amplification: f64,
    weakness: f64,
    shelter: f64,
    fragile: f64,
    vulnerability: f64,
    enemy_defense: f64,
    defense_change: f64,
    is_true_damage: bool,
    imbalance_coeff: f64,
    is_unbalanced: bool,
    enemy_resistance: f64,
    ignore_resistance: f64,
    non_control_reduction: f64,
    combo_bonus: f64,
    special: f64,
) -> f64 {
    let base = zones::base_damage_zone(final_attack, skill_multiplier, base_damage_bonus);
    let crit = zones::crit_zone(crit_rate, crit_damage, crit_mode);
    let db = 1.0 + damage_type_bonus;
    let dr = zones::damage_reduction_zone(damage_reduction);
    let amp = zones::amplification_zone(amplification);
    let wk = zones::weakness_zone(weakness);
    let sh = zones::shelter_zone(shelter);
    let fr = zones::fragile_zone(fragile);
    let vu = zones::vulnerability_zone(vulnerability);
    let dff = zones::defense_zone(enemy_defense, defense_change, is_true_damage);
    let imb = zones::imbalance_zone(imbalance_coeff, is_unbalanced);
    let res = zones::resistance_zone(enemy_resistance, ignore_resistance);
    let ncr = zones::non_control_reduction_zone(non_control_reduction);
    let com = zones::combo_bonus_zone(combo_bonus);
    let sp = zones::special_zone(special);
    base * crit * db * dr * amp * wk * sh * fr * vu * dff * imb * res * ncr * com * sp
}

/// 完整搜索评估：接收预处理后的效果列表，累加乘区 → 连乘 → 返回结果。
///
/// 对应 Python `search_evaluate.py::evaluate_search_damage`。
/// `effects` 参数为 (effect_type: str, value: float) 元组列表（已过滤）。
#[pyfunction]
#[pyo3(signature = (
    final_attack,
    skill_multiplier,
    skill_type = "战技",
    is_true_damage = false,
    is_unbalanced = false,
    enemy_defense = 100.0,
    enemy_resistance = 0.0,
    ignore_resistance = 0.0,
    imbalance_vulnerability_coeff = 1.3,
    crit_rate = 0.05,
    crit_damage = 0.5,
    damage_type_bonus = 0.0,
    skill_type_bonus = 0.0,
    imbalance_damage_bonus = 0.0,
    other_damage_bonus = 0.0,
    combo_stacks = 0,
    break_defense_stacks = 0,
    base_damage_bonus = 0.0,
    effects = Vec::new(),
    crit_mode = "non_crit",
    damage_pipeline = "normal",
))]
fn evaluate_search_damage(
    final_attack: f64,
    skill_multiplier: f64,
    skill_type: &str,
    is_true_damage: bool,
    is_unbalanced: bool,
    enemy_defense: f64,
    enemy_resistance: f64,
    ignore_resistance: f64,
    imbalance_vulnerability_coeff: f64,
    crit_rate: f64,
    crit_damage: f64,
    damage_type_bonus: f64,
    skill_type_bonus: f64,
    imbalance_damage_bonus: f64,
    other_damage_bonus: f64,
    combo_stacks: i32,
    break_defense_stacks: i32,
    base_damage_bonus: f64,
    effects: Vec<(String, f64)>,
    crit_mode: &str,
    damage_pipeline: &str,
) -> PyResult<PyDamageEvalResult> {
    let result = evaluate::evaluate_search_damage(
        final_attack,
        skill_multiplier,
        skill_type,
        is_true_damage,
        is_unbalanced,
        enemy_defense,
        enemy_resistance,
        ignore_resistance,
        imbalance_vulnerability_coeff,
        crit_rate,
        crit_damage,
        damage_type_bonus,
        skill_type_bonus,
        imbalance_damage_bonus,
        other_damage_bonus,
        combo_stacks,
        break_defense_stacks,
        base_damage_bonus,
        &effects,
        crit_mode,
        damage_pipeline,
    );

    let mut zone_values = std::collections::HashMap::new();
    zone_values.insert("基础伤害区".to_string(), result.base_damage);
    zone_values.insert("暴击区".to_string(), result.crit);
    zone_values.insert("伤害加成区".to_string(), result.damage_bonus);
    zone_values.insert("伤害减免区".to_string(), result.damage_reduction);
    zone_values.insert("增幅区".to_string(), result.amplification);
    zone_values.insert("虚弱区".to_string(), result.weakness);
    zone_values.insert("庇护区".to_string(), result.shelter);
    zone_values.insert("脆弱区".to_string(), result.fragile);
    zone_values.insert("易伤区".to_string(), result.vulnerability);
    zone_values.insert("防御区".to_string(), result.defense);
    zone_values.insert("失衡易伤区".to_string(), result.imbalance);
    zone_values.insert("抗性区".to_string(), result.resistance);
    zone_values.insert("非主控减伤区".to_string(), result.non_control_reduction);
    zone_values.insert("连击增伤区".to_string(), result.combo_bonus);
    zone_values.insert("特殊乘区".to_string(), result.special);

    Ok(PyDamageEvalResult {
        final_damage: result.final_damage,
        zone_values,
        warnings: Vec::new(),
        unknown_effects: Vec::new(),
    })
}

/// 批量评估：一次性计算 N 个组合的伤害值，摊销 FFI 开销。
///
/// 每个参数为长度 N 的 Vec，与 `evaluate_search_damage` 的单参数一一对应。
#[pyfunction]
fn evaluate_search_damage_batch(
    final_attacks: Vec<f64>,
    skill_multipliers: Vec<f64>,
    skill_types: Vec<String>,
    is_true_damages: Vec<bool>,
    is_unbalanceds: Vec<bool>,
    enemy_defenses: Vec<f64>,
    enemy_resistances: Vec<f64>,
    ignore_resistances: Vec<f64>,
    imbalance_vulnerability_coeffs: Vec<f64>,
    crit_rates: Vec<f64>,
    crit_damages: Vec<f64>,
    damage_type_bonuses: Vec<f64>,
    skill_type_bonuses: Vec<f64>,
    imbalance_damage_bonuses: Vec<f64>,
    other_damage_bonuses: Vec<f64>,
    combo_stacks_list: Vec<i32>,
    break_defense_stacks_list: Vec<i32>,
    base_damage_bonuses: Vec<f64>,
    effects_batch: Vec<Vec<(String, f64)>>,
    crit_modes: Vec<String>,
    damage_pipelines: Vec<String>,
) -> PyResult<Vec<f64>> {
    let n = final_attacks.len();
    let mut results = Vec::with_capacity(n);

    for i in 0..n {
        let r = evaluate::evaluate_search_damage(
            final_attacks[i],
            skill_multipliers[i],
            &skill_types[i],
            is_true_damages[i],
            is_unbalanceds[i],
            enemy_defenses[i],
            enemy_resistances[i],
            ignore_resistances[i],
            imbalance_vulnerability_coeffs[i],
            crit_rates[i],
            crit_damages[i],
            damage_type_bonuses[i],
            skill_type_bonuses[i],
            imbalance_damage_bonuses[i],
            other_damage_bonuses[i],
            combo_stacks_list[i],
            break_defense_stacks_list[i],
            base_damage_bonuses[i],
            &effects_batch[i],
            &crit_modes[i],
            &damage_pipelines[i],
        );
        results.push(r.final_damage);
    }
    Ok(results)
}

/// 伤害评估结果，与 Python `DamageEvalResult` 保持字段一致。
#[pyclass(name = "DamageEvalResult")]
#[derive(Clone, Debug)]
pub struct PyDamageEvalResult {
    #[pyo3(get)]
    pub final_damage: f64,
    #[pyo3(get)]
    pub zone_values: std::collections::HashMap<String, f64>,
    #[pyo3(get)]
    pub warnings: Vec<String>,
    #[pyo3(get)]
    pub unknown_effects: Vec<Vec<(String, String)>>,
}

/// 公式反推搜索：用 floor_linear 公式拟合等级数据。
///
/// 对应 ``calc_framework/inverse/base.py::FloorFormulaFitter.fit()``。
/// 接受缩放后的整数数据和搜索范围，返回 (growth, divisor, offset, scale_factor, max_error, is_exact)。
#[pyfunction]
#[pyo3(signature = (
    scaled_data,
    scaled_base,
    scale_factor,
    divisor_start = 1,
    divisor_end = 501,
    growth_start = 1,
    growth_end = 10001,
    offset_search_limit = 500,
))]
fn fit_floor_formula_py(
    scaled_data: Vec<i64>,
    scaled_base: i64,
    scale_factor: i64,
    divisor_start: i64,
    divisor_end: i64,
    growth_start: i64,
    growth_end: i64,
    offset_search_limit: i64,
) -> PyResult<Option<(i64, i64, i64, i64, f64, bool)>> {
    let result = inverse::fit_floor_formula(
        &scaled_data,
        scaled_base,
        scale_factor,
        divisor_start,
        divisor_end,
        growth_start,
        growth_end,
        offset_search_limit,
    );
    Ok(result.map(|r| (r.growth, r.divisor, r.offset, r.scale_factor, r.max_error, r.is_exact)))
}

/// Python 模块注册。
#[pymodule]
fn rust_search(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(compute_15_zone_damage, m)?)?;
    m.add_function(wrap_pyfunction!(evaluate_search_damage, m)?)?;
    m.add_function(wrap_pyfunction!(evaluate_search_damage_batch, m)?)?;
    m.add_function(wrap_pyfunction!(fit_floor_formula_py, m)?)?;
    m.add_class::<PyDamageEvalResult>()?;
    Ok(())
}
