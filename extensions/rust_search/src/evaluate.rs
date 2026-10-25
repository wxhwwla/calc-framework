// SPDX-License-Identifier: AGPL-3.0
//! 搜索评估热路径 — 效果聚合 + 15 乘区伤害计算。
//!
//! 对应 Python `games/endfield/calc/dag_adapter/search_evaluate.py::evaluate_search_damage`。

use crate::zones;

/// 连击增伤层数表（与 Python combo_bonus.py 一致）
const COMBO_STACKS_SKILL: [f64; 4] = [0.30, 0.45, 0.60, 0.75];
const COMBO_STACKS_ULTIMATE: [f64; 4] = [0.20, 0.30, 0.40, 0.50];

/// 伤害评估结果（浮点部分）。
#[derive(Clone, Debug)]
pub struct EvalResult {
    pub final_damage: f64,
    pub base_damage: f64,
    pub crit: f64,
    pub damage_bonus: f64,
    pub damage_reduction: f64,
    pub amplification: f64,
    pub weakness: f64,
    pub shelter: f64,
    pub fragile: f64,
    pub vulnerability: f64,
    pub defense: f64,
    pub imbalance: f64,
    pub resistance: f64,
    pub non_control_reduction: f64,
    pub combo_bonus: f64,
    pub special: f64,
}

/// 连击增伤加成率。
fn combo_bonus_rate(skill_type: &str, stacks: i32) -> f64 {
    if stacks <= 0 {
        return 0.0;
    }
    let idx = (stacks.min(4) - 1) as usize;
    let table = if skill_type == "终结技" {
        &COMBO_STACKS_ULTIMATE
    } else {
        &COMBO_STACKS_SKILL
    };
    table[idx]
}

/// 连击增伤区乘数。
fn combo_zone_multiplier(skill_type: &str, stacks: i32, flat_legacy_bonus: f64) -> f64 {
    if stacks > 0 {
        1.0 + combo_bonus_rate(skill_type, stacks)
    } else {
        1.0 + flat_legacy_bonus.max(0.0)
    }
}

