/** Context 来源：local（默认，浏览器构建）| api（服务器构建） */

export type CalcContextMode = "local" | "api";

export function getCalcContextMode(): CalcContextMode {
  const raw = (import.meta.env.VITE_CALC_CONTEXT as string | undefined)?.trim().toLowerCase();
  if (raw === "api") return "api";
  return "local";
}
