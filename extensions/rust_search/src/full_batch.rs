// SPDX-License-Identifier: AGPL-3.0
//! 全批量评估引擎 — Python 预处理 → Rust 完整评估 → 返回结果。
//!
//! 消除 Python 逐任务开销，实现 ~5 秒完成 97 万组合遍历。

use crate::zones;

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
}

/// 配装结果
#[derive(Clone, Debug)]
pub struct LoadoutResult {
    pub weapon_name: String,
    pub final_damage: f64,
    pub loadout_names: std::collections::HashMap<String, String>,
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

/// 累加效果到乘区
fn accumulate_effects(
    effects: &[(String, f64)],
    params: &CalcParams,
) -> (f64, f64, f64, f64, f64, f64, f64, f64, f64, f64, f64, f64, f64) {
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
            "非主控减伤" => non_control_reduction *= 1.0 - value,
            "特殊乘区" => special_zone_val *= value,
            _ => {}
        }
    }

    let shelter = 1.0 - shelter_max;
    let combo_bonus = 1.0 + combo_bonus_flat.max(0.0);

    (
        dmg_bonus,
        dmg_reduction,
        amplification,
        weakness,
        shelter,
        fragile,
        vulnerability,
        combo_bonus,
        non_control_reduction,
        special_zone_val,
        resistance_extra,
        resistance_change,
        defense_change,
    )
}

/// 评估单个配装的伤害
fn evaluate_single(
    final_attack: f64,
    effects: &[(String, f64)],
    params: &CalcParams,
) -> f64 {
    let (
        dmg_bonus,
        dmg_reduction,
        amplification,
        weakness,
        shelter,
        fragile,
        vulnerability,
        combo_bonus,
        non_control_reduction,
        special_zone_val,
        resistance_extra,
        resistance_change,
        defense_change,
    ) = accumulate_effects(effects, params);

    // 基础伤害区
    let base = zones::base_damage_zone(final_attack, params.skill_multiplier, params.base_damage_bonus);

    // 暴击区（默认 non_crit）
    let crit = 1.0;

    // 失衡易伤区
    let imb = if params.is_unbalanced {
        params.imbalance_vulnerability_coeff
    } else {
        1.0
    };

    // 抗性区
    let total_resistance = params.enemy_resistance + resistance_change;
    let total_ignore = params.ignore_resistance + resistance_extra;
    let res = 1.0 - total_resistance / 100.0 + total_ignore / 100.0;

    // 防御区
    let dff = if params.is_true_damage {
        1.0
    } else {
        let effective_def = (params.enemy_defense + defense_change).max(0.0);
        100.0 / (effective_def + 100.0)
    };

    // 15 乘区连乘
    base * crit * dmg_bonus * dmg_reduction * amplification * weakness * shelter
        * fragile * vulnerability * dff * imb * res * non_control_reduction
        * combo_bonus * special_zone_val
}

/// 全批量评估主入口
pub fn evaluate_full_batch(
    weapons: &[WeaponData],
    equipment_combos: &[EquipmentCombo],
    char_data: &CharData,
    params: &CalcParams,
    top_n: usize,
) -> Vec<LoadoutResult> {
    let mut results = Vec::new();

    for weapon in weapons {
        for equipment in equipment_combos {
            // 1. 计算最终攻击力
            let final_attack = calculate_final_attack(char_data, weapon, equipment);

            // 2. 合并效果列表
            let effects = merge_effects(&weapon.effects, &equipment.effects);

            // 3. 计算伤害
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

    #[test]
    fn test_basic_evaluation() {
        let weapon = WeaponData {
            name: "测试武器".to_string(),
            final_attack: 500.0,
            effects: vec![],
        };

        let equipment = EquipmentCombo {
            chest_name: "胸甲".to_string(),
            gloves_name: "手套".to_string(),
            acc_a_name: "饰品A".to_string(),
            acc_b_name: "饰品B".to_string(),
            effects: vec![],
            flat_stats: std::collections::HashMap::new(),
            atk_percent: 0.0,
        };

        let char_data = CharData {
            name: "测试角色".to_string(),
            level: 90,
            base_attack: 500.0,
            base_hp: 10000.0,
            base_defense: 500.0,
        };

        let params = CalcParams {
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
        };

        let weapons = vec![weapon];
        let equipment_combos = vec![equipment];

        let results = evaluate_full_batch(&weapons, &equipment_combos, &char_data, &params, 10);

        assert_eq!(results.len(), 1);
        // final_attack = (500 + 500) * (1 + 0) = 1000
        // base_damage = 1000 * 2.0 = 2000
        // defense = 100 / (100 + 100) = 0.5
        // final = 2000 * 0.5 = 1000
        assert!((results[0].final_damage - 1000.0).abs() < 1e-6);
    }
}
