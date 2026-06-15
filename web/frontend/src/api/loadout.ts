import type { EnemyParams, SearchRequest } from "./search";
import type { MultiSkillSettings } from "../components/calculator/MultiSkillPanel";
import type { CritAndAbnormalSettings } from "../components/calculator/CritAndAbnormalPanel";
import type { FixedLoadoutSelection } from "../components/calculator/FixedLoadoutPanel";
import type { EvaluateResult } from "./compute";
import { compactEntityForTransport } from "../utils/entityCompact";

export interface WebLoadoutPayload {
  char_data: Record<string, unknown>;
  weapon_data: Record<string, unknown>;
  char_level: number;
  weapon_level: number;
  trust_level: number;
  skill_1_level: number;
  skill_2_level: number;
  skill_3_level: number;
  weapon_scope_label: string;
  equipment_scope_label: string;
  weapon_skill_values: Record<string, number>;
  use_manual_multi_skill_counts: boolean;
  manual_counts: Record<string, number>;
  physical_abnormal_counts: Record<string, number>;
  spell_abnormal_counts: Record<string, number>;
  damage_component_mode: string;
  use_expected_crit: boolean;
  include_conditional_equipment_crit: boolean;
  extra_crit_rate: number;
  extra_crit_damage: number;
  enemy_params: EnemyParams;
  fixed_equipment_names: Record<string, string | null>;
  manual_buffs: Record<string, { effect_type: string; value: number }[]>;
  equipment_catalog?: Record<string, Record<string, unknown>[]>;
  calculation_mode?: string;
  calc_mode?: string;
}

export interface BuildLoadoutContext {
  charData: Record<string, unknown> | null;
  weaponData: Record<string, unknown> | null;
  charLevel: number;
  weaponLevel: number;
  trustLevel: number;
  skillLevels: Record<string, number>;
  weaponSkillValues: Record<string, number>;
  weaponScope: string;
  equipmentScope: string;
  calcMode: string;
  multiSkill: MultiSkillSettings;
  critAbnormal: CritAndAbnormalSettings;
  enemyParams: EnemyParams;
  fixedLoadout: FixedLoadoutSelection | null;
  manualBuffStore: Record<string, { effect_type: string; value: number }[]>;
  equipmentCatalog?: Record<string, unknown[]>;
}

function resolveCalculationMode(calcMode: string, multiSkill: MultiSkillSettings): string {
  if (calcMode === "single_skill_search" || calcMode === "multi_skill_search") {
    return calcMode;
  }
  if (multiSkill.useManualCounts) {
    return "multi_skill_search";
  }
  return "single_skill_search";
}

export function buildWebLoadoutPayload(ctx: BuildLoadoutContext): WebLoadoutPayload | null {
  if (!ctx.charData || !ctx.weaponData) return null;
  const calculationMode = resolveCalculationMode(ctx.calcMode, ctx.multiSkill);
  return {
    char_data: compactEntityForTransport(ctx.charData, "character"),
    weapon_data: compactEntityForTransport(ctx.weaponData, "weapon"),
    char_level: ctx.charLevel,
    weapon_level: ctx.weaponLevel,
    trust_level: ctx.trustLevel,
    skill_1_level: (ctx.skillLevels.skill_1_level as number) ?? 8,
    skill_2_level: (ctx.skillLevels.skill_2_level as number) ?? 8,
    skill_3_level: (ctx.skillLevels.skill_3_level as number) ?? 8,
    weapon_scope_label: ctx.weaponScope,
    equipment_scope_label: ctx.equipmentScope,
    weapon_skill_values: ctx.weaponSkillValues,
    use_manual_multi_skill_counts: ctx.multiSkill.useManualCounts,
    manual_counts: ctx.multiSkill.manualCounts,
    physical_abnormal_counts: ctx.critAbnormal.physicalAbnormalCounts,
    spell_abnormal_counts: ctx.critAbnormal.spellAbnormalCounts,
    damage_component_mode: ctx.multiSkill.damageComponentMode,
    use_expected_crit: ctx.multiSkill.useExpectedCrit,
    include_conditional_equipment_crit: ctx.critAbnormal.includeConditionalEquipmentCrit,
    extra_crit_rate: ctx.critAbnormal.extraCritRate,
    extra_crit_damage: ctx.critAbnormal.extraCritDamage,
    enemy_params: ctx.enemyParams,
    fixed_equipment_names: {
      chest: ctx.fixedLoadout?.chest ?? null,
      gloves: ctx.fixedLoadout?.gloves ?? null,
      accessory_a: ctx.fixedLoadout?.accessory_a ?? null,
      accessory_b: ctx.fixedLoadout?.accessory_b ?? null,
    },
    manual_buffs: ctx.manualBuffStore,
    equipment_catalog: ctx.equipmentCatalog as Record<string, Record<string, unknown>[]> | undefined,
    calculation_mode: calculationMode,
    calc_mode: ctx.calcMode,
  };
}

