// SPDX-License-Identifier: AGPL-3.0
//! 全批量评估引擎 — Python 预处理 → Rust 完整评估 → 返回结果。
//!
//! 消除 Python 逐任务开销，实现 ~5 秒完成 97 万组合遍历。
//!
//! 评估逻辑与 `evaluate.rs` / `batch_eval.rs` 完全一致：
//! - 效果累加：14 种效果类型 + 失衡易伤系数覆盖
//! - 暴击模式：non_crit / always_crit / expected
//! - 连击增伤：按技能类型查表（战技/终结技）
//! - 异常管线：abnormal 跳过连击增伤和非主控减伤

use crate::zones;

/// 连击增伤层数表（与 Python combo_bonus.py 一致）
const COMBO_STACKS_SKILL: [f64; 4] = [0.30, 0.45, 0.60, 0.75];
const COMBO_STACKS_ULTIMATE: [f64; 4] = [0.20, 0.30, 0.40, 0.50];

/// 武器数据
#[derive(Clone, Debug)]
pub struct WeaponData {
    pub name: String,
    pub final_attack: f64,
    pub effects: Vec<(String, f64)>,
}

/// 装备组合
#[derive(Clone, Debug)]
pub struct EquipmentCombo {
    pub chest_name: String,
    pub gloves_name: String,
    pub acc_a_name: String,
    pub acc_b_name: String,
    pub effects: Vec<(String, f64)>,
    pub flat_stats: std::collections::HashMap<String, f64>,
    pub atk_percent: f64,
}

/// 角色数据
#[derive(Clone, Debug)]
pub struct CharData {
    pub name: String,
    pub level: i32,
    pub base_attack: f64,
    pub base_hp: f64,
    pub base_defense: f64,
}

/// 计算参数
#[derive(Clone, Debug)]
pub struct CalcParams {
    pub skill_multiplier: f64,
    pub damage_type: String,
    pub skill_type: String,
    pub is_unbalanced: bool,
    pub is_true_damage: bool,
    pub enemy_defense: f64,
    pub enemy_resistance: f64,
    pub ignore_resistance: f64,
    pub imbalance_vulnerability_coeff: f64,
    pub crit_rate: f64,
    pub crit_damage: f64,
    pub damage_type_bonus: f64,
    pub skill_type_bonus: f64,
    pub imbalance_damage_bonus: f64,
    pub other_damage_bonus: f64,
    pub combo_stacks: i32,
    pub break_defense_stacks: i32,
    pub base_damage_bonus: f64,
    /// 暴击模式："non_crit" / "always_crit" / "expected"
    pub crit_mode: String,
    /// 伤害管线："normal" / "abnormal"
    pub damage_pipeline: String,
}

