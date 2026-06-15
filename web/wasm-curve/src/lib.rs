//! floor_linear 曲线热点 — WASM 加速（可选，失败回退 TS）。

use wasm_bindgen::prelude::*;

#[wasm_bindgen]
pub fn floor_linear_value(base: f64, growth: f64, divisor: f64, offset: f64, level: i32) -> f64 {
    if divisor <= 0.0 || level < 1 {
        return base;
    }
    let lv = (level - 1) as f64;
    base + ((growth * lv + offset) / divisor).floor()
}

#[wasm_bindgen]
pub fn floor_linear_curve(
    base: f64,
    growth: f64,
    divisor: f64,
    offset: f64,
    max_level: i32,
) -> Vec<f64> {
    let mut out = Vec::with_capacity(max_level.max(0) as usize);
    for level in 1..=max_level {
        out.push(floor_linear_value(base, growth, divisor, offset, level));
    }
    out
}
