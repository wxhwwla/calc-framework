/** 干员列表筛选用（与 BWIKI 星级 / 职业 / 分支一致） */
export interface OperatorIndexEntry {
  名称: string;
  星级: number;
  职业: string;
  分支: string;
}

export interface OperatorCatalog {
  operators: string[];
  index: OperatorIndexEntry[];
  count: number;
}

export interface OperatorSummary {
  名称: string;
  星级: number;
  职业: string;
  分支: string;
  特性: string;
  基础属性: Record<string, number>;
  信赖加成: Record<string, number>;
  天赋: { name: string; description: string; unlock: string }[];
  技能: ArknightsSkill[];
  潜能: string[];
}

export interface ArknightsSkillLevel {
  description: string;
  sp_cost: number;
  init_sp: number;
  duration: string;
}

export interface ArknightsSkill {
  name: string;
  sp_type: string;
  trigger: string;
  levels: ArknightsSkillLevel[];
}

export interface ComputeRequest {
  operator_name: string;
  skill_multiplier: number;
  skill_level: number;
  enemy_def: number;
  enemy_res: number;
  atk_percent_bonus: number;
  dmg_bonus: number;
  def_penetration: number;
  res_penetration: number;
}

export interface ComputeResponse {
  operator_name: string;
  final_atk: number;
  physical_damage: number;
  magical_damage: number;
  true_damage: number;
  execution_count: number;
}

import { readApiJson } from "../utils/readApiJson";

const BASE = "/api/arknights";

export async function fetchOperatorCatalog(): Promise<OperatorCatalog> {
  const r = await fetch(`${BASE}/operators`);
  const data = await readApiJson<OperatorCatalog>(r);
  if (data.index?.length) {
    return data;
  }
  return {
    operators: data.operators,
    count: data.count ?? data.operators.length,
    index: data.operators.map((名称) => ({ 名称, 星级: 0, 职业: "", 分支: "" })),
  };
}

export async function fetchOperatorDetail(name: string): Promise<OperatorSummary> {
  const r = await fetch(`${BASE}/operators/${encodeURIComponent(name)}`);
  return readApiJson<OperatorSummary>(r);
}

export async function computeDamage(req: ComputeRequest): Promise<ComputeResponse> {
  const r = await fetch(`${BASE}/compute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  return readApiJson<ComputeResponse>(r);
}
