import type { EquipmentCatalog } from "./enumerateLoadouts";

function isBeneficial(item: Record<string, unknown>): boolean {
  const effects = item.效果;
  const setEffects = item.三件套效果;
  if (Array.isArray(effects) && effects.length > 0) return true;
  if (Array.isArray(setEffects) && setEffects.length > 0) return true;
  const affixes = item.属性词条;
  return Array.isArray(affixes) && affixes.length > 0;
}

/** 剪枝无益装备（对齐 optimizer/catalog._is_equipment_beneficial）。 */
export function pruneEquipmentCatalog(
  catalog: EquipmentCatalog,
  pruneNonBeneficial = true,
): EquipmentCatalog {
  if (!pruneNonBeneficial) {
    return {
      chest: [...(catalog.chest ?? [])],
      gloves: [...(catalog.gloves ?? [])],
      accessories: [...(catalog.accessories ?? [])],
    };
  }
  const prune = (items: Record<string, unknown>[]) => items.filter(isBeneficial);
  return {
    chest: prune(catalog.chest ?? []),
    gloves: prune(catalog.gloves ?? []),
    accessories: prune(catalog.accessories ?? []),
  };
}
