/** Context 来源：api（默认）| local（浏览器构建，无 loadout-context 请求） */

export type CalcContextMode = "api" | "local";

export function getCalcContextMode(): CalcContextMode {
  const raw = (import.meta.env.VITE_CALC_CONTEXT as string | undefined)?.trim().toLowerCase();
  return raw === "local" ? "local" : "api";
}
