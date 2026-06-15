/** 从 ``成长参数`` 物化角色/武器曲线（compact 双读） */

import { calculateGrowthCurve, type GrowthParams, valueAtLevel } from "./formula";

const GROWTH_KEY = "成长参数";

const CHARACTER_ATTRS = [
  "力量",
  "敏捷",
  "智识",
  "意志",
  "基础攻击力",
  "基础生命值",
  "基础防御力",
  "战技倍率",
  "连携技倍率",
  "终结技倍率",
] as const;

function parseParams(raw: unknown): GrowthParams | null {
  if (!raw || typeof raw !== "object") return null;
  const p = raw as Record<string, unknown>;
  if (p.base == null || p.growth == null || p.divisor == null) return null;
  const special = Array.isArray(p.special) ? p.special.map(Number) : undefined;
  return {
    base: Number(p.base),
    growth: Number(p.growth),
    divisor: Number(p.divisor),
    offset: Number(p.offset ?? 0),
    is_decimal: p.is_decimal as boolean | undefined,
    special,
  };
}

function skillLevelOverrides(params: GrowthParams, length: number): Record<number, number> {
  const overrides: Record<number, number> = {};
  if (params.special) {
    params.special.forEach((val, idx) => {
      overrides[idx + 1] = val;
    });
  }
  if (length === 9 && params.special?.length) {
    overrides[9] = params.special[params.special.length - 1];
  }
  return overrides;
}

export function materializeCharacterEntity(char: Record<string, unknown>): Record<string, unknown> {
  const growth = char[GROWTH_KEY];
  if (!growth || typeof growth !== "object") return { ...char };
  const out = { ...char };
  const gp = growth as Record<string, unknown>;
  for (const key of CHARACTER_ATTRS) {
    const raw = gp[key];
    if (Array.isArray(raw) && raw.length && Array.isArray(raw[0])) {
      out[key] = (raw as unknown[][]).map((seg) => {
        const params = parseParams(seg[0] ?? seg);
        return params ? calculateGrowthCurve(params, seg.length) : seg.map(Number);
      });
      continue;
    }
    const params = parseParams(raw);
    if (!params) continue;
    const maxLevel = Number(char["最大等级"] ?? 90);
    if (key.includes("倍率")) {
      const len = key === "战技倍率" ? 12 : 9;
      out[key] = calculateGrowthCurve(params, len, skillLevelOverrides(params, len));
    } else {
      out[key] = calculateGrowthCurve(params, maxLevel);
    }
  }
  return out;
}

export function materializeWeaponEntity(weapon: Record<string, unknown>): Record<string, unknown> {
  const growth = weapon[GROWTH_KEY];
  if (!growth || typeof growth !== "object") return { ...weapon };
  const out = { ...weapon };
  const gp = growth as Record<string, unknown>;
  for (const [key, raw] of Object.entries(gp)) {
    const params = parseParams(raw);
    if (!params) continue;
    const maxLevel = key === "基础攻击力" ? Number(weapon["最大等级"] ?? 90) : 9;
    out[key] = calculateGrowthCurve(params, maxLevel);
  }
  return out;
}

export function sampleEntityAtLevel(
  entity: Record<string, unknown>,
  kind: "character" | "weapon",
  level: number,
): Record<string, number> {
  const baked = kind === "character" ? materializeCharacterEntity(entity) : materializeWeaponEntity(entity);
  const out: Record<string, number> = {};
  for (const [key, val] of Object.entries(baked)) {
    if (Array.isArray(val) && val.length && typeof val[0] === "number") {
      out[key] = valueAtLevel(val as number[], level);
    }
  }
  return out;
}
