import type { SearchRequest } from "../../api/search";

/** 简化 run_signature（对齐桌面 build_run_signature 主要字段）。 */
export function buildSearchRunSignature(
  params: SearchRequest,
  counts: {
    weaponCount: number;
    chestCount: number;
    loadoutCombos: number;
    candidateNames?: { weapons: string[]; chest: string[]; gloves: string[]; accessories: string[] };
    topN?: number;
  },
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
    JSON.stringify(params.weapon_skill_values ?? {}),
    String(params.skill_1_level),
    String(params.skill_2_level),
    String(params.skill_3_level),
    String(params.enemy_defense),
    String(params.enemy_resistance),
    String(params.ignore_resistance),
    String(params.imbalance_vulnerability_coeff),
    String(params.is_unbalanced),
    String(params.is_true_damage),
    String(params.combo_stacks),
    String(params.break_defense_stacks),
    String(params.attached_effect_multiplier),
    String(params.corrosion_duration_seconds),
    JSON.stringify(params.physical_abnormal_counts ?? {}),
    JSON.stringify(params.spell_abnormal_counts ?? {}),
    String(params.damage_component_mode),
    String(params.use_expected_crit),
    String(params.include_conditional_equipment_crit),
    String(params.extra_crit_rate),
    String(params.extra_crit_damage),
    JSON.stringify(counts.candidateNames ?? {}),
    String(counts.topN ?? 0),
  ];
  return parts.join("::");
}