/// 配装结果
#[derive(Clone, Debug)]
pub struct LoadoutResult {
    pub weapon_name: String,
    pub final_damage: f64,
    pub loadout_names: std::collections::HashMap<String, String>,
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

/// 计算最终攻击力
fn calculate_final_attack(
    char_data: &CharData,
    weapon: &WeaponData,
    equipment: &EquipmentCombo,
) -> f64 {
    // 基础攻击力 = 角色基础 + 武器基础
    let base_attack = char_data.base_attack + weapon.final_attack;

    // 装备平铺攻击
    let equip_flat = equipment.flat_stats.get("攻击力").copied().unwrap_or(0.0);

    // 攻击力百分比加成
    let atk_percent = equipment.atk_percent;

    // 最终攻击力 = (基础攻击 + 装备平铺) * (1 + 攻击力%)
    (base_attack + equip_flat) * (1.0 + atk_percent)
}

/// 合并效果列表
fn merge_effects(
    weapon_effects: &[(String, f64)],
    equipment_effects: &[(String, f64)],
) -> Vec<(String, f64)> {
    let mut result = Vec::with_capacity(weapon_effects.len() + equipment_effects.len());
    result.extend_from_slice(weapon_effects);
    result.extend_from_slice(equipment_effects);
    result
}

/// 评估单个配装的伤害。
///
/// 逻辑与 `evaluate.rs::evaluate_search_damage` 完全一致。
fn evaluate_single(
    final_attack: f64,
    effects: &[(String, f64)],
    params: &CalcParams,
) -> f64 {
    // ---- 1. 初始化累加器 ----
    let mut dmg_bonus = 1.0
        + params.damage_type_bonus
        + params.skill_type_bonus
        + params.imbalance_damage_bonus
        + params.other_damage_bonus;
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

    // ---- 2. 效果累加循环（与 evaluate.rs 一致） ----
    for (effect_type, value) in effects {
        match effect_type.as_str() {
            "伤害减免" => dmg_reduction *= 1.0 - value,
            "增幅" => amplification += value,
            "虚弱" => weakness *= 1.0 - value,
            "庇护" => {
                if *value > shelter_max {
                    shelter_max = *value;
                }
            }
            "脆弱" => fragile += value,
            "易伤" => vulnerability += value,
            "连击增伤" => combo_bonus_flat += value,
            "伤害类型伤害加成" | "技能类型伤害加成" | "失衡伤害加成" | "其他伤害加成" => {
                dmg_bonus += value;
            }
            "无视抗性" => resistance_extra += value,
            "抗性" => resistance_change += value,
            "防御" => defense_change += value,
            "失衡易伤系数" => {
                imbalance_coeff_override = Some(*value);
            }
            "非主控减伤" => non_control_reduction *= 1.0 - value,
            "特殊乘区" => special_zone_val *= value,
            _ => { /* 未知效果类型，Python 侧已过滤 */ }
        }
    }

    // ---- 3. 庇护取 max ----
    let shelter = 1.0 - shelter_max;

    // ---- 4. 连击增伤（abnormal pipeline 跳过） ----
    let is_abnormal = params.damage_pipeline == "abnormal";
    let combo_bonus = if is_abnormal {
        1.0
    } else {
        combo_zone_multiplier(&params.skill_type, params.combo_stacks, combo_bonus_flat.max(0.0))
    };

    // ---- 5. 非主控减伤（abnormal pipeline 跳过） ----
    let ncr = if is_abnormal {
        1.0
    } else {
        non_control_reduction
    };

    // ---- 6. 失衡易伤系数 ----
    let imb_coeff = imbalance_coeff_override.unwrap_or(params.imbalance_vulnerability_coeff);

    // ---- 7. 抗性 ----
    let total_resistance = params.enemy_resistance + resistance_change;
    let total_ignore = params.ignore_resistance + resistance_extra;

    // ---- 8. 防御区变化 ----
    let effective_def = (params.enemy_defense + defense_change).max(0.0);

    // ---- 9. 调用各乘区函数（与 evaluate.rs 一致） ----
    let base = zones::base_damage_zone(final_attack, params.skill_multiplier, params.base_damage_bonus);
    let crit = zones::crit_zone(params.crit_rate, params.crit_damage, &params.crit_mode);
    let db = dmg_bonus;
    let dr = dmg_reduction;
    let amp = amplification;
    let wk = weakness;
    let sh = shelter;
    let fr = fragile;
    let vu = vulnerability;
    let dff = if params.is_true_damage {
        1.0
    } else {
        100.0 / (effective_def + 100.0)
    };
    let imb = if params.is_unbalanced { imb_coeff } else { 1.0 };
    let res = 1.0 - total_resistance / 100.0 + total_ignore / 100.0;
    let sp = special_zone_val;

    // ---- 10. 15 乘区连乘 ----
    base * crit * db * dr * amp * wk * sh * fr * vu * dff * imb * res * ncr * combo_bonus * sp
}

/// 全批量评估主入口。
///
/// ``precomputed_final_attacks`` 若提供且长度为 ``weapons.len() * equipment_combos.len()``，
/// 则按行优先（武器外层、装备内层）直接使用，跳过简化版 ``calculate_final_attack``。
/// 这与 Python ``final_attack_details_for_loadout`` 对齐，避免双计角色基础攻。
pub fn evaluate_full_batch(
    weapons: &[WeaponData],
    equipment_combos: &[EquipmentCombo],
    char_data: &CharData,
    params: &CalcParams,
    top_n: usize,
    precomputed_final_attacks: Option<&[f64]>,
) -> Vec<LoadoutResult> {
    let mut results = Vec::new();
    let n_equip = equipment_combos.len();
    let use_precomputed = match precomputed_final_attacks {
        Some(arr) => arr.len() == weapons.len() * n_equip && n_equip > 0,
        None => false,
    };

    for (wi, weapon) in weapons.iter().enumerate() {
        for (ei, equipment) in equipment_combos.iter().enumerate() {
            // 1. 最终攻击力：优先预计算（与 SoA/search_eval 同 seam）
            let final_attack = if use_precomputed {
                precomputed_final_attacks.unwrap()[wi * n_equip + ei]
            } else {
                calculate_final_attack(char_data, weapon, equipment)
            };

            // 2. 合并效果列表
            let effects = merge_effects(&weapon.effects, &equipment.effects);

            // 3. 计算伤害（使用完整评估逻辑）
            let damage = evaluate_single(final_attack, &effects, params);

            // 4. 构建配装名称
            let mut loadout_names = std::collections::HashMap::new();
            loadout_names.insert("chest".to_string(), equipment.chest_name.clone());
            loadout_names.insert("gloves".to_string(), equipment.gloves_name.clone());
            loadout_names.insert("accessory_a".to_string(), equipment.acc_a_name.clone());
            loadout_names.insert("accessory_b".to_string(), equipment.acc_b_name.clone());

            results.push(LoadoutResult {
                weapon_name: weapon.name.clone(),
                final_damage: damage,
                loadout_names,
            });
        }
    }

    // 5. 排序返回 TopN
    results.sort_by(|a, b| b.final_damage.partial_cmp(&a.final_damage).unwrap());
    results.truncate(top_n);
    results
}

#[cfg(test)]
mod tests {
    use super::*;

