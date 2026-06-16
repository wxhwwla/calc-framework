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

mod zones;

use pyo3::prelude::*;

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

/// 15 乘区连乘计算最终伤害。
///
/// 与 `framework/adapters/endfield/functions.py::compute_15_zone_damage` 完全一致。
///
/// # Parameters
///
/// 参数名与 Python 版 `compute_15_zone_detail` 一一对应，方便调用方直接映射。
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

/// Python 模块注册。
#[pymodule]
fn rust_search(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(compute_15_zone_damage, m)?)?;
    m.add_class::<PyDamageEvalResult>()?;
    Ok(())
}
