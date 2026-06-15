/** 可选 Rust WASM floor_linear；未构建或加载失败时回退 TS。 */

import { calculateGrowthCurve, type GrowthParams } from "./formula";

type WasmCurveModule = {
  floor_linear_curve: (
    base: number,
    growth: number,
    divisor: number,
    offset: number,
    maxLevel: number,
  ) => Float64Array;
  default: (wasmPath: string) => Promise<void>;
};

let wasmModule: WasmCurveModule | null | undefined;

async function loadWasmCurve(): Promise<WasmCurveModule | null> {
  if (wasmModule !== undefined) return wasmModule;
  try {
    const base = import.meta.env.BASE_URL ?? "/";
    const jsUrl = `${base}wasm-curve/endfield_curve_wasm.js`.replace(/([^:]\/)\/+/g, "$1");
    const wasmUrl = `${base}wasm-curve/endfield_curve_wasm_bg.wasm`.replace(/([^:]\/)\/+/g, "$1");
    const head = await fetch(jsUrl, { method: "HEAD" });
    if (!head.ok) {
      wasmModule = null;
      return null;
    }
    const mod = (await Function(`return import("${jsUrl}")`)()) as WasmCurveModule;
    await mod.default(wasmUrl);
    wasmModule = mod;
  } catch {
    wasmModule = null;
  }
  return wasmModule;
}

export async function calculateGrowthCurveWasm(
  params: GrowthParams,
  maxLevel = 90,
  levelOverrides: Record<number, number> = {},
): Promise<number[] | null> {
  const wasm = await loadWasmCurve();
  if (!wasm) return null;
  const { base, growth, divisor, offset = 0 } = params;
  if (Object.keys(levelOverrides).length > 0) return null;
  const raw = wasm.floor_linear_curve(base, growth, divisor, offset, maxLevel);
  return Array.from(raw);
}

export async function materializeCurveWithWasmFallback(
  params: GrowthParams,
  maxLevel = 90,
  levelOverrides: Record<number, number> = {},
): Promise<number[]> {
  const wasmCurve = await calculateGrowthCurveWasm(params, maxLevel, levelOverrides);
  return wasmCurve ?? calculateGrowthCurve(params, maxLevel, levelOverrides);
}
