// SPDX-License-Identifier: AGPL-3.0
//! 效果类型 → 整数 ID 映射（消除字符串匹配开销）。
//!
//! Python 侧一次性将效果类型字符串映射为 u8，Rust 侧用整数 match。

/// 伤害减免
pub const EFFECT_DAMAGE_REDUCTION: u8 = 0;
/// 增幅
pub const EFFECT_AMPLIFICATION: u8 = 1;
/// 虚弱
pub const EFFECT_WEAKNESS: u8 = 2;
/// 庇护
pub const EFFECT_SHELTER: u8 = 3;
/// 脆弱
pub const EFFECT_FRAGILE: u8 = 4;
/// 易伤
pub const EFFECT_VULNERABILITY: u8 = 5;
/// 连击增伤
pub const EFFECT_COMBO_BONUS: u8 = 6;
/// 伤害类型/技能类型/失衡/其他伤害加成
pub const EFFECT_DAMAGE_BONUS: u8 = 7;
/// 无视抗性
pub const EFFECT_IGNORE_RESISTANCE: u8 = 8;
/// 抗性变化
pub const EFFECT_RESISTANCE: u8 = 9;
/// 防御变化
pub const EFFECT_DEFENSE: u8 = 10;
/// 失衡易伤系数
pub const EFFECT_IMBALANCE_COEFF: u8 = 11;
/// 非主控减伤
pub const EFFECT_NON_CONTROL_REDUCTION: u8 = 12;
/// 特殊乘区
pub const EFFECT_SPECIAL_ZONE: u8 = 13;

/// 效果类型字符串 → 整数 ID。未知类型返回 None。（PyO3 导出，Rust 内部未使用）
#[allow(dead_code)]
pub fn effect_type_to_id(name: &str) -> Option<u8> {
    match name {
        "伤害减免" => Some(EFFECT_DAMAGE_REDUCTION),
        "增幅" => Some(EFFECT_AMPLIFICATION),
        "虚弱" => Some(EFFECT_WEAKNESS),
        "庇护" => Some(EFFECT_SHELTER),
        "脆弱" => Some(EFFECT_FRAGILE),
        "易伤" => Some(EFFECT_VULNERABILITY),
        "连击增伤" => Some(EFFECT_COMBO_BONUS),
        "伤害类型伤害加成" | "技能类型伤害加成" | "失衡伤害加成" | "其他伤害加成" => {
            Some(EFFECT_DAMAGE_BONUS)
        }
        "无视抗性" => Some(EFFECT_IGNORE_RESISTANCE),
        "抗性" => Some(EFFECT_RESISTANCE),
        "防御" => Some(EFFECT_DEFENSE),
        "失衡易伤系数" => Some(EFFECT_IMBALANCE_COEFF),
        "非主控减伤" => Some(EFFECT_NON_CONTROL_REDUCTION),
        "特殊乘区" => Some(EFFECT_SPECIAL_ZONE),
        _ => None,
    }
}

/// 技能类型字符串 → 整数 ID。（PyO3 导出，Rust 内部未使用）
#[allow(dead_code)]
pub const SKILL_TYPE_NORMAL: u8 = 0;
pub const SKILL_TYPE_ULTIMATE: u8 = 1;

#[allow(dead_code)]
pub fn skill_type_to_id(name: &str) -> u8 {
    match name {
        "终结技" => SKILL_TYPE_ULTIMATE,
        _ => SKILL_TYPE_NORMAL,
    }
}

/// 暴击模式字符串 → 整数 ID。（PyO3 导出，Rust 内部未使用）
#[allow(dead_code)]
pub const CRIT_MODE_NON_CRIT: u8 = 0;
pub const CRIT_MODE_ALWAYS_CRIT: u8 = 1;
pub const CRIT_MODE_EXPECTED: u8 = 2;

#[allow(dead_code)]
pub fn crit_mode_to_id(name: &str) -> u8 {
    match name {
        "always_crit" => CRIT_MODE_ALWAYS_CRIT,
        "expected" => CRIT_MODE_EXPECTED,
        _ => CRIT_MODE_NON_CRIT,
    }
}
