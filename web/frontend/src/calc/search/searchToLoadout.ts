import type { SearchRequest } from "../../api/search";
import type { WebLoadoutPayload } from "../../api/loadout";
import { mergeEnemyParams } from "../../api/search";
import { compactEntityForTransport } from "../../utils/entityCompact";
import type { EquipmentCatalog, LoadoutCombo } from "./enumerateLoadouts";

const PRIMARY_DAMAGE_KEY = "最终伤害";

export function extractFinalDamage(outputs: Record<string, number>): number {
  const v = outputs[PRIMARY_DAMAGE_KEY];
  return typeof v === "number" && Number.isFinite(v) ? v : 0;
}

export function searchRequestToLoadoutPayload(
  params: SearchRequest,
  weapon: Record<string, unknown>,
  combo: LoadoutCombo,
  equipmentCatalog: EquipmentCatalog,
): WebLoadoutPayload {
  return {
    char_data: params.char_data,
    weapon_data: compactEntityForTransport(weapon, "weapon"),
    char_level: params.char_level,
    weapon_level: params.weapon_level,
    trust_level: params.trust_level,
    skill_1_level: params.skill_1_level ?? 0,
    skill_2_level: params.skill_2_level ?? 0,
    skill_3_level: params.skill_3_level ?? 0,
    weapon_scope_label: params.weapon_scope_label,
    equipment_scope_label: params.equipment_scope_label,
    weapon_skill_values: (params.weapon_skill_values as Record<string, number>) ?? {},
    use_manual_multi_skill_counts: params.use_manual_multi_skill_counts ?? false,
    manual_counts: params.manual_counts ?? {},
    physical_abnormal_counts: params.physical_abnormal_counts ?? {},
    spell_abnormal_counts: params.spell_abnormal_counts ?? {},
    damage_component_mode: params.damage_component_mode ?? "skill_and_abnormal",
    use_expected_crit: params.use_expected_crit ?? false,
    include_conditional_equipment_crit: params.include_conditional_equipment_crit ?? false,
    extra_crit_rate: params.extra_crit_rate ?? 0,
    extra_crit_damage: params.extra_crit_damage ?? 0,
    enemy_params: mergeEnemyParams({
      enemy_defense: params.enemy_defense,
      enemy_resistance: params.enemy_resistance,
      ignore_resistance: params.ignore_resistance,
      imbalance_vulnerability_coeff: params.imbalance_vulnerability_coeff,
      is_unbalanced: params.is_unbalanced,
      is_true_damage: params.is_true_damage,
      combo_stacks: params.combo_stacks,
      break_defense_stacks: params.break_defense_stacks,
      attached_effect_multiplier: params.attached_effect_multiplier,
      corrosion_duration_seconds: params.corrosion_duration_seconds,
    }),
    fixed_equipment_names: {
      chest: String(combo.chest.名称 ?? ""),
      gloves: String(combo.gloves.名称 ?? ""),
      accessory_a: String(combo.accessory_a.名称 ?? ""),
      accessory_b: String(combo.accessory_b.名称 ?? ""),
    },
    manual_buffs: {},
    equipment_catalog: equipmentCatalog,
    calc_mode: "zone_snapshot",
  };
}
