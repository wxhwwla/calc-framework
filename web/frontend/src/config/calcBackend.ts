/** 计算后端选择：wasm（默认，浏览器本地）| api（服务器计算） */

export type CalcBackend = "wasm" | "api";

export function getCalcBackend(): CalcBackend {
  const raw = (import.meta.env.VITE_CALC_BACKEND as string | undefined)?.trim().toLowerCase();
  if (raw === "api") return "api";
  return "wasm";
}
