/** 计算后端选择：api（默认）| wasm（本地 POC） */

export type CalcBackend = "api" | "wasm";

export function getCalcBackend(): CalcBackend {
  const raw = (import.meta.env.VITE_CALC_BACKEND as string | undefined)?.trim().toLowerCase();
  return raw === "wasm" ? "wasm" : "api";
}
