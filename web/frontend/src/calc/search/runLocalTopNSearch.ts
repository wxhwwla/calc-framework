import type { LoadoutResult, SearchRequest, SearchResult } from "../../api/search";
import { getCalcBackend } from "../../config/calcBackend";
import { getCalcContextMode } from "../../config/calcContext";
import {
  getSearchBackendMode,
  LOCAL_SEARCH_MAX_COMBINATIONS,
} from "../../config/searchBackend";
import { buildLoadoutContext } from "../context";
import { evaluateBatchInWorkerPool } from "../dag/workerPool";
import { loadEndfieldDag } from "../dag";
import {
  countLoadoutCombinations,
  iterateLoadoutCombinations,
  resolveFixedLoadoutItems,
  type EquipmentCatalog,
} from "./enumerateLoadouts";
import { filterWeaponsByScope } from "./filterWeapons";
import { pruneEquipmentCatalog } from "./pruneCatalog";
import { extractFinalDamage, searchRequestToLoadoutPayload } from "./searchToLoadout";
import { TopNTracker } from "./topNTracker";

export interface LocalSearchProgress {
  processed: number;
  total: number;
  topResults: LoadoutResult[];
}

export interface LocalSearchOptions {
  weapons: Record<string, unknown>[];
  equipmentCatalog: EquipmentCatalog;
  topN: number;
  batchSize?: number;
  onProgress?: (progress: LocalSearchProgress) => void;
  signal?: AbortSignal;
}

const DEFAULT_BATCH_SIZE = 32;

export function canUseLocalSearch(params: {
  totalCombinations: number;
  useManualMultiSkill?: boolean;
  hasCatalog?: boolean;
}): boolean {
  if (params.useManualMultiSkill) return false;
  const mode = getSearchBackendMode();
  if (mode === "api") return false;
  if (getCalcBackend() !== "wasm" || getCalcContextMode() !== "local") return false;
  if (!params.hasCatalog) return false;
  const max =
    mode === "local" ? LOCAL_SEARCH_MAX_COMBINATIONS * 4 : LOCAL_SEARCH_MAX_COMBINATIONS;
  return params.totalCombinations <= max;
}

export function prepareLocalSearchCatalog(
  params: SearchRequest,
  weapons: Record<string, unknown>[],
  equipmentCatalog: EquipmentCatalog,
): { weapons: Record<string, unknown>[]; catalog: EquipmentCatalog; total: number } {
  const scopedWeapons = filterWeaponsByScope(
    weapons,
    params.char_data,
    params.current_weapon,
    params.weapon_scope_label,
    params.weapon_candidate_names,
  );
  const catalog = pruneEquipmentCatalog(equipmentCatalog, true);
  const fixed = resolveFixedLoadoutItems(catalog, params.fixed_equipment_names);
  const loadoutCombos = countLoadoutCombinations(catalog, fixed, true);
  const total = scopedWeapons.length * loadoutCombos;
  return { weapons: scopedWeapons, catalog, total };
}

export async function runLocalTopNSearch(
  params: SearchRequest,
  options: LocalSearchOptions,
): Promise<SearchResult> {
  const batchSize = options.batchSize ?? DEFAULT_BATCH_SIZE;
  const dag = await loadEndfieldDag();
  const { weapons, catalog } = prepareLocalSearchCatalog(
    params,
    options.weapons,
    options.equipmentCatalog,
  );
  const fixed = resolveFixedLoadoutItems(catalog, params.fixed_equipment_names);
  const loadoutCombos = countLoadoutCombinations(catalog, fixed, true);
  const total = weapons.length * loadoutCombos;
  const tracker = new TopNTracker(options.topN);
  let processed = 0;

  const report = () => {
    options.onProgress?.({
      processed,
      total,
      topResults: tracker.snapshot(),
    });
  };

  for (const weapon of weapons) {
    if (options.signal?.aborted) {
      return {
        top_results: tracker.snapshot(),
        total_combinations: total,
        searched_combinations: processed,
        cancelled: true,
        warnings: ["浏览器本地搜索已取消"],
      };
    }

    const batchPayloads: ReturnType<typeof searchRequestToLoadoutPayload>[] = [];
    const batchMeta: LoadoutResult[] = [];

    for (const combo of iterateLoadoutCombinations(catalog, fixed, true)) {
      const payload = searchRequestToLoadoutPayload(params, weapon, combo, catalog);
      batchPayloads.push(payload);
      batchMeta.push({
        weapon_name: String(weapon.名称 ?? ""),
        chest: String(combo.chest.名称 ?? ""),
        gloves: String(combo.gloves.名称 ?? ""),
        accessory_a: String(combo.accessory_a.名称 ?? ""),
        accessory_b: String(combo.accessory_b.名称 ?? ""),
        final_damage: 0,
      });

      if (batchPayloads.length >= batchSize) {
        const contexts = batchPayloads.map((p) => buildLoadoutContext(p));
        const results = await evaluateBatchInWorkerPool(dag, contexts);
        for (let i = 0; i < results.length; i += 1) {
          batchMeta[i].final_damage = extractFinalDamage(results[i].outputs);
          tracker.consider(batchMeta[i]);
        }
        processed += batchPayloads.length;
        batchPayloads.length = 0;
        batchMeta.length = 0;
        report();
        if (options.signal?.aborted) {
          return {
            top_results: tracker.snapshot(),
            total_combinations: total,
            searched_combinations: processed,
            cancelled: true,
            warnings: ["浏览器本地搜索已取消"],
          };
        }
      }
    }

    if (batchPayloads.length > 0) {
      const contexts = batchPayloads.map((p) => buildLoadoutContext(p));
      const results = await evaluateBatchInWorkerPool(dag, contexts);
      for (let i = 0; i < results.length; i += 1) {
        batchMeta[i].final_damage = extractFinalDamage(results[i].outputs);
        tracker.consider(batchMeta[i]);
      }
      processed += batchPayloads.length;
      report();
    }
  }

  return {
    top_results: tracker.snapshot(),
    total_combinations: total,
    searched_combinations: processed,
    cancelled: false,
    warnings: [],
  };
}