    /// 辅助：构造默认 CalcParams
    fn default_params() -> CalcParams {
        CalcParams {
            skill_multiplier: 2.0,
            damage_type: "物理".to_string(),
            skill_type: "战技".to_string(),
            is_unbalanced: false,
            is_true_damage: false,
            enemy_defense: 100.0,
            enemy_resistance: 0.0,
            ignore_resistance: 0.0,
            imbalance_vulnerability_coeff: 1.3,
            crit_rate: 0.05,
            crit_damage: 0.5,
            damage_type_bonus: 0.0,
            skill_type_bonus: 0.0,
            imbalance_damage_bonus: 0.0,
            other_damage_bonus: 0.0,
            combo_stacks: 0,
            break_defense_stacks: 0,
            base_damage_bonus: 0.0,
            crit_mode: "non_crit".to_string(),
            damage_pipeline: "normal".to_string(),
        }
    }

    fn default_char() -> CharData {
        CharData {
            name: "测试角色".to_string(),
            level: 90,
            base_attack: 500.0,
            base_hp: 10000.0,
            base_defense: 500.0,
        }
    }

    fn make_weapon(name: &str, final_attack: f64, effects: Vec<(String, f64)>) -> WeaponData {
        WeaponData {
            name: name.to_string(),
            final_attack,
            effects,
        }
    }

    fn make_equipment(
        chest: &str, gloves: &str, acc_a: &str, acc_b: &str,
        effects: Vec<(String, f64)>,
        flat_stats: std::collections::HashMap<String, f64>,
        atk_percent: f64,
    ) -> EquipmentCombo {
        EquipmentCombo {
            chest_name: chest.to_string(),
            gloves_name: gloves.to_string(),
            acc_a_name: acc_a.to_string(),
            acc_b_name: acc_b.to_string(),
            effects,
            flat_stats,
            atk_percent,
        }
    }

    #[test]
    fn test_basic_evaluation() {
        let weapon = make_weapon("测试武器", 500.0, vec![]);
        let equipment = make_equipment("胸甲", "手套", "饰品A", "饰品B", vec![], std::collections::HashMap::new(), 0.0);
        let params = default_params();

        let results = evaluate_full_batch(&[weapon], &[equipment], &default_char(), &params, 10, None);

        assert_eq!(results.len(), 1);
        // final_attack = (500 + 500) * (1 + 0) = 1000
        // base_damage = 1000 * 2.0 = 2000
        // crit = 1.0 (non_crit)
        // defense = 100 / (100 + 100) = 0.5
        // final = 2000 * 0.5 = 1000
        assert!((results[0].final_damage - 1000.0).abs() < 1e-6);
    }

    #[test]
    fn test_expected_crit_mode() {
        let weapon = make_weapon("测试武器", 500.0, vec![]);
        let equipment = make_equipment("胸甲", "手套", "饰品A", "饰品B", vec![], std::collections::HashMap::new(), 0.0);
        let mut params = default_params();
        params.crit_mode = "expected".to_string();
        params.crit_rate = 0.5;
        params.crit_damage = 0.8;

        let results = evaluate_full_batch(&[weapon], &[equipment], &default_char(), &params, 10, None);

        // crit = 1 + 0.5 * 0.8 = 1.4
        // final = 2000 * 1.4 * 0.5 = 1400
        assert!((results[0].final_damage - 1400.0).abs() < 1e-6);
    }

