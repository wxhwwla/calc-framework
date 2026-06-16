# WASM 曲线加速（Rust）

可选 `floor_linear` WASM 模块；构建需安装 Rust + wasm-pack。

```powershell
cargo install wasm-pack
cd web/wasm-curve
wasm-pack build --target web --out-dir ../frontend/public/wasm-curve --release
```

前端 `calc/wasmCurve.ts` 优先加载 `public/wasm-curve/endfield_curve_wasm_bg.wasm`，失败时回退 TS `formula.ts`。
