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

const BASE = "/api/arknights";

export async function fetchOperators(): Promise<string[]> {
  const r = await fetch(`${BASE}/operators`);
  if (!r.ok) throw new Error(`获取干员列表失败: ${r.statusText}`);
  const data = await r.json();
  return data.operators;
}

export async function fetchOperatorDetail(name: string): Promise<OperatorSummary> {
  const r = await fetch(`${BASE}/operators/${encodeURIComponent(name)}`);
  if (!r.ok) throw new Error(`获取干员详情失败: ${r.statusText}`);
  return r.json();
}

export async function computeDamage(req: ComputeRequest): Promise<ComputeResponse> {
  const r = await fetch(`${BASE}/compute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!r.ok) {
    const text = await r.text();
    throw new Error(`计算失败 (${r.status}): ${text}`);
  }
  return r.json();
}
