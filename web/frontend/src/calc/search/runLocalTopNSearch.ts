import type { LoadoutResult, SearchRequest, SearchResult } from "../../api/search";
import { scoreSearchBatch } from "../../api/search";
import { getCalcBackend } from "../../config/calcBackend";
import { getCalcContextMode } from "../../config/calcContext";
import { getSearchBackendMode } from "../../config/searchBackend";
import { buildLoadoutContext } from "../context";
import { evaluateBatchInWorkerPool } from "../dag/workerPool";
import { loadEndfieldDag } from "../dag";
import { buildComboKey } from "./comboKey";
import {
  countLoadoutCombinations,
  iterateLoadoutCombinations,
  resolveFixedLoadoutItems,
  type EquipmentCatalog,
} from "./enumerateLoadouts";
import { filterWeaponsByScope } from "./filterWeapons";
import { evaluateMultiSkillWeightedDamage, hasActiveManualCounts } from "./multiSkillEval";
import { needsServerSearchScoring } from "./needsServerSearchScoring";
import { pruneEquipmentCatalog } from "./pruneCatalog";
import { buildSearchRunSignature } from "./runSignature";
import {
  countProcessed,
  ensureSearchRun,
  flushSearchResumeDb,
  initSearchResumeDb,
  isComboProcessed,
  markProcessedBatch,
  markRunStatus,
  replaceTopScores,
} from "./searchResumeDb";
import { extractFinalDamage, searchRequestToLoadoutPayload } from "./searchToLoadout";
import { TopNTracker } from "./topNTracker";

export interface LocalSearchProgress {
  processed: number;
  total: number;
  topResults: LoadoutResult[];
  skippedPreprocessed?: number;
}

export interface LocalSearchOptions {
  weapons: Record<string, unknown>[];
  equipmentCatalog: EquipmentCatalog;
  topN: number;
  batchSize?: number;
  resume?: boolean;
  onProgress?: (progress: LocalSearchProgress) => void;
  signal?: AbortSignal;
}

const DEFAULT_BATCH_SIZE = 32;
const PROCESSED_BATCH_SIZE = 200;

export function canUseLocalSearch(params: {
  hasCatalog?: boolean;
}): boolean {
  const mode = getSearchBackendMode();
  if (mode === "api") return false;
  if (getCalcBackend() !== "wasm" || getCalcContextMode() !== "local") return false;
  return Boolean(params.hasCatalog);
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

async function evaluateBatchDamage(
  dag: Awaited<ReturnType<typeof loadEndfieldDag>>,
  params: SearchRequest,
  batchPayloads: ReturnType<typeof searchRequestToLoadoutPayload>[],
  batchMeta: LoadoutResult[],
): Promise<number[]> {
  if (needsServerSearchScoring(params)) {
    return scoreSearchBatch(
      params,
      batchMeta.map((row) => ({
        weapon_name: row.weapon_name,
        chest: row.chest,
        gloves: row.gloves,
        accessory_a: row.accessory_a,
        accessory_b: row.accessory_b,
      })),
    );
  }
  const multi = params.use_manual_multi_skill_counts && hasActiveManualCounts(params.manual_counts);
  if (multi) {
    const out: number[] = [];
    for (const payload of batchPayloads) {
      out.push(await evaluateMultiSkillWeightedDamage(dag, payload, params.manual_counts ?? {}));
    }
    return out;
  }
  const contexts = batchPayloads.map((p) => buildLoadoutContext(p));
  const results = await evaluateBatchInWorkerPool(dag, contexts);
  return results.map((r) => extractFinalDamage(r.outputs));
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
  const signature = buildSearchRunSignature(params, {
    weaponCount: weapons.length,
    chestCount: catalog.chest?.length ?? 0,
    loadoutCombos,
  });

  if (options.resume !== false) {
    await initSearchResumeDb();
    await ensureSearchRun(signature, total);
  }

  const tracker = new TopNTracker(options.topN);
  let processed = options.resume !== false ? countProcessed(signature) : 0;
  let skippedPreprocessed = 0;
  const processedBuffer: string[] = [];

  const report = () => {
    options.onProgress?.({
      processed,
      total,
      topResults: tracker.snapshot(),
      skippedPreprocessed,
    });
  };

  for (const weapon of weapons) {
    if (options.signal?.aborted) {
      if (options.resume !== false) {
        markRunStatus(signature, "cancelled");
        await flushSearchResumeDb();
      }
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
    const batchKeys: string[] = [];

    for (const combo of iterateLoadoutCombinations(catalog, fixed, true)) {
      const weaponName = String(weapon.名称 ?? "");
      const chest = String(combo.chest.名称 ?? "");
      const gloves = String(combo.gloves.名称 ?? "");
      const accA = String(combo.accessory_a.名称 ?? "");
      const accB = String(combo.accessory_b.名称 ?? "");
      const comboKey = buildComboKey(weaponName, chest, gloves, accA, accB);

      if (options.resume !== false && isComboProcessed(signature, comboKey)) {
        skippedPreprocessed += 1;
        continue;
      }

      const payload = searchRequestToLoadoutPayload(params, weapon, combo, catalog);
      batchPayloads.push(payload);
      batchKeys.push(comboKey);
      batchMeta.push({
        weapon_name: weaponName,
        chest,
        gloves,
        accessory_a: accA,
        accessory_b: accB,
        final_damage: 0,
      });

      if (batchPayloads.length >= batchSize) {
        const damages = await evaluateBatchDamage(dag, params, batchPayloads, batchMeta);
        for (let i = 0; i < damages.length; i += 1) {
          batchMeta[i].final_damage = damages[i];
          tracker.consider(batchMeta[i]);
        }
        processed += batchPayloads.length;
        if (options.resume !== false) {
          processedBuffer.push(...batchKeys);
          if (processedBuffer.length >= PROCESSED_BATCH_SIZE) {
            markProcessedBatch(signature, processedBuffer.splice(0, processedBuffer.length));
            replaceTopScores(signature, tracker.snapshot());
          }
        }
        batchPayloads.length = 0;
        batchMeta.length = 0;
        batchKeys.length = 0;
        report();
        if (options.signal?.aborted) {
          if (options.resume !== false) {
            if (processedBuffer.length) markProcessedBatch(signature, processedBuffer);
            markRunStatus(signature, "cancelled");
            await flushSearchResumeDb();
          }
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
      const damages = await evaluateBatchDamage(dag, params, batchPayloads, batchMeta);
      for (let i = 0; i < damages.length; i += 1) {
        batchMeta[i].final_damage = damages[i];
        tracker.consider(batchMeta[i]);
      }
      processed += batchPayloads.length;
      if (options.resume !== false) {
        processedBuffer.push(...batchKeys);
      }
      report();
    }
  }

  if (options.resume !== false) {
    if (processedBuffer.length) markProcessedBatch(signature, processedBuffer);
    replaceTopScores(signature, tracker.snapshot());
    markRunStatus(signature, "completed");
    await flushSearchResumeDb();
  }

  return {
    top_results: tracker.snapshot(),
    total_combinations: total,
    searched_combinations: processed,
    cancelled: false,
    warnings: skippedPreprocessed > 0 ? [`续跑跳过已处理 ${skippedPreprocessed} 组合`] : [],
  };
}