    #[test]
    fn test_always_crit_mode() {
        let weapon = make_weapon("测试武器", 500.0, vec![]);
        let equipment = make_equipment("胸甲", "手套", "饰品A", "饰品B", vec![], std::collections::HashMap::new(), 0.0);
        let mut params = default_params();
        params.crit_mode = "always_crit".to_string();
        params.crit_damage = 0.8;

        let results = evaluate_full_batch(&[weapon], &[equipment], &default_char(), &params, 10, None);

        // crit = 1 + 0.8 = 1.8
        // final = 2000 * 1.8 * 0.5 = 1800
        assert!((results[0].final_damage - 1800.0).abs() < 1e-6);
    }

    #[test]
    fn test_damage_bonus_effect() {
        let weapon = make_weapon("测试武器", 500.0, vec![]);
        let effects = vec![("伤害类型伤害加成".to_string(), 0.5)];
        let equipment = make_equipment("胸甲", "手套", "饰品A", "饰品B", effects, std::collections::HashMap::new(), 0.0);
        let params = default_params();

        let results = evaluate_full_batch(&[weapon], &[equipment], &default_char(), &params, 10, None);

        // dmg_bonus = 1.0 + 0.5 = 1.5
        // final = 2000 * 1.5 * 0.5 = 1500
        assert!((results[0].final_damage - 1500.0).abs() < 1e-6);
    }

    #[test]
    fn test_abnormal_pipeline_skips_combo() {
        let weapon = make_weapon("测试武器", 500.0, vec![]);
        let equipment = make_equipment("胸甲", "手套", "饰品A", "饰品B", vec![], std::collections::HashMap::new(), 0.0);
        let mut params = default_params();
        params.combo_stacks = 2;
        params.damage_pipeline = "abnormal".to_string();

        let results = evaluate_full_batch(&[weapon], &[equipment], &default_char(), &params, 10, None);

        // abnormal 跳过连击增伤：2000 * 1.0 * 0.5 = 1000
        assert!((results[0].final_damage - 1000.0).abs() < 1e-6);
    }

    #[test]
    fn test_combo_stacks() {
        let weapon = make_weapon("测试武器", 500.0, vec![]);
        let equipment = make_equipment("胸甲", "手套", "饰品A", "饰品B", vec![], std::collections::HashMap::new(), 0.0);
        let mut params = default_params();
        params.enemy_defense = 0.0; // 防御=1.0，简化验证
        params.combo_stacks = 2;

        let results = evaluate_full_batch(&[weapon], &[equipment], &default_char(), &params, 10, None);

        // combo_stacks=2, 战技: 1 + 0.45 = 1.45
        // final = 2000 * 1.45 = 2900
        assert!((results[0].final_damage - 2900.0).abs() < 1e-6);
    }

    #[test]
    fn test_true_damage_skips_defense() {
        let weapon = make_weapon("测试武器", 500.0, vec![]);
        let equipment = make_equipment("胸甲", "手套", "饰品A", "饰品B", vec![], std::collections::HashMap::new(), 0.0);
        let mut params = default_params();
        params.is_true_damage = true;
        params.enemy_defense = 9999.0;

        let results = evaluate_full_batch(&[weapon], &[equipment], &default_char(), &params, 10, None);

        // 真伤忽略防御：2000
        assert!((results[0].final_damage - 2000.0).abs() < 1e-6);
    }

    #[test]
    fn test_imbalance_override_effect() {
        let weapon = make_weapon("测试武器", 500.0, vec![]);
        let effects = vec![("失衡易伤系数".to_string(), 2.0)];
        let equipment = make_equipment("胸甲", "手套", "饰品A", "饰品B", effects, std::collections::HashMap::new(), 0.0);
        let mut params = default_params();
        params.enemy_defense = 0.0;
        params.is_unbalanced = true;

        let results = evaluate_full_batch(&[weapon], &[equipment], &default_char(), &params, 10, None);

        // 失衡易伤系数覆盖: 2000 * 2.0 = 4000
        assert!((results[0].final_damage - 4000.0).abs() < 1e-6);
    }

    #[test]
    fn test_topn_truncation() {
        let weapons = vec![
            make_weapon("武器A", 500.0, vec![]),
            make_weapon("武器B", 600.0, vec![]),
            make_weapon("武器C", 400.0, vec![]),
        ];
        let equipment = make_equipment("胸甲", "手套", "饰品A", "饰品B", vec![], std::collections::HashMap::new(), 0.0);
        let params = default_params();

        let results = evaluate_full_batch(&weapons, &[equipment], &default_char(), &params, 2, None);

        assert_eq!(results.len(), 2);
        // 武器B 最强 (600+500=1100), 武器A 次之 (500+500=1000), 武器C 最弱 (400+500=900)
        assert_eq!(results[0].weapon_name, "武器B");
        assert_eq!(results[1].weapon_name, "武器A");
    }
}
