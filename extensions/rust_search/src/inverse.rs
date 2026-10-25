// SPDX-License-Identifier: AGPL-3.0
//! 公式反推引擎 — Rust 原生加速。
//!
//! 对应 `calc_framework/inverse/base.py::FloorFormulaFitter._search`。
//! 核心是 growth × divisor × offset 的三重嵌套循环。

/// 反推结果
#[derive(Debug, Clone)]
pub struct FitResult {
    pub growth: i64,
    pub divisor: i64,
    pub offset: i64,
    #[allow(dead_code)]
    pub scaled_base: i64,
    pub scale_factor: i64,
    pub max_error: f64,
    pub is_exact: bool,
}

/// 计算 floor 公式在各等级成立的 offset 区间。
fn offset_bounds(
    scaled_data: &[i64],
    scaled_base: i64,
    growth: i64,
    divisor: i64,
    num_levels: usize,
) -> (bool, i64, i64) {
    let mut offset_lower: i64 = i64::MIN / 2;
    let mut offset_upper: i64 = i64::MAX / 2;

    for lv in 1..=num_levels {
        let target = scaled_data[lv - 1] - scaled_base;
        // lower = target * divisor - growth * (lv - 1)
        let lower = target.saturating_mul(divisor).saturating_sub(growth * (lv as i64 - 1));
        // upper = (target + 1) * divisor - growth * (lv - 1) - 1
        let upper = (target + 1)
            .saturating_mul(divisor)
            .saturating_sub(growth * (lv as i64 - 1))
            .saturating_sub(1);

        offset_lower = offset_lower.max(ceil_div(lower, 1)); // lower is already integer
        offset_upper = offset_upper.min(floor_div(upper, 1));

        if offset_lower > offset_upper {
            return (false, 0, 0);
        }
    }
    (true, offset_lower, offset_upper)
}

fn ceil_div(a: i64, b: i64) -> i64 {
    if b == 0 {
        return a;
    }
    if a >= 0 {
        (a + b - 1) / b
    } else {
        a / b
    }
}

fn floor_div(a: i64, b: i64) -> i64 {
    if b == 0 {
        return a;
    }
    if a >= 0 {
        a / b
    } else {
        (a - b + 1) / b
    }
}

/// 计算 floor 公式各等级的值并求误差和。
fn compute_error(
    scaled_base: i64,
    growth: i64,
    divisor: i64,
    offset: i64,
    scaled_data: &[i64],
    num_levels: usize,
) -> f64 {
    let mut error = 0.0;
    for lv in 1..=num_levels {
        // floor((growth * (lv-1) + offset) / divisor)
        let numerator = growth * (lv as i64 - 1) + offset;
        let floor_val = if numerator >= 0 {
            numerator / divisor
        } else {
            (numerator - divisor + 1) / divisor
        };
        let computed = scaled_base + floor_val;
        error += (computed - scaled_data[lv - 1]).abs() as f64;
    }
    error
}

/// GCD 约分简化参数。
fn gcd_normalize(
    mut growth: i64,
    mut divisor: i64,
    offset: i64,
    scaled_data: &[i64],
    scaled_base: i64,
) -> (i64, i64, i64) {
    let num_levels = scaled_data.len();
    loop {
        let factor = gcd(growth.abs(), divisor.abs());
        if factor <= 1 {
            break;
        }
        let ng = growth / factor;
        let nd = divisor / factor;

        let mut all_match = true;
        for lv in 1..=num_levels {
            let numerator = ng * (lv as i64 - 1) + offset;
            let floor_val = if numerator >= 0 {
                numerator / nd
            } else {
                (numerator - nd + 1) / nd
            };
            if scaled_base + floor_val != scaled_data[lv - 1] {
                all_match = false;
                break;
            }
        }

        if all_match {
            growth = ng;
            divisor = nd;
        } else {
            break;
        }
    }
    (growth, divisor, offset)
}

fn gcd(a: i64, b: i64) -> i64 {
    let mut a = a.abs();
    let mut b = b.abs();
    while b != 0 {
        let t = b;
        b = a % b;
        a = t;
    }
    a
}