export async function evaluateLoadout(payload: WebLoadoutPayload): Promise<EvaluateResult> {
  const r = await fetch("/api/compute/evaluate-loadout", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function fetchLoadoutPreview(payload: WebLoadoutPayload): Promise<string[]> {
  const r = await fetch("/api/compute/preview", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!r.ok) throw new Error(await r.text());
  const data: { lines: string[] } = await r.json();
  return data.lines;
}

export async function fetchLoadoutSnapshot(payload: WebLoadoutPayload) {
  const r = await fetch("/api/compute/snapshot-full", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

/** 将配装 payload 展平为搜索 API 请求体（技能/固定配装由服务端归一化） */
export function buildSearchRequestFromLoadout(
  payload: WebLoadoutPayload,
  extras: {
    all_weapons: Record<string, unknown>[];
    current_weapon: Record<string, unknown>;
    equipment_catalog: Record<string, Record<string, unknown>[]>;
  },
): Omit<SearchRequest, "top_n" | "max_workers"> {
  const ep = payload.enemy_params;
  return {
    char_data: payload.char_data,
    char_level: payload.char_level,
    weapon_level: payload.weapon_level,
    trust_level: payload.trust_level,
    skill_name: "战技",
    skill_type: "战技",
    skill_multiplier: 1.0,
    damage_type: "物理",
    weapon_scope_label: payload.weapon_scope_label,
    equipment_scope_label: payload.equipment_scope_label,
    all_weapons: extras.all_weapons,
    current_weapon: extras.current_weapon,
    equipment_catalog: extras.equipment_catalog,
    fixed_equipment_names: payload.fixed_equipment_names,
    weapon_skill_values: payload.weapon_skill_values,
    enemy_defense: ep.enemy_defense,
    enemy_resistance: ep.enemy_resistance,
    ignore_resistance: ep.ignore_resistance,
    imbalance_vulnerability_coeff: ep.imbalance_vulnerability_coeff,
    is_unbalanced: ep.is_unbalanced,
    is_true_damage: ep.is_true_damage,
    combo_stacks: ep.combo_stacks,
    break_defense_stacks: ep.break_defense_stacks,
    attached_effect_multiplier: ep.attached_effect_multiplier,
    corrosion_duration_seconds: ep.corrosion_duration_seconds,
    physical_abnormal_counts: payload.physical_abnormal_counts,
    spell_abnormal_counts: payload.spell_abnormal_counts,
    damage_component_mode: payload.damage_component_mode,
    use_manual_multi_skill_counts: payload.use_manual_multi_skill_counts,
    manual_counts: payload.manual_counts,
    skill_1_level: payload.skill_1_level,
    skill_2_level: payload.skill_2_level,
    skill_3_level: payload.skill_3_level,
    use_expected_crit: payload.use_expected_crit,
    include_conditional_equipment_crit: payload.include_conditional_equipment_crit,
    extra_crit_rate: payload.extra_crit_rate,
    extra_crit_damage: payload.extra_crit_damage,
  };
}

export async function exportDesktopPreset(payload: WebLoadoutPayload): Promise<Record<string, unknown>> {
  const r = await fetch("/api/compute/preset-export", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}
