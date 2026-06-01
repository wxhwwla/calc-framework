const BASE = "/api/search";

/** 与桌面 `EnemyEvalParams` / 插件默认一致 */
export const DEFAULT_ENEMY_PARAMS: EnemyParams = {
  enemy_defense: 100,
  enemy_resistance: 0,
  ignore_resistance: 0,
  imbalance_vulnerability_coeff: 1.3,
  is_unbalanced: false,
  is_true_damage: false,
  combo_stacks: 0,
  break_defense_stacks: 0,
  attached_effect_multiplier: 1.0,
  corrosion_duration_seconds: 15.0,
  enemy_tier: "普通",
  imbalance_efficiency_bonus: 0.0,
};

export interface EnemyInfo {
  id: string;
  name: string;
  enemy_defense: number;
  enemy_resistance: number;
  ignore_resistance: number;
  imbalance_vulnerability_coeff: number;
  is_unbalanced: boolean;
  is_true_damage: boolean;
  combo_stacks: number;
  break_defense_stacks: number;
  attached_effect_multiplier: number;
  corrosion_duration_seconds: number;
  enemy_tier: string;
  imbalance_efficiency_bonus: number;
}

export interface EnemyParams {
  enemy_defense: number;
  enemy_resistance: number;
  ignore_resistance: number;
  imbalance_vulnerability_coeff: number;
  is_unbalanced: boolean;
  is_true_damage: boolean;
  combo_stacks: number;
  break_defense_stacks: number;
  attached_effect_multiplier: number;
  corrosion_duration_seconds: number;
  enemy_tier: string;
  imbalance_efficiency_bonus: number;
}

/** 预设 v1 仅 5 字段时补全缺省 */
export function mergeEnemyParams(partial: Partial<EnemyParams>): EnemyParams {
  return { ...DEFAULT_ENEMY_PARAMS, ...partial };
}

export interface SearchHistoryEntry {
  char_name: string;
  weapon_name: string;
  skill_name: string;
  top_n: number;
  result_count: number;
  total_combinations: number;
  searched_combinations: number;
  elapsed_seconds?: number;
  top_results?: LoadoutResult[];
  saved_at: string;
  [key: string]: unknown;
}

export async function fetchSearchHistory(): Promise<SearchHistoryEntry[]> {
  const r = await fetch(`${BASE}/history`);
  if (!r.ok) throw new Error(`获取搜索历史失败: ${r.statusText}`);
  return r.json();
}

export async function saveSearchHistory(entry: SearchHistoryEntry): Promise<void> {
  const r = await fetch(`${BASE}/history`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(entry),
  });
  if (!r.ok) throw new Error(`保存搜索历史失败: ${r.statusText}`);
}

export async function fetchEnemyChoices(): Promise<EnemyInfo[]> {
  const r = await fetch(`${BASE}/enemies`);
  if (!r.ok) throw new Error(`获取敌方参数失败: ${r.statusText}`);
  return r.json();
}

export interface LoadoutResult {
  weapon_name: string;
  chest: string;
  gloves: string;
  accessory_a: string;
  accessory_b: string;
  final_damage: number;
  segment_breakdown?: Record<string, number> | null;
}

export interface SearchEstimate {
  total_combinations: number;
  weapon_count: number;
  loadout_combinations: number;
  estimated_seconds: number;
  warnings: string[];
}

export interface SearchResult {
  top_results: LoadoutResult[];
  total_combinations: number;
  searched_combinations: number;
  cancelled: boolean;
  warnings: string[];
}

export interface SearchRequest {
  char_data: Record<string, unknown>;
  char_level: number;
  weapon_level: number;
  trust_level: number;
  skill_name: string;
  skill_type: string;
  skill_multiplier: number;
  damage_type: string;
  weapon_scope_label: string;
  equipment_scope_label: string;
  all_weapons: Record<string, unknown>[];
  current_weapon: Record<string, unknown>;
  equipment_catalog: Record<string, Record<string, unknown>[]>;
  fixed_loadout?: Record<string, unknown> | null;
  enemy_defense: number;
  enemy_resistance?: number;
  ignore_resistance?: number;
  imbalance_vulnerability_coeff?: number;
  is_unbalanced?: boolean;
  is_true_damage?: boolean;
  combo_stacks?: number;
  break_defense_stacks?: number;
  attached_effect_multiplier?: number;
  corrosion_duration_seconds?: number;
  physical_abnormal_counts?: Record<string, number> | null;
  spell_abnormal_counts?: Record<string, number> | null;
  damage_component_mode?: string;
  top_n: number;
  max_workers: number;
  use_manual_multi_skill_counts?: boolean;
  manual_counts?: Record<string, number> | null;
  skill_1_level?: number;
  skill_2_level?: number;
  skill_3_level?: number;
  use_expected_crit?: boolean;
  extra_crit_rate?: number;
  extra_crit_damage?: number;
}

export async function estimateSearch(
  params: Omit<SearchRequest, "top_n" | "max_workers" | "extra_crit_rate" | "extra_crit_damage">,
): Promise<SearchEstimate> {
  const r = await fetch(`${BASE}/estimate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!r.ok) {
    const text = await r.text();
    throw new Error(`搜索预估失败: ${text}`);
  }
  return r.json();
}

export async function runSearch(params: SearchRequest): Promise<SearchResult> {
  const r = await fetch(`${BASE}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!r.ok) {
    const text = await r.text();
    throw new Error(`搜索失败: ${text}`);
  }
  return r.json();
}

export async function fetchEquipmentCatalog(): Promise<Record<string, { 名称: string; 部位: string; 所属套组: string; 稀有度: string }[]>> {
  const r = await fetch(`${BASE}/catalog`);
  if (!r.ok) throw new Error(`获取装备目录失败: ${r.statusText}`);
  return r.json();
}

export interface StreamEvent {
  type: "start" | "heartbeat" | "summary" | "chunk" | "stream_end" | "error";
  total_combinations?: number;
  searched_combinations?: number;
  cancelled?: boolean;
  elapsed_seconds?: number;
  results?: LoadoutResult[];
  chunk_index?: number;
  total_chunks?: number;
  message?: string;
}

export async function runSearchStream(
  params: SearchRequest,
  onEvent: (event: StreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const r = await fetch(`${BASE}/run_stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
    signal,
  });

  if (!r.ok) {
    const text = await r.text();
    throw new Error(`流式搜索失败: ${text}`);
  }

  const reader = r.body?.getReader();
  if (!reader) {
    throw new Error("响应体不可读");
  }

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const data: StreamEvent = JSON.parse(line.slice(6));
          onEvent(data);
        } catch {
          // skip malformed lines
        }
      }
    }
  }
}