/// 核心评估函数：接收预处理后的效果列表，累加乘区 → 连乘 → 返回各乘区值。
///
/// # 参数说明
///
/// 多数参数直接对应 Python `evaluate_search_damage` 的同名参数：
/// - `effects`: 预处理后的 (effect_type, value) 元组列表（已过滤、已合并破防效果）
/// - `damage_pipeline`: "abnormal" 时跳过连击增伤和非主控减伤
#[allow(clippy::too_many_arguments)]
pub fn evaluate_search_damage(
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
    _break_defense_stacks: i32, // 效果列表已包含破防易伤，此参数保留 API 兼容
    base_damage_bonus: f64,
    effects: &[(String, f64)],
    crit_mode: &str,
    damage_pipeline: &str,
) -> EvalResult {
    // ---- 1. 初始化累加器 ----
    // dmg_bonus 从 1.0 + 传入的初始加成开始，效果累加直接加在 dmg_bonus 上
    let mut dmg_bonus = 1.0 + damage_type_bonus + skill_type_bonus + imbalance_damage_bonus + other_damage_bonus;
    let mut dmg_reduction = 1.0;
    let mut amplification = 1.0;
    let mut weakness = 1.0;
    let mut shelter_max = 0.0; // 庇护取 max
    let mut fragile = 1.0;
    let mut vulnerability = 1.0;
    let mut combo_bonus_flat = 0.0;
    let mut non_control_reduction = 1.0;
    let mut special_zone_val = 1.0;
    let mut resistance_extra = 0.0;
    let mut resistance_change = 0.0;
    let mut defense_change = 0.0;
    let mut imbalance_coeff_override: Option<f64> = None;

    // ---- 2. 效果累加循环（热路径核心） ----
    for (et, v) in effects {
        match et.as_str() {
            "伤害减免" => dmg_reduction *= 1.0 - v,
            "增幅" => amplification += v,
            "虚弱" => weakness *= 1.0 - v,
            "庇护" => {
                if *v > shelter_max {
                    shelter_max = *v;
                }
            }
            "脆弱" => fragile += v,
            "易伤" => vulnerability += v,
            "连击增伤" => combo_bonus_flat += v,
            "伤害类型伤害加成" | "技能类型伤害加成" | "失衡伤害加成" | "其他伤害加成" => {
                dmg_bonus += v;
            }
            "无视抗性" => resistance_extra += v,
            "抗性" => resistance_change += v,
            "防御" => defense_change += v,
            "失衡易伤系数" => {
                imbalance_coeff_override = Some(*v);
            }
            "非主控减伤" => non_control_reduction *= 1.0 - v,
            "特殊乘区" => special_zone_val *= v,
            _ => { /* 未知效果类型，Python 侧已过滤 */ }
        }
    }

    // ---- 3. 庇护取 max ----
    let shelter = 1.0 - shelter_max;

    // ---- 5. 连击增伤（abnormal pipeline 跳过） ----
    let combo_bonus = if damage_pipeline == "abnormal" {
        1.0
    } else {
        combo_zone_multiplier(skill_type, combo_stacks, combo_bonus_flat.max(0.0))
    };

    // ---- 6. 非主控减伤（abnormal pipeline 跳过） ----
    let ncr = if damage_pipeline == "abnormal" {
        1.0
    } else {
        non_control_reduction
    };

    // ---- 7. 失衡易伤系数 ----
    let imb_coeff = imbalance_coeff_override.unwrap_or(imbalance_vulnerability_coeff);

    // ---- 8. 抗性 ----
    let total_resistance = enemy_resistance + resistance_change;
    let total_ignore = ignore_resistance + resistance_extra;

    // ---- 9. 防御区变化 ----
    let effective_def = (enemy_defense + defense_change).max(0.0);

    // ---- 10. 调用各乘区函数 ----
    let base = zones::base_damage_zone(final_attack, skill_multiplier, base_damage_bonus);
    let crit = zones::crit_zone(crit_rate, crit_damage, crit_mode);
    // damage_type_bonus 实际是总 dmg_bonus - 1.0
    let db = 1.0 + (dmg_bonus - 1.0);
    let dr = 1.0 - (1.0 - dmg_reduction); // damage_reduction_zone
    let amp = amplification;
    let wk = weakness;
    let sh = shelter;
    let fr = fragile;
    let vu = vulnerability;
    let dff = if is_true_damage {
        1.0
    } else {
        100.0 / (effective_def + 100.0)
    };
    let imb = if is_unbalanced { imb_coeff } else { 1.0 };
    let res = 1.0 - total_resistance / 100.0 + total_ignore / 100.0;
    let ncr_final = ncr;
    let com = combo_bonus;
    let sp = special_zone_val;

    let final_damage = base * crit * db * dr * amp * wk * sh * fr * vu * dff * imb * res * ncr_final * com * sp;

    EvalResult {
        final_damage,
        base_damage: base,
        crit,
        damage_bonus: db,
        damage_reduction: dr,
        amplification: amp,
        weakness: wk,
        shelter: sh,
        fragile: fr,
        vulnerability: vu,
        defense: dff,
        imbalance: imb,
        resistance: res,
        non_control_reduction: ncr_final,
        combo_bonus: com,
        special: sp,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// 辅助：构造 effects 切片
    fn eff(pairs: &[(&str, f64)]) -> Vec<(String, f64)> {
        pairs.iter().map(|(k, v)| (k.to_string(), *v)).collect()
    }

    #[test]
    fn test_basic_no_effects() {
        let r = evaluate_search_damage(
            1000.0, 2.0, "战技", false, false,
            200.0, 0.0, 0.0, 1.3, 0.05, 0.5, 0.0, 0.0, 0.0, 0.0,
            0, 0, 0.0, &[], "non_crit", "normal",
        );
        // 2000 * 100/300 = 666.666...
        assert!((r.final_damage - 2000.0 * 100.0 / 300.0).abs() < 1e-9);
    }

    #[test]
    fn test_damage_bonus_effect() {
        let effects = eff(&[("伤害类型伤害加成", 0.5)]);
        let r = evaluate_search_damage(
            1000.0, 2.0, "战技", false, false,
            200.0, 0.0, 0.0, 1.3, 0.05, 0.5, 0.0, 0.0, 0.0, 0.0,
            0, 0, 0.0, &effects, "non_crit", "normal",
        );
        // 2000 * 1.5 * 100/300 = 1000.0
        assert!((r.final_damage - 1000.0).abs() < 1e-9);
    }

    #[test]
    fn test_true_damage_skips_defense() {
        let r = evaluate_search_damage(
            1000.0, 2.0, "战技", true, false,
            9999.0, 0.0, 0.0, 1.3, 0.05, 0.5, 0.0, 0.0, 0.0, 0.0,
            0, 0, 0.0, &[], "non_crit", "normal",
        );
        assert!((r.final_damage - 2000.0).abs() < 1e-9);
    }

    #[test]
    fn test_shelter_max() {
        let effects = eff(&[("庇护", 0.3), ("庇护", 0.5), ("庇护", 0.1)]);
        let r = evaluate_search_damage(
            1000.0, 2.0, "战技", false, false,
            0.0, 0.0, 0.0, 1.3, 0.05, 0.5, 0.0, 0.0, 0.0, 0.0,
            0, 0, 0.0, &effects, "non_crit", "normal",
        );
        // 2000 * (1 - 0.5) = 1000
        assert!((r.final_damage - 1000.0).abs() < 1e-9);
    }

    #[test]
    fn test_imbalance_override() {
        let effects = eff(&[("失衡易伤系数", 2.0)]);
        let r = evaluate_search_damage(
            1000.0, 2.0, "战技", false, true,
            0.0, 0.0, 0.0, 1.3, 0.05, 0.5, 0.0, 0.0, 0.0, 0.0,
            0, 0, 0.0, &effects, "non_crit", "normal",
        );
        // 2000 * 2.0 = 4000
        assert!((r.final_damage - 4000.0).abs() < 1e-9);
    }

    #[test]
    fn test_combo_stacks() {
        let r = evaluate_search_damage(
            1000.0, 2.0, "战技", false, false,
            0.0, 0.0, 0.0, 1.3, 0.05, 0.5, 0.0, 0.0, 0.0, 0.0,
            2, 0, 0.0, &[], "non_crit", "normal",
        );
        // 2000 * (1.0 + 0.45) = 2900
        assert!((r.final_damage - 2900.0).abs() < 1e-9);
    }

    #[test]
    fn test_combo_stacks_ultimate() {
        let r = evaluate_search_damage(
            1000.0, 2.0, "终结技", false, false,
            0.0, 0.0, 0.0, 1.3, 0.05, 0.5, 0.0, 0.0, 0.0, 0.0,
            3, 0, 0.0, &[], "non_crit", "normal",
        );
        // 2000 * (1.0 + 0.40) = 2800
        assert!((r.final_damage - 2800.0).abs() < 1e-9);
    }

    #[test]
    fn test_abnormal_pipeline_skips_combo_and_ncr() {
        let effects = eff(&[("非主控减伤", 0.3)]);
        let r = evaluate_search_damage(
            1000.0, 2.0, "战技", false, false,
            0.0, 0.0, 0.0, 1.3, 0.05, 0.5, 0.0, 0.0, 0.0, 0.0,
            4, 0, 0.0, &effects, "non_crit", "abnormal",
        );
        // abnormal 跳过连击增伤和非主控减伤
        // 2000 * 1.0(combo) * 1.0(ncr) = 2000
        assert!((r.final_damage - 2000.0).abs() < 1e-9);
    }

    #[test]
    fn test_break_defense_vulnerability() {
        // 破防易伤现在通过效果列表传入（Python 侧 damage_effects_from_break_defense）
        let effects = eff(&[("易伤", 0.24)]); // 3 层 × 0.08
        let r = evaluate_search_damage(
            1000.0, 1.0, "战技", false, false,
            0.0, 0.0, 0.0, 1.3, 0.05, 0.5, 0.0, 0.0, 0.0, 0.0,
            0, 0, 0.0, &effects, "non_crit", "normal",
        );
        // 1000 * (1 + 0.24) = 1240
        assert!((r.final_damage - 1240.0).abs() < 1e-9);
    }

    #[test]
    fn test_all_effect_types() {
        let effects = eff(&[
            ("伤害减免", 0.2),
            ("增幅", 0.3),
            ("虚弱", 0.1),
            ("庇护", 0.25),
            ("脆弱", 0.15),
            ("易伤", 0.1),
            ("连击增伤", 0.5),
            ("伤害类型伤害加成", 0.2),
            ("无视抗性", 20.0),
            ("抗性", -10.0),
            ("防御", -50.0),
            ("非主控减伤", 0.1),
            ("特殊乘区", 1.5),
        ]);
        let r = evaluate_search_damage(
            1000.0, 2.0, "战技", false, false,
            200.0, 30.0, 0.0, 1.3, 0.05, 0.5, 0.1, 0.05, 0.0, 0.0,
            0, 0, 0.0, &effects, "non_crit", "normal",
        );
        // 基础 = 2000
        // 暴击 = 1.0
        // 伤害加成 = 1.0 + 0.1 + 0.05 + 0.2 = 1.35
        // 伤害减免 = 1 - 0.2 = 0.8
        // 增幅 = 1 + 0.3 = 1.3
        // 虚弱 = 1 - 0.1 = 0.9
        // 庇护 = 1 - 0.25 = 0.75
        // 脆弱 = 1 + 0.15 = 1.15
        // 易伤 = 1 + 0.1 = 1.1
        // 防御 = 100 / (150 + 100) = 0.4
        // 失衡 = 1.0
        // 抗性 = 1 - (30 + (-10))/100 + 20/100 = 1.0
        // 非主控 = 1 - 0.1 = 0.9
        // 连击 = 1 + 0.5 = 1.5
        // 特殊 = 1.5
        let expected = 2000.0 * 1.0 * 1.35 * 0.8 * 1.3 * 0.9 * 0.75 * 1.15 * 1.1
            * (100.0 / 250.0) * 1.0 * 1.0 * 0.9 * 1.5 * 1.5;
        assert!((r.final_damage - expected).abs() < 1e-6);
    }

    #[test]
    fn test_vs_python_reference() {
        // 这个测试用例与 search_evaluate.py 里的场景一致
        let effects = eff(&[
            ("伤害类型伤害加成", 0.3),
            ("易伤", 0.15),
        ]);
        let r = evaluate_search_damage(
            // 艾拉: ATK=473, 2.0x倍率, DEF=200
            473.73, 2.0, "战技", false, false,
            200.0, 0.0, 0.0, 1.3, 0.05, 0.5, 0.0, 0.0, 0.0, 0.0,
            0, 0, 0.0, &effects, "non_crit", "normal",
        );
        // 基础 = 947.46
        // 伤害加成 = 1.3
        // 防御 = 100/300 = 0.333...
        // 易伤 = 1.15
        let expected = 947.46 * 1.3 * (100.0 / 300.0) * 1.15;
        assert!((r.final_damage - expected).abs() < 0.01);
    }
}
