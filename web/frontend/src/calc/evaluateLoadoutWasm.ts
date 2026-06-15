import type { EvaluateResult } from "../api/compute";
import type { WebLoadoutPayload } from "../api/loadout";
import { getCalcBackend } from "../config/calcBackend";
import { sampleEntityAtLevel } from "./materialize";

interface GoldenFile {
  payload: WebLoadoutPayload;
  outputs: Record<string, number>;
  node_values: Record<string, number>;
  execution_order: string[];
}

let goldenCache: GoldenFile | null = null;

async function loadGolden(): Promise<GoldenFile | null> {
  if (goldenCache) return goldenCache;
  try {
    const r = await fetch("/wasm-golden/canonical_loadout.json");
    if (!r.ok) return null;
    goldenCache = (await r.json()) as GoldenFile;
    return goldenCache;
  } catch {
    return null;
  }
}

/** 4.1 POC：canonical golden 命中时返回预导出 outputs；否则回退 API。 */
export async function evaluateLoadoutWasm(payload: WebLoadoutPayload): Promise<EvaluateResult | null> {
  const golden = await loadGolden();
  if (!golden || !payloadMatchesGolden(payload, golden.payload)) {
    return null;
  }
  sampleEntityAtLevel(payload.weapon_data, "weapon", payload.weapon_level);
  return {
    outputs: golden.outputs,
    node_values: golden.node_values,
    execution_order: golden.execution_order,
  };
}

function payloadMatchesGolden(payload: WebLoadoutPayload, goldenPayload: WebLoadoutPayload): boolean {
  const a = stablePayload(payload);
  const b = stablePayload(goldenPayload);
  return JSON.stringify(a) === JSON.stringify(b);
}

function stablePayload(payload: WebLoadoutPayload): Record<string, unknown> {
  return {
    char_name: (payload.char_data as Record<string, unknown>)["名称"],
    weapon_name: (payload.weapon_data as Record<string, unknown>)["名称"],
    char_level: payload.char_level,
    weapon_level: payload.weapon_level,
    trust_level: payload.trust_level,
    skill_1_level: payload.skill_1_level,
    skill_2_level: payload.skill_2_level,
    skill_3_level: payload.skill_3_level,
  };
}

export async function evaluateLoadoutWithBackend(
  payload: WebLoadoutPayload,
  apiCall: () => Promise<EvaluateResult>,
): Promise<EvaluateResult> {
  if (getCalcBackend() === "wasm") {
    const local = await evaluateLoadoutWasm(payload);
    if (local) return local;
  }
  return apiCall();
}
