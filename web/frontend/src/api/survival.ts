import i18n from "../i18n/config";

const BASE = "/api/survival";

export interface SurvivalEstimateRequest {
  char_data: Record<string, unknown>;
  weapon_data: Record<string, unknown>;
  char_level?: number;
  weapon_level?: number;
  trust_level?: number;
  enemy_tier?: string;
  imbalance_efficiency_bonus?: number;
  enemy_max_hp?: number | null;
  enemy_id?: string;
  base_heal_flat?: number;
  stat_per_point?: number;
  heal_efficiency?: number;
  independent_heal_bonus?: number;
  imbalance_gain_base?: number;
  hot_resistance_percent?: number;
  sp_start?: number;
  sp_seconds?: number;
  ult_start?: number;
  life_steal_rate?: number;
}

export interface SurvivalEstimateResult {
  execute_damage: number;
  execute_multiplier: number;
  execute_sp_restore: number;
  imbalance_cap: number;
  imbalance_duration_sec: number;
  imbalance_nodes_1: number[];
  imbalance_nodes_2: number[];
  imbalance_gain_effective: number;
  imbalance_gain_percent: number;
  fast_break_multiplier: number;
  burn_tick_per_sec: number;
  enemy_max_hp: number;
  sp_after_regen: number;
  sp_regen_per_sec: number;
  ultimate_charge_after: number;
  ultimate_charge_per_100_sp: number;
  dodge_sp_gain: number;
  life_steal_heal: number;
  healing_amount: number;
  character_max_hp: number;
}

export async function fetchSurvivalEstimate(
  params: SurvivalEstimateRequest,
): Promise<SurvivalEstimateResult> {
  const r = await fetch(`${BASE}/estimate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!r.ok) {
    const text = await r.text();
    throw new Error(`${i18n.t("api.survivalEstimateFailed")}: ${text}`);
  }
  return r.json();
}
