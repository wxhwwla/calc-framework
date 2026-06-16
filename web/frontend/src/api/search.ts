import i18n from "../i18n/config";

const BASE = "/api/search";

/** 与桌面 `ENEMY_TIERS` 一致 */
export const ENEMY_TIERS = ["普通", "进阶", "精英", "头目", "领袖"] as const;

/** Display name mapping for ENEMY_TIERS (i18n-aware). */
export function getEnemyTierDisplay(tier: string): string {
  const map: Record<string, string> = {
    "普通": i18n.t("enemyTiers.normal"),
    "进阶": i18n.t("enemyTiers.advanced"),
    "精英": i18n.t("enemyTiers.elite"),
    "头目": i18n.t("enemyTiers.boss"),
    "领袖": i18n.t("enemyTiers.leader"),
  };
  return map[tier] || tier;
}

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
  if (!r.ok) throw new Error(`${i18n.t("api.searchHistoryGetFailed")}: ${r.statusText}`);
  return r.json();
}

export async function saveSearchHistory(entry: SearchHistoryEntry): Promise<void> {
  const r = await fetch(`${BASE}/history`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(entry),
  });
  if (!r.ok) throw new Error(`${i18n.t("api.searchHistorySaveFailed")}: ${r.statusText}`);
}

/** 由搜索参数与结果构建历史条目。 */
export function buildSearchHistoryEntry(
  params: Pick<SearchRequest, "char_data" | "current_weapon" | "skill_name">,
  result: SearchResult,
  options: { topN: number; elapsedSeconds: number; source?: string },
): SearchHistoryEntry {
  return {
    char_name: String(params.char_data?.名称 ?? ""),
    weapon_name: String(params.current_weapon?.名称 ?? ""),
    skill_name: params.skill_name,
    top_n: options.topN,
    result_count: result.top_results.length,
    total_combinations: result.total_combinations,
    searched_combinations: result.searched_combinations,
    elapsed_seconds: options.elapsedSeconds,
    top_results: result.top_results,
    saved_at: new Date().toISOString(),
    search_source: options.source ?? "api",
  };
}

/** 搜索完成后写入历史（失败静默，不阻断 UI）。 */
export async function persistSearchHistory(
  params: Pick<SearchRequest, "char_data" | "current_weapon" | "skill_name">,
  result: SearchResult,
  options: { topN: number; elapsedSeconds: number; source?: string },
): Promise<void> {
  if (result.cancelled || result.top_results.length === 0) {
    return;
  }
  try {
    await saveSearchHistory(buildSearchHistoryEntry(params, result, options));
  } catch {
    // 历史为辅助功能，离线或 PA 写入失败时不打断主流程
  }
}

/** 导出搜索结果 JSON（对齐桌面 search_output 可读格式）。 */
export function downloadSearchResultJson(
  params: SearchRequest,
  result: SearchResult,
  source = "web",
): void {
  const payload = {
    schema: "endfield-search-export-v1",
    exported_at: new Date().toISOString(),
    source,
    params,
    result,
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  const stamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
  anchor.href = url;
  anchor.download = `search-top${result.top_results.length}-${stamp}.json`;
  anchor.click();
  URL.revokeObjectURL(url);
}

export async function fetchEnemyChoices(): Promise<EnemyInfo[]> {
  const r = await fetch(`${BASE}/enemies`);
  if (!r.ok) throw new Error(`${i18n.t("api.enemiesGetFailed")}: ${r.statusText}`);
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
  /** include_catalog=true 时由服务端返回 */
  weapons?: Record<string, unknown>[];
  equipment_catalog?: Record<string, Record<string, unknown>[]>;
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
  /** @deprecated 省略时服务端按 scope 从 catalog 加载 */
  all_weapons?: Record<string, unknown>[];
  weapon_candidate_names?: string[];
  current_weapon: Record<string, unknown>;
  /** @deprecated 省略时服务端按 equipment_scope_label 加载 */
  equipment_catalog?: Record<string, Record<string, unknown>[]>;
  fixed_loadout?: Record<string, unknown> | null;
  fixed_equipment_names?: Record<string, string | null>;
  weapon_skill_values?: Record<string, number>;
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
  top_n?: number;
  max_workers?: number;
  use_manual_multi_skill_counts?: boolean;
  manual_counts?: Record<string, number> | null;
  skill_1_level?: number;
  skill_2_level?: number;
  skill_3_level?: number;
  use_expected_crit?: boolean;
  include_conditional_equipment_crit?: boolean;
  extra_crit_rate?: number;
  extra_crit_damage?: number;
}

export async function estimateSearch(
  params: Omit<SearchRequest, "top_n" | "max_workers" | "extra_crit_rate" | "extra_crit_damage">,
  options?: { includeCatalog?: boolean },
): Promise<SearchEstimate> {
  const r = await fetch(`${BASE}/estimate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ...params,
      include_catalog: options?.includeCatalog ?? false,
    }),
  });
  if (!r.ok) {
    const text = await r.text();
    throw new Error(`${i18n.t("api.searchEstimateFailed")}: ${text}`);
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
    throw new Error(`${i18n.t("api.searchRunFailed")}: ${text}`);
  }
  return r.json();
}

export interface LoadoutComboItem {
  weapon_name: string;
  chest: string;
  gloves: string;
  accessory_a: string;
  accessory_b: string;
}

/** 浏览器本地搜索 — 批量服务端评分（异常 / compose_damage_total parity）。 */
export async function scoreSearchBatch(
  params: SearchRequest,
  loadouts: LoadoutComboItem[],
): Promise<number[]> {
  const r = await fetch(`${BASE}/score-batch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ params, loadouts }),
  });
  if (!r.ok) {
    const text = await r.text();
    throw new Error(`${i18n.t("api.searchRunFailed")}: ${text}`);
  }
  const data = (await r.json()) as { final_damage?: number[] };
  return Array.isArray(data.final_damage) ? data.final_damage : [];
}

export async function fetchEquipmentCatalog(
  scope = "全部装备",
): Promise<Record<string, { 名称: string; 部位: string; 所属套组: string; 稀有度: string }[]>> {
  const r = await fetch(`${BASE}/catalog?scope=${encodeURIComponent(scope)}`);
  if (!r.ok) throw new Error(`${i18n.t("api.equipmentCatalogGetFailed")}: ${r.statusText}`);
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
    throw new Error(`${i18n.t("api.searchStreamFailed")}: ${text}`);
  }

  const reader = r.body?.getReader();
  if (!reader) {
    throw new Error(i18n.t("api.responseNotReadable"));
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
