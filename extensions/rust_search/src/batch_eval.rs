// SPDX-License-Identifier: AGPL-3.0
//! SoA 批量评估引擎 — 零 Python 调用的内部循环。
//!
//! 接收预处理后的 Structure-of-Arrays 格式数据，在 Rust 内部完成
//! 效果累加 + 15 乘区计算，返回 `Vec<f64>`。

use crate::effect_id::*;
use crate::zones;

/// 连击增伤层数表
const COMBO_STACKS_SKILL: [f64; 4] = [0.30, 0.45, 0.60, 0.75];
const COMBO_STACKS_ULTIMATE: [f64; 4] = [0.20, 0.30, 0.40, 0.50];

/// SoA 格式批量输入。
pub struct BatchInput<'a> {
    pub final_attacks: &'a [f64],
    pub skill_multipliers: &'a [f64],
    pub skill_type_ids: &'a [u8],
    pub is_true_damages: &'a [bool],
    pub is_unbalanceds: &'a [bool],
    pub enemy_defenses: &'a [f64],
    pub enemy_resistances: &'a [f64],
    pub ignore_resistances: &'a [f64],
    pub imbalance_vulnerability_coeffs: &'a [f64],
    pub crit_rates: &'a [f64],
    pub crit_damages: &'a [f64],
    pub damage_type_bonuses: &'a [f64],
    pub skill_type_bonuses: &'a [f64],
    pub imbalance_damage_bonuses: &'a [f64],
    pub other_damage_bonuses: &'a [f64],
    pub combo_stacks_list: &'a [i32],
    pub break_defense_stacks_list: &'a [i32],
    pub base_damage_bonuses: &'a [f64],
    pub effect_ids_batch: &'a [Vec<u8>],
    pub effect_values_batch: &'a [Vec<f64>],
    pub crit_mode_ids: &'a [u8],
    pub damage_pipelines: &'a [bool], // true = "abnormal"
}

/// 单次评估的内联热路径（无函数调用开销）。
#[inline(always)]
fn eval_single(
    final_attack: f64,
    skill_multiplier: f64,
    skill_type_id: u8,
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
    _break_defense_stacks: i32,
    base_damage_bonus: f64,
    effect_ids: &[u8],
    effect_values: &[f64],
    crit_mode_id: u8,
    is_abnormal: bool,
) -> f64 {
    // ---- 1. 初始化累加器 ----
    let mut dmg_bonus =
        1.0 + damage_type_bonus + skill_type_bonus + imbalance_damage_bonus + other_damage_bonus;
    let mut dmg_reduction = 1.0_f64;
    let mut amplification = 1.0_f64;
    let mut weakness = 1.0_f64;
    let mut shelter_max = 0.0_f64;
    let mut fragile = 1.0_f64;
    let mut vulnerability = 1.0_f64;
    let mut combo_bonus_flat = 0.0_f64;
    let mut non_control_reduction = 1.0_f64;
    let mut special_zone_val = 1.0_f64;
    let mut resistance_extra = 0.0_f64;
    let mut resistance_change = 0.0_f64;
    let mut defense_change = 0.0_f64;
    let mut imbalance_coeff_override: Option<f64> = None;

    // ---- 2. 效果累加（整数 ID 匹配） ----
    let len = effect_ids.len();
    for i in 0..len {
        let v = unsafe { *effect_values.get_unchecked(i) };
        match unsafe { *effect_ids.get_unchecked(i) } {
            EFFECT_DAMAGE_REDUCTION => dmg_reduction *= 1.0 - v,
            EFFECT_AMPLIFICATION => amplification += v,
            EFFECT_WEAKNESS => weakness *= 1.0 - v,
            EFFECT_SHELTER => {
                if v > shelter_max {
                    shelter_max = v;
                }
            }
            EFFECT_FRAGILE => fragile += v,
            EFFECT_VULNERABILITY => vulnerability += v,
            EFFECT_COMBO_BONUS => combo_bonus_flat += v,
            EFFECT_DAMAGE_BONUS => dmg_bonus += v,
            EFFECT_IGNORE_RESISTANCE => resistance_extra += v,
            EFFECT_RESISTANCE => resistance_change += v,
            EFFECT_DEFENSE => defense_change += v,
            EFFECT_IMBALANCE_COEFF => imbalance_coeff_override = Some(v),
            EFFECT_NON_CONTROL_REDUCTION => non_control_reduction *= 1.0 - v,
            EFFECT_SPECIAL_ZONE => special_zone_val *= v,
            _ => {}
        }
    }

    // ---- 3. 庇护取 max ----
    let shelter = 1.0 - shelter_max;

    // ---- 5. 连击增伤 ----
    let combo_bonus = if is_abnormal {
        1.0
    } else if combo_stacks > 0 {
        let idx = (combo_stacks.min(4) - 1) as usize;
        let table = if skill_type_id == SKILL_TYPE_ULTIMATE {
            &COMBO_STACKS_ULTIMATE
        } else {
            &COMBO_STACKS_SKILL
        };
        1.0 + table[idx]
    } else {
        1.0 + combo_bonus_flat.max(0.0)
    };

    // ---- 6. 非主控减伤 ----
    let ncr = if is_abnormal {
        1.0
    } else {
        non_control_reduction
    };

    // ---- 7. 失衡易伤系数 ----
    let imb_coeff = imbalance_coeff_override.unwrap_or(imbalance_vulnerability_coeff);

    // ---- 8. 抗性 ----
    let total_resistance = enemy_resistance + resistance_change;
    let total_ignore = ignore_resistance + resistance_extra;

    // ---- 9. 防御区 ----
    let effective_def = (enemy_defense + defense_change).max(0.0);

    // ---- 10. 15 乘区连乘 ----
    let base = zones::base_damage_zone(final_attack, skill_multiplier, base_damage_bonus);
    let crit = match crit_mode_id {
        CRIT_MODE_ALWAYS_CRIT => 1.0 + crit_damage,
        CRIT_MODE_EXPECTED => 1.0 + crit_rate * crit_damage,
        _ => 1.0,
    };
    let db = dmg_bonus;
    let dr = dmg_reduction;
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
    let sp = special_zone_val;

    base * crit * db * dr * amp * wk * sh * fr * vu * dff * imb * res * ncr * combo_bonus * sp
}

