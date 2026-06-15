/** 传输用 compact — 有 ``成长参数`` 时去掉可再生的等级数组字段。 */

const CHARACTER_BAKED_KEYS = [
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

const WEAPON_BAKED_KEYS = ["基础攻击力"] as const;

function hasGrowthParams(entity: Record<string, unknown>): boolean {
  const growth = entity["成长参数"];
  return typeof growth === "object" && growth !== null && Object.keys(growth as object).length > 0;
}

export type EntityDataFormat = "compact" | "runtime" | "raw";

export function compactEntityForTransport(
  entity: Record<string, unknown>,
  kind: "character" | "weapon",
): Record<string, unknown> {
  if (!hasGrowthParams(entity)) {
    return entity;
  }
  const out = { ...entity };
  const keys = kind === "character" ? CHARACTER_BAKED_KEYS : WEAPON_BAKED_KEYS;
  for (const key of keys) {
    delete out[key];
  }
  delete out["等级"];
  if (kind === "weapon") {
    for (const key of Object.keys(out)) {
      if (key.endsWith("+") && key !== "攻击力+" && Array.isArray(out[key])) {
        delete out[key];
      }
    }
  }
  return out;
}

export function entityFormatQuery(format: EntityDataFormat): string {
  return `?format=${encodeURIComponent(format)}`;
}