/// 核心反推搜索：先找精确解，再找近似最优解。
///
/// `divisor_range` / `growth_range` 为 (start, end)，Python `range(start, end)` 语义。
/// 返回 None 表示无解。
#[allow(clippy::too_many_arguments)]
pub fn fit_floor_formula(
    scaled_data: &[i64],
    scaled_base: i64,
    scale_factor: i64,
    divisor_start: i64,
    divisor_end: i64,
    growth_start: i64,
    growth_end: i64,
    offset_search_limit: i64,
) -> Option<FitResult> {
    let num_levels = scaled_data.len();

    // ── 精确解搜索 ──
    for growth in growth_start..growth_end {
        for divisor in divisor_start..divisor_end {
            let (valid, offset_lower, offset_upper) =
                offset_bounds(scaled_data, scaled_base, growth, divisor, num_levels);
            if !valid {
                continue;
            }
            for offset in offset_lower..=offset_upper {
                let error = compute_error(scaled_base, growth, divisor, offset, scaled_data, num_levels);
                if error < 0.001 {
                    let (g, d, o) = gcd_normalize(growth, divisor, offset, scaled_data, scaled_base);
                    return Some(FitResult {
                        growth: g,
                        divisor: d,
                        offset: o,
                        scaled_base,
                        scale_factor,
                        max_error: 0.0,
                        is_exact: true,
                    });
                }
            }
        }
    }

    // ── 近似解搜索 ──
    let mut best_growth: i64 = 0;
    let mut best_divisor: i64 = 1;
    let mut best_offset: i64 = 0;
    let mut best_error = f64::MAX;
    let mut best_sort_key: (i64, i64, i64) = (i64::MAX, i64::MAX, i64::MAX);

    for growth in growth_start..growth_end {
        for divisor in divisor_start..divisor_end {
            // 近似 offset = round(Σ(target * divisor - growth * (lv-1)) / num_levels)
            let total: i64 = scaled_data
                .iter()
                .enumerate()
                .map(|(i, &val)| {
                    let lv = i as i64 + 1;
                    (val - scaled_base) * divisor - growth * (lv - 1)
                })
                .sum();
            let offset_approx = (total as f64 / num_levels as f64).round() as i64;

            let error = compute_error(scaled_base, growth, divisor, offset_approx, scaled_data, num_levels);
            let key = (growth, divisor, offset_approx.abs());
            register_candidate(
                growth, divisor, offset_approx, error, key,
                &mut best_error, &mut best_sort_key,
                &mut best_growth, &mut best_divisor, &mut best_offset,
            );

            let (valid, offset_lower, offset_upper) =
                offset_bounds(scaled_data, scaled_base, growth, divisor, num_levels);
            if !valid {
                continue;
            }

            let offset_end = (offset_lower + offset_search_limit).min(offset_upper + 1);
            for offset in offset_lower..offset_end {
                let error = compute_error(scaled_base, growth, divisor, offset, scaled_data, num_levels);
                let key = (growth, divisor, offset.abs());
                register_candidate(
                    growth, divisor, offset, error, key,
                    &mut best_error, &mut best_sort_key,
                    &mut best_growth, &mut best_divisor, &mut best_offset,
                );
            }
        }
    }

    if best_error >= num_levels as f64 * 0.1 {
        return None;
    }

    let (g, d, o) = if best_error < 0.001 {
        gcd_normalize(best_growth, best_divisor, best_offset, scaled_data, scaled_base)
    } else {
        (best_growth, best_divisor, best_offset)
    };

    Some(FitResult {
        growth: g,
        divisor: d,
        offset: o,
        scaled_base,
        scale_factor,
        max_error: best_error / num_levels as f64,
        is_exact: best_error < 0.001,
    })
}