/// 批量评估主入口。
pub fn evaluate_batch(input: &BatchInput<'_>) -> Vec<f64> {
    let n = input.final_attacks.len();
    debug_assert_eq!(input.skill_multipliers.len(), n, "skill_multipliers length mismatch");
    debug_assert_eq!(input.skill_type_ids.len(), n, "skill_type_ids length mismatch");
    debug_assert_eq!(input.is_true_damages.len(), n, "is_true_damages length mismatch");
    debug_assert_eq!(input.is_unbalanceds.len(), n, "is_unbalanceds length mismatch");
    debug_assert_eq!(input.enemy_defenses.len(), n, "enemy_defenses length mismatch");
    debug_assert_eq!(input.enemy_resistances.len(), n, "enemy_resistances length mismatch");
    debug_assert_eq!(input.ignore_resistances.len(), n, "ignore_resistances length mismatch");
    debug_assert_eq!(input.imbalance_vulnerability_coeffs.len(), n, "imbalance_vulnerability_coeffs length mismatch");
    debug_assert_eq!(input.crit_rates.len(), n, "crit_rates length mismatch");
    debug_assert_eq!(input.crit_damages.len(), n, "crit_damages length mismatch");
    debug_assert_eq!(input.damage_type_bonuses.len(), n, "damage_type_bonuses length mismatch");
    debug_assert_eq!(input.skill_type_bonuses.len(), n, "skill_type_bonuses length mismatch");
    debug_assert_eq!(input.imbalance_damage_bonuses.len(), n, "imbalance_damage_bonuses length mismatch");
    debug_assert_eq!(input.other_damage_bonuses.len(), n, "other_damage_bonuses length mismatch");
    debug_assert_eq!(input.combo_stacks_list.len(), n, "combo_stacks_list length mismatch");
    debug_assert_eq!(input.break_defense_stacks_list.len(), n, "break_defense_stacks_list length mismatch");
    debug_assert_eq!(input.base_damage_bonuses.len(), n, "base_damage_bonuses length mismatch");
    debug_assert_eq!(input.effect_ids_batch.len(), n, "effect_ids_batch length mismatch");
    debug_assert_eq!(input.effect_values_batch.len(), n, "effect_values_batch length mismatch");
    debug_assert_eq!(input.crit_mode_ids.len(), n, "crit_mode_ids length mismatch");
    debug_assert_eq!(input.damage_pipelines.len(), n, "damage_pipelines length mismatch");
    let mut results = Vec::with_capacity(n);

    for i in 0..n {
        let damage = eval_single(
            input.final_attacks[i],
            input.skill_multipliers[i],
            input.skill_type_ids[i],
            input.is_true_damages[i],
            input.is_unbalanceds[i],
            input.enemy_defenses[i],
            input.enemy_resistances[i],
            input.ignore_resistances[i],
            input.imbalance_vulnerability_coeffs[i],
            input.crit_rates[i],
            input.crit_damages[i],
            input.damage_type_bonuses[i],
            input.skill_type_bonuses[i],
            input.imbalance_damage_bonuses[i],
            input.other_damage_bonuses[i],
            input.combo_stacks_list[i],
            input.break_defense_stacks_list[i],
            input.base_damage_bonuses[i],
            &input.effect_ids_batch[i],
            &input.effect_values_batch[i],
            input.crit_mode_ids[i],
            input.damage_pipelines[i],
        );
        results.push(damage);
    }
    results
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_batch_basic() {
        let n = 1;
        let fa = [1000.0];
        let sm = [2.0];
        let st = [SKILL_TYPE_NORMAL];
        let td = [false];
        let ub = [false];
        let ed = [100.0];
        let er = [0.0];
        let ir = [0.0];
        let ivc = [1.3];
        let cr = [0.05];
        let cd = [0.5];
        let dtb = [0.0];
        let stb = [0.0];
        let idb = [0.0];
        let odb = [0.0];
        let cs = [0_i32];
        let bds = [0_i32];
        let bdb = [0.0];
        let ids = vec![vec![]];
        let vals = vec![vec![]];
        let cm = [CRIT_MODE_NON_CRIT];
        let dp = [false];
        let input = BatchInput {
            final_attacks: &fa,
            skill_multipliers: &sm,
            skill_type_ids: &st,
            is_true_damages: &td,
            is_unbalanceds: &ub,
            enemy_defenses: &ed,
            enemy_resistances: &er,
            ignore_resistances: &ir,
            imbalance_vulnerability_coeffs: &ivc,
            crit_rates: &cr,
            crit_damages: &cd,
            damage_type_bonuses: &dtb,
            skill_type_bonuses: &stb,
            imbalance_damage_bonuses: &idb,
            other_damage_bonuses: &odb,
            combo_stacks_list: &cs,
            break_defense_stacks_list: &bds,
            base_damage_bonuses: &bdb,
            effect_ids_batch: &ids,
            effect_values_batch: &vals,
            crit_mode_ids: &cm,
            damage_pipelines: &dp,
        };
        let results = evaluate_batch(&input);
        assert_eq!(results.len(), 1);
        assert!((results[0] - 1000.0).abs() < 1e-9);
    }

    #[test]
    fn test_batch_with_effects() {
        let ids = vec![vec![EFFECT_DAMAGE_BONUS]];
        let vals = vec![vec![0.5]];
        let fa = [1000.0];
        let sm = [2.0];
        let input = BatchInput {
            final_attacks: &fa,
            skill_multipliers: &sm,
            skill_type_ids: &[SKILL_TYPE_NORMAL],
            is_true_damages: &[false],
            is_unbalanceds: &[false],
            enemy_defenses: &[100.0],
            enemy_resistances: &[0.0],
            ignore_resistances: &[0.0],
            imbalance_vulnerability_coeffs: &[1.3],
            crit_rates: &[0.05],
            crit_damages: &[0.5],
            damage_type_bonuses: &[0.0],
            skill_type_bonuses: &[0.0],
            imbalance_damage_bonuses: &[0.0],
            other_damage_bonuses: &[0.0],
            combo_stacks_list: &[0],
            break_defense_stacks_list: &[0],
            base_damage_bonuses: &[0.0],
            effect_ids_batch: &ids,
            effect_values_batch: &vals,
            crit_mode_ids: &[CRIT_MODE_NON_CRIT],
            damage_pipelines: &[false],
        };
        let results = evaluate_batch(&input);
        assert!((results[0] - 1500.0).abs() < 1e-9);
    }

    /// 辅助宏：从 tuple 构造 BatchInput（避免临时值生命周期问题）
    macro_rules! batch_input {
        ($t:expr) => {
            BatchInput {
                final_attacks: $t.0,
                skill_multipliers: $t.1,
                skill_type_ids: $t.2,
                is_true_damages: $t.3,
                is_unbalanceds: $t.4,
                enemy_defenses: $t.5,
                enemy_resistances: $t.6,
                ignore_resistances: $t.7,
                imbalance_vulnerability_coeffs: $t.8,
                crit_rates: $t.9,
                crit_damages: $t.10,
                damage_type_bonuses: $t.11,
                skill_type_bonuses: $t.12,
                imbalance_damage_bonuses: $t.13,
                other_damage_bonuses: $t.14,
                combo_stacks_list: $t.15,
                break_defense_stacks_list: $t.16,
                base_damage_bonuses: $t.17,
                effect_ids_batch: $t.18,
                effect_values_batch: $t.19,
                crit_mode_ids: $t.20,
                damage_pipelines: $t.21,
            }
        };
    }

    #[test]
    fn test_combo_stacks() {
        let ids = vec![vec![]];
        let vals = vec![vec![]];
        let data = (
            &[1000.0_f64][..], &[2.0_f64][..], &[SKILL_TYPE_NORMAL][..],
            &[false][..], &[false][..], &[0.0_f64][..],  // enemy_defense=0 → 防御乘数=1.0
            &[0.0_f64][..], &[0.0_f64][..], &[1.3_f64][..],
            &[0.05_f64][..], &[0.5_f64][..], &[0.0_f64][..],
            &[0.0_f64][..], &[0.0_f64][..], &[0.0_f64][..],
            &[2_i32][..], &[0_i32][..], &[0.0_f64][..],
            &ids[..], &vals[..], &[CRIT_MODE_NON_CRIT][..], &[false][..],
        );
        let r = evaluate_batch(&batch_input!(data));
        // 2000 * (1 + 0.45) = 2900
        assert!((r[0] - 2900.0).abs() < 1e-9);
    }

    #[test]
    fn test_combo_stacks_ultimate() {
        let ids = vec![vec![]];
        let vals = vec![vec![]];
        let data = (
            &[1000.0_f64][..], &[2.0_f64][..], &[SKILL_TYPE_ULTIMATE][..],
            &[false][..], &[false][..], &[0.0_f64][..],
            &[0.0_f64][..], &[0.0_f64][..], &[1.3_f64][..],
            &[0.05_f64][..], &[0.5_f64][..], &[0.0_f64][..],
            &[0.0_f64][..], &[0.0_f64][..], &[0.0_f64][..],
            &[3_i32][..], &[0_i32][..], &[0.0_f64][..],
            &ids[..], &vals[..], &[CRIT_MODE_NON_CRIT][..], &[false][..],
        );
        let r = evaluate_batch(&batch_input!(data));
        // 2000 * (1 + 0.40) = 2800
        assert!((r[0] - 2800.0).abs() < 1e-9);
    }

    #[test]
    fn test_break_defense_via_effects() {
        let ids = vec![vec![EFFECT_VULNERABILITY]];
        let vals = vec![vec![0.24]]; // 3 层 × 0.08
        let data = (
            &[1000.0_f64][..], &[1.0_f64][..], &[SKILL_TYPE_NORMAL][..],
            &[false][..], &[false][..], &[0.0_f64][..],
            &[0.0_f64][..], &[0.0_f64][..], &[1.3_f64][..],
            &[0.05_f64][..], &[0.5_f64][..], &[0.0_f64][..],
            &[0.0_f64][..], &[0.0_f64][..], &[0.0_f64][..],
            &[0_i32][..], &[0_i32][..], &[0.0_f64][..],
            &ids[..], &vals[..], &[CRIT_MODE_NON_CRIT][..], &[false][..],
        );
        let r = evaluate_batch(&batch_input!(data));
        // 1000 * (1 + 0.24) = 1240
        assert!((r[0] - 1240.0).abs() < 1e-9);
    }

    #[test]
    fn test_abnormal_pipeline_skips_combo() {
        let ids = vec![vec![]];
        let vals = vec![vec![]];
        let data = (
            &[1000.0_f64][..], &[2.0_f64][..], &[SKILL_TYPE_NORMAL][..],
            &[false][..], &[false][..], &[0.0_f64][..],
            &[0.0_f64][..], &[0.0_f64][..], &[1.3_f64][..],
            &[0.05_f64][..], &[0.5_f64][..], &[0.0_f64][..],
            &[0.0_f64][..], &[0.0_f64][..], &[0.0_f64][..],
            &[4_i32][..], &[0_i32][..], &[0.0_f64][..],
            &ids[..], &vals[..], &[CRIT_MODE_NON_CRIT][..], &[true][..],
        );
        let r = evaluate_batch(&batch_input!(data));
        // abnormal 跳过连击增伤：2000 * 1.0 = 2000
        assert!((r[0] - 2000.0).abs() < 1e-9);
    }

    #[test]
    fn test_true_damage_skips_defense() {
        let ids = vec![vec![]];
        let vals = vec![vec![]];
        let data = (
            &[1000.0_f64][..], &[2.0_f64][..], &[SKILL_TYPE_NORMAL][..],
            &[true][..], &[false][..], &[9999.0_f64][..],
            &[0.0_f64][..], &[0.0_f64][..], &[1.3_f64][..],
            &[0.05_f64][..], &[0.5_f64][..], &[0.0_f64][..],
            &[0.0_f64][..], &[0.0_f64][..], &[0.0_f64][..],
            &[0_i32][..], &[0_i32][..], &[0.0_f64][..],
            &ids[..], &vals[..], &[CRIT_MODE_NON_CRIT][..], &[false][..],
        );
        let r = evaluate_batch(&batch_input!(data));
        // 真伤忽略防御：2000
        assert!((r[0] - 2000.0).abs() < 1e-9);
    }

    #[test]
    fn test_multi_effect_combination() {
        let ids = vec![vec![
            EFFECT_DAMAGE_BONUS,
            EFFECT_VULNERABILITY,
            EFFECT_DAMAGE_REDUCTION,
        ]];
        let vals = vec![vec![0.5, 0.2, 0.3]];
        let data = (
            &[1000.0_f64][..], &[2.0_f64][..], &[SKILL_TYPE_NORMAL][..],
            &[false][..], &[false][..], &[200.0_f64][..],
            &[0.0_f64][..], &[0.0_f64][..], &[1.3_f64][..],
            &[0.05_f64][..], &[0.5_f64][..], &[0.0_f64][..],
            &[0.0_f64][..], &[0.0_f64][..], &[0.0_f64][..],
            &[0_i32][..], &[0_i32][..], &[0.0_f64][..],
            &ids[..], &vals[..], &[CRIT_MODE_NON_CRIT][..], &[false][..],
        );
        let r = evaluate_batch(&batch_input!(data));
        let expected = 2000.0 * 1.5 * 1.2 * 0.7 * (100.0 / 300.0);
        assert!((r[0] - expected).abs() < 1e-6);
    }

    #[test]
    fn test_batch_heterogeneous() {
        let ids = vec![
            vec![],
            vec![EFFECT_DAMAGE_BONUS],
            vec![EFFECT_VULNERABILITY],
        ];
        let vals = vec![vec![], vec![0.5], vec![0.2]];
        let data = (
            &[1000.0_f64, 1000.0, 1000.0][..],
            &[2.0_f64, 2.0, 2.0][..],
            &[SKILL_TYPE_NORMAL, SKILL_TYPE_NORMAL, SKILL_TYPE_NORMAL][..],
            &[false, false, false][..],
            &[false, false, false][..],
            &[0.0_f64, 0.0, 0.0][..],  // enemy_defense=0
            &[0.0_f64, 0.0, 0.0][..],
            &[0.0_f64, 0.0, 0.0][..],
            &[1.3_f64, 1.3, 1.3][..],
            &[0.05_f64, 0.05, 0.05][..],
            &[0.5_f64, 0.5, 0.5][..],
            &[0.0_f64, 0.0, 0.0][..],
            &[0.0_f64, 0.0, 0.0][..],
            &[0.0_f64, 0.0, 0.0][..],
            &[0.0_f64, 0.0, 0.0][..],
            &[0_i32, 0, 0][..],
            &[0_i32, 0, 0][..],
            &[0.0_f64, 0.0, 0.0][..],
            &ids[..],
            &vals[..],
            &[CRIT_MODE_NON_CRIT, CRIT_MODE_NON_CRIT, CRIT_MODE_NON_CRIT][..],
            &[false, false, false][..],
        );
        let r = evaluate_batch(&batch_input!(data));
        assert_eq!(r.len(), 3);
        // 任务 0: 2000 * 1.0 = 2000
        assert!((r[0] - 2000.0).abs() < 1e-9);
        // 任务 1: 2000 * 1.5 = 3000
        assert!((r[1] - 3000.0).abs() < 1e-9);
        // 任务 2: 2000 * 1.2 = 2400
        assert!((r[2] - 2400.0).abs() < 1e-9);
    }
}
