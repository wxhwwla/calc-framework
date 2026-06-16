/** floor_linear 成长曲线 — 与 Python FloorFormulaFitter 对齐 */

export interface GrowthParams {
  base: number;
  growth: number;
  divisor: number;
  offset?: number;
  is_decimal?: boolean;
  special?: number[];
}

function detectDecimal(params: GrowthParams): boolean {
  if (params.is_decimal != null) return params.is_decimal;
  const vals = [params.base, params.growth, params.divisor, params.offset ?? 0, ...(params.special ?? [])];
  return vals.some((v) => typeof v === "number" && !Number.isInteger(v));
}

export function calculateGrowthCurve(
  params: GrowthParams,
  maxLevel = 90,
  levelOverrides: Record<number, number> = {},
): number[] {
  const { base, growth, divisor, offset = 0 } = params;
  if (divisor <= 0 || maxLevel < 1) {
    throw new Error("invalid growth params");
  }
  const isDecimal = detectDecimal(params);
  const curve: number[] = [];
  if (isDecimal) {
    const scale = 10;
    const sb = base * scale;
    const sg = growth * scale;
    const so = offset * scale;
    for (let lv = 1; lv <= maxLevel; lv += 1) {
      if (levelOverrides[lv] != null) {
        curve.push(Math.round(levelOverrides[lv] * 10) / 10);
      } else {
        curve.push(Math.round((sb + Math.floor((sg * (lv - 1) + so) / divisor)) / scale * 10) / 10);
      }
    }
  } else {
    for (let lv = 1; lv <= maxLevel; lv += 1) {
      if (levelOverrides[lv] != null) {
        curve.push(Math.round(levelOverrides[lv] * 10) / 10);
      } else {
        curve.push(Math.round((base + Math.floor((growth * (lv - 1) + offset) / divisor)) * 10) / 10);
      }
    }
  }
  return curve;
}

export function valueAtLevel(curve: number[], level: number): number {
  const idx = Math.max(0, Math.min(curve.length - 1, level - 1));
  return curve[idx];
}