#[inline]
fn register_candidate(
    growth: i64,
    divisor: i64,
    offset: i64,
    error: f64,
    key: (i64, i64, i64),
    best_error: &mut f64,
    best_key: &mut (i64, i64, i64),
    best_growth: &mut i64,
    best_divisor: &mut i64,
    best_offset: &mut i64,
) {
    if *best_error < 0.001 {
        if error < 0.001 && key < *best_key {
            *best_key = key;
            *best_growth = growth;
            *best_divisor = divisor;
            *best_offset = offset;
        }
        return;
    }
    if error < *best_error || (error == *best_error && key < *best_key) {
        *best_error = error;
        *best_key = key;
        *best_growth = growth;
        *best_divisor = divisor;
        *best_offset = offset;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// 用 `compute` 正向计算验证反推结果的正确性
    fn compute_values(params: &FitResult, num_levels: usize) -> Vec<f64> {
        (1..=num_levels)
            .map(|lv| {
                let numerator = params.growth * (lv as i64 - 1) + params.offset;
                let floor_val = if numerator >= 0 {
                    numerator / params.divisor
                } else {
                    (numerator - params.divisor + 1) / params.divisor
                };
                (params.scaled_base + floor_val) as f64 / params.scale_factor as f64
            })
            .collect()
    }

    #[test]
    fn test_simple_linear() {
        // 线性数据: y = 100 + 10*(lv-1) → growth=10*sf, divisor=1, offset=0
        let sf = 10;
        let data: Vec<i64> = (1..=10).map(|lv| (100 + (lv - 1) * 10) * sf).collect();
        let base = data[0];

        let result = fit_floor_formula(&data, base, sf, 1, 5, 1, 200, 500);
        assert!(result.is_some());
        let r = result.unwrap();
        assert!(r.is_exact);
        assert!((r.max_error - 0.0).abs() < 1e-9);
        assert_eq!(r.divisor, 1);
    }

    #[test]
    fn test_floor_divisor() {
        // floor 除法: y = floor((100 + (lv-1) * 7) / 3)
        let sf = 1;
        let data: Vec<i64> = (1..=20)
            .map(|lv| ((100 + (lv - 1) * 7) as f64 / 3.0).floor() as i64 * sf)
            .collect();
        let base = data[0];

        let result = fit_floor_formula(&data, base, sf, 1, 10, 1, 500, 500);
        assert!(result.is_some());
        let r = result.unwrap();
        assert!(r.is_exact, "should find exact match");
        // growth=7, divisor=3
        assert_eq!(r.growth / r.divisor, 2); // growth/divisor ≈ 7/3
    }

    #[test]
    fn test_arknights_like() {
        // 明日方舟式属性：精0 1-50级，每级增长 ~34.3
        // scaled: floor(34.3*(lv-1))*10 = floor(343*(lv-1)/10)*10
        // 公式搜索到 growth=3430, divisor=10, offset=0
        let sf = 1;
        let data: Vec<i64> = (1..=50)
            .map(|lv| 100 + (343 * (lv - 1)) / 10)
            .collect();
        let base = data[0];

        let result = fit_floor_formula(&data, base, sf, 1, 50, 1, 5000, 500);
        assert!(result.is_some());
        let r = result.unwrap();
        assert!(r.is_exact, "should be exact match");
        assert_eq!(r.growth, 343);
        assert_eq!(r.divisor, 10);
    }

    #[test]
    fn test_negative_growth() {
        // 递减数据（如技能 SP 消耗随等级下降）
        let sf = 10;
        let data: Vec<i64> = (1..=10)
            .map(|lv| (200 - (5 * (lv - 1)) / 1) * sf)
            .collect();
        let base = data[0];

        let result = fit_floor_formula(&data, base, sf, 1, 10, -200, -1, 500);
        assert!(result.is_some());
        let r = result.unwrap();
        assert!(r.is_exact);
    }

    #[test]
    fn test_large_scale() {
        // 90 级数据 + 较大的 growth/divisor
        // 使用 sf=1，growth=1234, divisor=50
        let sf = 1;
        let data: Vec<i64> = (1..=90)
            .map(|lv| 1500 + (1234 * (lv - 1)) / 50)
            .collect();
        let base = data[0];

        let result = fit_floor_formula(&data, base, sf, 1, 100, 1, 5000, 1000);
        assert!(result.is_some());
        let r = result.unwrap();
        assert!(r.is_exact);
        // 可能有 GCD 约分: 1234/50 = 617/25，验证比值一致
        assert_eq!(r.growth * 50, r.divisor * 1234, "growth/divisor 应等于 1234/50");
    }

    #[test]
    fn test_approximate_solution() {
        // 使用非整数增长（无法精确表示为 floor 公式）→ 近似解
        let sf = 1;
        let data: Vec<i64> = (1..=15)
            .map(|lv| 100 + ((lv as f64 - 1.0) * 10.7).floor() as i64)
            .collect();
        let base = data[0];

        let result = fit_floor_formula(&data, base, sf, 1, 20, 1, 500, 500);
        assert!(result.is_some(), "should find approximate solution");
        let r = result.unwrap();
        // 应该是近似解（不是精确匹配）
        assert!(r.max_error < 2.0, "error should be moderate, got {}", r.max_error);
    }
}
