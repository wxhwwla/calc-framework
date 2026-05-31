const BASE = "/api";

export interface AdapterInfo {
  name: string;
  game: string;
  version: string;
  description: string;
}

export interface AdapterAttr {
  name: string;
  type: string;
  source: string;
  default: number | boolean | null;
  description: string;
}

export interface EvaluateResult {
  outputs: Record<string, number>;
  node_values: Record<string, number | string | null>;
  execution_order: string[];
}

export async function fetchAdapters(): Promise<AdapterInfo[]> {
  const r = await fetch(`${BASE}/adapters`);
  if (!r.ok) throw new Error(`Failed to fetch adapters: ${r.statusText}`);
  return r.json();
}

export async function fetchSchema(name: string): Promise<AdapterAttr[]> {
  const r = await fetch(`${BASE}/adapters/${encodeURIComponent(name)}/schema`);
  if (!r.ok) throw new Error(`Failed to fetch schema: ${r.statusText}`);
  const data = await r.json();
  return data.attributes;
}

export async function evaluate(
  adapter: string,
  context: Record<string, Record<string, number | boolean | string>>,
): Promise<EvaluateResult> {
  const r = await fetch(`${BASE}/compute/evaluate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ adapter, context }),
  });
  if (!r.ok) {
    const text = await r.text();
    throw new Error(`Compute failed (${r.status}): ${text}`);
  }
  return r.json();
}

export interface DamageSnapshot {
  segment_damage: Record<string, number>;
  segment_counts: Record<string, number>;
  segment_totals: Record<string, number>;
  skill_type_totals: Record<string, number>;
  weighted_total_damage: number;
  rotation_share_percent: Record<string, number>;
  zone_share_percent: Record<string, number>;
  selected_skill_label: string;
}

export async function fetchSnapshot(params: {
  char_name: string;
  weapon_name: string;
  char_level?: number;
  weapon_level?: number;
  trust_level?: number;
  skill_1_level?: number;
  skill_2_level?: number;
  skill_3_level?: number;
  normal_skill_1_level?: number;
  normal_skill_2_level?: number;
  normal_skill_3_level?: number;
  special_skill_1_level?: number;
  special_skill_1_stack?: number;
  special_skill_2_level?: number;
  special_skill_2_stack?: number;
  enemy_defense?: number;
  enemy_resistance?: number;
  ignore_resistance?: number;
  imbalance_vulnerability_coeff?: number;
  is_unbalanced?: boolean;
  extra_crit_rate?: number;
  extra_crit_damage?: number;
}): Promise<DamageSnapshot> {
  const r = await fetch(`${BASE}/compute/snapshot`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!r.ok) {
    const text = await r.text();
    throw new Error(`Snapshot failed (${r.status}): ${text}`);
  }
  return r.json();
}
