import type { SearchRequest } from "../../api/search";

/** 简化 run_signature（对齐桌面 build_run_signature 主要字段）。 */
export function buildSearchRunSignature(
  params: SearchRequest,
  counts: { weaponCount: number; chestCount: number; loadoutCombos: number },
): string {
  const fixed = params.fixed_equipment_names ?? {};
  const parts = [
    String(params.char_data?.名称 ?? ""),
    String(params.char_level),
    String(params.weapon_level),
    String(params.trust_level),
    params.skill_name,
    params.skill_type,
    params.weapon_scope_label,
    params.equipment_scope_label,
    String(counts.weaponCount),
    String(counts.chestCount),
    String(counts.loadoutCombos),
    `c:${fixed.chest ?? "vary"}`,
    `g:${fixed.gloves ?? "vary"}`,
    `a1:${fixed.accessory_a ?? "vary"}`,
    `a2:${fixed.accessory_b ?? "vary"}`,
    params.use_manual_multi_skill_counts ? "multi" : "single",
    JSON.stringify(params.manual_counts ?? {}),
  ];
  return parts.join("::");
}
