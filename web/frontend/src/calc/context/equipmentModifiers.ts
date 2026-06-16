/** 装备 catalog 解析与固定配装聚合（对齐 web_context_enrich / affix.py 子集）。 */

import type { WebLoadoutPayload } from "../../api/loadout";

export interface EquipmentEffect {
  effect_type: string;
  value: number;
}

export interface EquipmentModifiers {
  effects: EquipmentEffect[];
  flat_stats: Record<string, number>;
  attack_percent: number;
}

const STAT_FLAT_RE = /^(力量|敏捷|智识|意志|攻击力|防御力|生命值)(\d+(?:\.\d+)?)(%?)$/;
const SKILL_BONUS_RE = /^(战技|连携技|终结技|普通攻击)伤害(?:加成)?(\d+(?:\.\d+)?)%?$/;
const DAMAGE_BONUS_RE = /^(物理|灼热|电磁|寒冷|自然|法术|超域)?伤害(?:加成)?(\d+(?:\.\d+)?)%?$/;
const ATK_PERCENT_RE = /攻击力\+(\d+(?:\.\d+)?)%/;

function parseAffixLine(text: string): { effects: EquipmentEffect[]; flats: Record<string, number> } {
  const raw = text.trim();
  if (!raw) return { effects: [], flats: {} };
  const compact = raw.replace(/\s/g, "");
  const effects: EquipmentEffect[] = [];
  const flats: Record<string, number> = {};

  const skillMatch = SKILL_BONUS_RE.exec(compact);
  if (skillMatch) {
    effects.push({ effect_type: "技能类型伤害加成", value: Number(skillMatch[2]) / 100 });
    return { effects, flats };
  }

  const dmgMatch = DAMAGE_BONUS_RE.exec(compact);
  if (dmgMatch?.[1]) {
    effects.push({ effect_type: "伤害类型伤害加成", value: Number(dmgMatch[2]) / 100 });
    return { effects, flats };
  }

  const statMatch = STAT_FLAT_RE.exec(compact);
  if (statMatch && statMatch[3] !== "%") {
    flats[statMatch[1]] = Number(statMatch[2]);
    return { effects, flats };
  }

  return { effects, flats };
}

function buildRuntimeEquipment(row: Record<string, unknown>): Record<string, unknown> {
  const flatStats: Record<string, number> = {};
  const effects: EquipmentEffect[] = [];
  for (const text of (row.属性词条 as unknown[]) ?? []) {
    const parsed = parseAffixLine(String(text));
    for (const [k, v] of Object.entries(parsed.flats)) {
      flatStats[k] = (flatStats[k] ?? 0) + v;
    }
    effects.push(...parsed.effects);
  }
  for (const text of (row.效果 as unknown[]) ?? []) {
    const parsed = parseAffixLine(String(text));
    effects.push(...parsed.effects);
  }
  return {
    ...row,
    flat_stats: flatStats,
    effects,
    套装: String(row.套装 ?? ""),
    三件套效果: row.三件套效果 ?? [],
  };
}

function findEquipmentRow(
  name: string | null | undefined,
  catalogKey: string,
  catalog: Record<string, Record<string, unknown>[]>,
): Record<string, unknown> | null {
  if (!name) return null;
  for (const row of catalog[catalogKey] ?? []) {
    if (String(row.名称 ?? "") === String(name)) return row;
  }
  return null;
}

function resolveFixedRows(payload: WebLoadoutPayload): Record<string, unknown>[] {
  const catalog = payload.equipment_catalog ?? {};
  const names = payload.fixed_equipment_names ?? {};
  const slots: [string, string][] = [
    ["chest", "chest"],
    ["gloves", "gloves"],
    ["accessory_a", "accessories"],
    ["accessory_b", "accessories"],
  ];
  const rows: Record<string, unknown>[] = [];
  for (const [slotKey, catalogKey] of slots) {
    const row = findEquipmentRow(names[slotKey], catalogKey, catalog as Record<string, Record<string, unknown>[]>);
    if (row) rows.push(buildRuntimeEquipment(row));
  }
  return rows;
}

function absorbItem(
  item: Record<string, unknown>,
  acc: EquipmentModifiers,
): void {
  for (const eff of (item.effects as EquipmentEffect[]) ?? []) {
    if (eff.effect_type === "装备攻击力加成") {
      acc.attack_percent += eff.value;
    } else {
      acc.effects.push(eff);
    }
  }
  for (const [key, val] of Object.entries((item.flat_stats as Record<string, number>) ?? {})) {
    acc.flat_stats[key] = (acc.flat_stats[key] ?? 0) + Number(val);
  }
}

export function resolveEquipmentModifiers(payload: WebLoadoutPayload): EquipmentModifiers {
  const acc: EquipmentModifiers = { effects: [], flat_stats: {}, attack_percent: 0 };
  const items = resolveFixedRows(payload);
  if (items.length === 0) return acc;

  const setCounts: Record<string, number> = {};
  for (const item of items) {
    const setId = String(item.套装 ?? "").trim();
    if (setId) setCounts[setId] = (setCounts[setId] ?? 0) + 1;
  }

  for (const item of items) {
    absorbItem(item, acc);
  }

  for (const [setId, count] of Object.entries(setCounts)) {
    if (count < 3) continue;
    const owner = items.find((it) => String(it.套装 ?? "").trim() === setId);
    if (!owner) continue;
    for (const text of (owner.三件套效果 as unknown[]) ?? []) {
      const match = ATK_PERCENT_RE.exec(String(text).replace(/\s/g, ""));
      if (match) {
        acc.attack_percent += Number(match[1]) / 100;
      }
    }
    break;
  }

  return acc;
}
