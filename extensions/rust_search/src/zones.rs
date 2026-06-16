// SPDX-License-Identifier: AGPL-3.0
//! 终末地 15 乘区伤害公式 — Rust 原生实现。
//!
//! 与 `framework/adapters/endfield/functions.py` 中的同名函数保持计算一致。
//! 纯 Rust 函数，无 PyO3 依赖，可直接单元测试。

/// 基础伤害区：最终攻击力 × 技能倍率 + 基础伤害提升。
pub fn base_damage_zone(final_attack: f64, skill_multiplier: f64, base_damage_bonus: f64) -> f64 {
    final_attack * skill_multiplier + base_damage_bonus
}

/// 暴击区。
///
/// - `non_crit`: 不暴击，返回 1.0
/// - `always_crit`: 必定暴击，返回 1.0 + crit_damage
/// - `expected`: 期望值，返回 1.0 + crit_rate * crit_damage
pub fn crit_zone(crit_rate: f64, crit_damage: f64, crit_mode: &str) -> f64 {
    match crit_mode {
        "always_crit" => 1.0 + crit_damage,
        "expected" => 1.0 + crit_rate * crit_damage,
        _ => 1.0, // non_crit 及其他未知模式均视为不暴击
    }
}

/// 伤害减免区：1.0 - damage_reduction。
pub fn damage_reduction_zone(damage_reduction: f64) -> f64 {
    1.0 - damage_reduction
}

/// 增幅区：1.0 + amplification。
pub fn amplification_zone(amplification: f64) -> f64 {
    1.0 + amplification
}

/// 虚弱区：1.0 - weakness。
pub fn weakness_zone(weakness: f64) -> f64 {
    1.0 - weakness
}

/// 庇护区：1.0 - shelter（调用方已取 max）。
pub fn shelter_zone(shelter: f64) -> f64 {
    1.0 - shelter
}

/// 脆弱区：1.0 + fragile。
pub fn fragile_zone(fragile: f64) -> f64 {
    1.0 + fragile
}

/// 易伤区：1.0 + vulnerability。
pub fn vulnerability_zone(vulnerability: f64) -> f64 {
    1.0 + vulnerability
}

/// 防御区。
///
/// 真伤时返回 1.0，否则按 `100 / (100 + effective_def)` 计算。
pub fn defense_zone(enemy_defense: f64, defense_change: f64, is_true_damage: bool) -> f64 {
    if is_true_damage {
        return 1.0;
    }
    let effective = (enemy_defense + defense_change).max(0.0);
    100.0 / (effective + 100.0)
}

/// 失衡易伤区：失衡时返回 imbalance_coeff，否则 1.0。
pub fn imbalance_zone(imbalance_coeff: f64, is_unbalanced: bool) -> f64 {
    if is_unbalanced {
        imbalance_coeff
    } else {
        1.0
    }
}

/// 抗性区：1.0 - enemy_resistance / 100.0 + ignore_resistance / 100.0。
pub fn resistance_zone(enemy_resistance: f64, ignore_resistance: f64) -> f64 {
    1.0 - enemy_resistance / 100.0 + ignore_resistance / 100.0
}

/// 非主控减伤区：1.0 - non_control_reduction。
pub fn non_control_reduction_zone(non_control_reduction: f64) -> f64 {
    1.0 - non_control_reduction
}

/// 连击增伤区：1.0 + combo_bonus。
pub fn combo_bonus_zone(combo_bonus: f64) -> f64 {
    1.0 + combo_bonus
}

/// 特殊乘区：连乘值。
pub fn special_zone(special: f64) -> f64 {
    special
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_base_damage_zone() {
        let r = base_damage_zone(1000.0, 2.0, 0.0);
        assert!((r - 2000.0).abs() < 1e-9);

        let r = base_damage_zone(1000.0, 2.0, 50.0);
        assert!((r - 2050.0).abs() < 1e-9);
    }

    #[test]
    fn test_crit_zone_non_crit() {
        let r = crit_zone(0.5, 0.8, "non_crit");
        assert!((r - 1.0).abs() < 1e-9);
    }

    #[test]
    fn test_crit_zone_always_crit() {
        let r = crit_zone(0.5, 0.8, "always_crit");
        assert!((r - 1.8).abs() < 1e-9);
    }

    #[test]
    fn test_crit_zone_expected() {
        let r = crit_zone(0.5, 0.8, "expected");
        assert!((r - 1.4).abs() < 1e-9);
    }

    #[test]
    fn test_defense_zone_normal() {
        let r = defense_zone(200.0, 0.0, false);
        assert!((r - 100.0 / 300.0).abs() < 1e-9);
    }

    #[test]
    fn test_defense_zone_true_damage() {
        let r = defense_zone(200.0, 0.0, true);
        assert!((r - 1.0).abs() < 1e-9);
    }

    #[test]
    fn test_defense_zone_negative_effective() {
        let r = defense_zone(50.0, -100.0, false);
        assert!((r - 1.0).abs() < 1e-9); // effective = max(0, -50) = 0 → 100/100 = 1.0
    }

    #[test]
    fn test_imbalance_zone_unbalanced() {
        let r = imbalance_zone(1.5, true);
        assert!((r - 1.5).abs() < 1e-9);
    }

    #[test]
    fn test_imbalance_zone_not_unbalanced() {
        let r = imbalance_zone(1.5, false);
        assert!((r - 1.0).abs() < 1e-9);
    }

    #[test]
    fn test_resistance_zone() {
        let r = resistance_zone(50.0, 10.0);
        assert!((r - (1.0 - 0.5 + 0.1)).abs() < 1e-9);
    }

    #[test]
    fn test_all_zones_multiplicative() {
        // 所有区都是 1.0 时，结果应为 1.0
        let r = base_damage_zone(1.0, 1.0, 0.0)
            * crit_zone(0.0, 0.0, "non_crit")
            * (1.0 + 0.0) // damage_bonus
            * damage_reduction_zone(0.0)
            * amplification_zone(0.0)
            * weakness_zone(0.0)
            * shelter_zone(0.0)
            * fragile_zone(0.0)
            * vulnerability_zone(0.0)
            * defense_zone(0.0, 0.0, true)
            * imbalance_zone(1.0, false)
            * resistance_zone(0.0, 0.0)
            * non_control_reduction_zone(0.0)
            * combo_bonus_zone(0.0)
            * special_zone(1.0);
        assert!((r - 1.0).abs() < 1e-9);
    }
}
