#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test Rust inverse engine vs Python."""

import sys
import time

sys.path.insert(0, "games/endfield")
sys.path.insert(0, "framework/src")
sys.path.insert(0, ".")

import rust_search
from calc_framework.inverse.base import FloorFormulaFitter

fitter = FloorFormulaFitter()

# Test 1: simple linear
data = [100 + 10 * i for i in range(30)]
r = rust_search.fit_floor_formula_py(data, data[0], 1, 1, 20, 1, 500, 500)
assert r is not None, "should find solution"
g, d, o, sf, err, exact = r
print(f"Linear: growth={g}, divisor={d}, exact={exact}")

# Test 2: floor division (Arknights-style)
data2 = [100 + (343 * i) // 10 for i in range(50)]
r2 = rust_search.fit_floor_formula_py(data2, data2[0], 1, 1, 50, 1, 5000, 500)
assert r2 is not None, "should find solution"
g2, d2, *_2 = r2
print(f"Floor:  growth={g2}, divisor={d2}, exact={r2[5]}")

# Test 3: Performance
data3 = [1500 + (1234 * i) // 50 for i in range(90)]
scale = fitter._detect_scale(data3)
scaled = [round(x * scale) for x in data3]
base = scaled[0]
gr = fitter._default_growth_range(data3)
print(f"\nScale={scale}, growth_range={gr}")

# Python
t0 = time.perf_counter()
for _ in range(100):
    r_py = fitter.fit(data3)
t_py = time.perf_counter() - t0
p = r_py.params
print(f"Python 100x: {t_py:.3f}s (growth={p.get('growth')}, divisor={p.get('divisor')}, exact={r_py.is_exact})")

# Rust
t0 = time.perf_counter()
for _ in range(100):
    r_rs = rust_search.fit_floor_formula_py(scaled, base, scale, 1, 101, gr[0], gr[1], 500)
t_rs = time.perf_counter() - t0
print(f"Rust   100x: {t_rs:.3f}s (growth={r_rs[0]}, divisor={r_rs[1]}, exact={r_rs[5]})")
print(f"Speedup: {t_py / t_rs:.1f}x")
