/** 配装组合枚举（对齐 slot_search.iter_loadout_combinations_for_selection）。 */

export type EquipmentCatalog = Record<string, Record<string, unknown>[]>;

export interface FixedLoadoutItems {
  chest: Record<string, unknown> | null;
  gloves: Record<string, unknown> | null;
  accessory_a: Record<string, unknown> | null;
  accessory_b: Record<string, unknown> | null;
}

export interface LoadoutCombo {
  chest: Record<string, unknown>;
  gloves: Record<string, unknown>;
  accessory_a: Record<string, unknown>;
  accessory_b: Record<string, unknown>;
}

function findByName(
  catalogKey: string,
  name: string | null | undefined,
  catalog: EquipmentCatalog,
): Record<string, unknown> | null {
  if (!name) return null;
  for (const row of catalog[catalogKey] ?? []) {
    if (String(row.名称 ?? "") === String(name)) return row;
  }
  return null;
}

export function resolveFixedLoadoutItems(
  catalog: EquipmentCatalog,
  fixedNames: Record<string, string | null> | undefined,
): FixedLoadoutItems {
  return {
    chest: findByName("chest", fixedNames?.chest, catalog),
    gloves: findByName("gloves", fixedNames?.gloves, catalog),
    accessory_a: findByName("accessory_a", fixedNames?.accessory_a, catalog),
    accessory_b: findByName("accessory_b", fixedNames?.accessory_b, catalog),
  };
}

function choicesForSlot(
  items: Record<string, unknown>[],
  fixed: Record<string, unknown> | null,
): Record<string, unknown>[] {
  return fixed ? [fixed] : items;
}

export function countLoadoutCombinations(
  catalog: EquipmentCatalog,
  fixed: FixedLoadoutItems,
  allowDuplicateAccessory = true,
): number {
  let n = 0;
  for (const _ of iterateLoadoutCombinations(catalog, fixed, allowDuplicateAccessory)) {
    n += 1;
  }
  return n;
}

export function* iterateLoadoutCombinations(
  catalog: EquipmentCatalog,
  fixed: FixedLoadoutItems,
  allowDuplicateAccessory = true,
): Generator<LoadoutCombo> {
  const chests = catalog.chest ?? [];
  const gloves = catalog.gloves ?? [];
  const accessories = catalog.accessories ?? [];
  if (!chests.length || !gloves.length || !accessories.length) {
    return;
  }

  const chestChoices = choicesForSlot(chests, fixed.chest);
  const gloveChoices = choicesForSlot(gloves, fixed.gloves);
  const accAChoices = choicesForSlot(accessories, fixed.accessory_a);
  const accBChoices = choicesForSlot(accessories, fixed.accessory_b);

  if (!chestChoices.length || !gloveChoices.length || !accAChoices.length || !accBChoices.length) {
    return;
  }

  for (const chest of chestChoices) {
    for (const glove of gloveChoices) {
      for (const accessory_a of accAChoices) {
        for (const accessory_b of accBChoices) {
          if (
            !allowDuplicateAccessory &&
            String(accessory_a.名称 ?? "") === String(accessory_b.名称 ?? "")
          ) {
            continue;
          }
          yield { chest, gloves: glove, accessory_a, accessory_b };
        }
      }
    }
  }
}
