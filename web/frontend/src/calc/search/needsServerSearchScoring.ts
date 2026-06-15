import type { SearchRequest } from "../../api/search";

/** 浏览器 WASM 本地路径无法完整复现异常/compose 时改走服务端 score-batch。 */
export function needsServerSearchScoring(params: SearchRequest): boolean {
  const mode = params.damage_component_mode ?? "skill_and_abnormal";
  if (mode === "skill_only") return false;
  if (mode === "abnormal_only") return true;
  const phys = params.physical_abnormal_counts ?? {};
  const spell = params.spell_abnormal_counts ?? {};
  return (
    Object.values(phys).some((v) => Number(v) > 0) ||
    Object.values(spell).some((v) => Number(v) > 0)
  );
}
