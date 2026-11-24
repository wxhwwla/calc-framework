import type { FixedLoadoutSelection } from "../components/calculator/FixedLoadoutPanel";
import type { HistoryEntry } from "./history";
import { fetchCharacter, fetchWeapon } from "./data";

export async function loadEntitiesForRestore(
  charName: string,
  weaponName: string,
): Promise<[Record<string, unknown> | null, Record<string, unknown> | null]> {
  return Promise.all([
    charName ? fetchCharacter(charName) : Promise.resolve(null),
    weaponName ? fetchWeapon(weaponName) : Promise.resolve(null),
  ]);
}

export function historyPresetPayload(entry: HistoryEntry): Record<string, unknown> {
  const loadout = (entry.loadout as Record<string, unknown> | undefined) ?? {};
  return {
    ...loadout,
    char_name: entry.char_name,
    weapon_name: entry.weapon_name,
  };
}

export function fixedLoadoutFromPayload(data: Record<string, unknown>): FixedLoadoutSelection | null {
  const direct = data.fixed_loadout as FixedLoadoutSelection | null | undefined;
  if (direct) return direct;
  const names = data.fixed_equipment_names as Record<string, string | null> | undefined;
  if (!names) return null;
  return {
    chest: names.chest ?? null,
    gloves: names.gloves ?? null,
    accessory_a: names.accessory_a ?? null,
    accessory_b: names.accessory_b ?? null,
  };
}
