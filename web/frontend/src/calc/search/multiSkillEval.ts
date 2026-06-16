/** 多技能段级加权求值（对齐 evaluate_multi_skill_task 语义子集）。 */

import type { WebLoadoutPayload } from "../../api/loadout";
import { materializeCharacterEntity } from "../materialize";
import { valueAtLevel } from "../formula";
import { buildLoadoutContext } from "../context";
import { evaluateGraphInWorker } from "../dag/evaluateInWorker";
import type { DAGGraphRaw } from "../dag/types";
import { extractFinalDamage } from "./searchToLoadout";

function parseSegmentKey(key: string): { skillField: string; segmentIndex: number } | null {
  const m = /^(.+?):(\d+)$/.exec(key.trim());
  if (!m) return null;
  const label = m[1];
  const segmentIndex = Number(m[2]);
  const fieldMap: Record<string, string> = {
    战技: "战技倍率",
    连携技: "连携技倍率",
    终结技: "终结技倍率",
    普通攻击: "普通攻击倍率",
  };
  const skillField = fieldMap[label];
  if (!skillField || !Number.isFinite(segmentIndex) || segmentIndex < 1) return null;
  return { skillField, segmentIndex };
}

function segmentMultiplier(
  payload: WebLoadoutPayload,
  skillField: string,
  segmentIndex: number,
): number {
  const char = materializeCharacterEntity(payload.char_data);
  const segments = char[skillField];
  if (!Array.isArray(segments) || segments.length === 0) return 1;
  const segIdx = Math.max(0, Math.min(segments.length - 1, segmentIndex - 1));
  const curve = segments[segIdx];
  if (!Array.isArray(curve) || curve.length === 0) return 1;
  const level =
    skillField === "战技倍率"
      ? payload.skill_1_level
      : skillField === "连携技倍率"
        ? payload.skill_2_level
        : skillField === "终结技倍率"
          ? payload.skill_3_level
          : payload.skill_1_level;
  return valueAtLevel(curve as number[], level) / 100;
}

/** 单配装多段加权总伤。 */
export async function evaluateMultiSkillWeightedDamage(
  dag: DAGGraphRaw,
  payload: WebLoadoutPayload,
  manualCounts: Record<string, number>,
): Promise<number> {
  let total = 0;
  const basePayload = { ...payload, use_manual_multi_skill_counts: false };
  for (const [key, count] of Object.entries(manualCounts)) {
    const times = Number(count);
    if (!Number.isFinite(times) || times <= 0) continue;
    const parsed = parseSegmentKey(key);
    if (!parsed) continue;
    const ctx = buildLoadoutContext(basePayload);
    const computed = (ctx.computed ?? {}) as Record<string, unknown>;
    computed.技能倍率 = segmentMultiplier(basePayload, parsed.skillField, parsed.segmentIndex);
    ctx.computed = computed;
    const result = await evaluateGraphInWorker(dag, ctx);
    total += extractFinalDamage(result.outputs) * times;
  }
  return total;
}

export function hasActiveManualCounts(manualCounts: Record<string, number> | null | undefined): boolean {
  if (!manualCounts) return false;
  return Object.values(manualCounts).some((v) => Number(v) > 0);
}
