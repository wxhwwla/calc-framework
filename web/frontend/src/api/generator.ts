const BASE = "/api/generator";

export interface TemplateInfo {
  name: string;
  description: string;
}

export interface TemplateDetail {
  id: string;
  meta: Record<string, unknown>;
  files: string[];
  dag_preview?: {
    variables: number;
    nodes: number;
    outputs: number;
  };
}

export interface VariableDef {
  name: string;
  type: string;
  source: string;
  default: number | boolean;
  description: string;
}

export interface FormulaStep {
  id: string;
  op: string;
  lhs?: string;
  rhs?: string;
  cond?: string;
  true_val?: string;
  false_val?: string;
  expr?: string;
  input_map?: Record<string, string>;
  label?: string;
}

export interface OutputDef {
  name: string;
  node?: string;
  label?: string;
  format?: string;
  is_primary?: boolean;
}

export interface GenerateRequest {
  template_id: string;
  game_name: string;
  variables: VariableDef[];
  formula_steps: FormulaStep[];
  outputs: OutputDef[];
}

export async function fetchTemplates(): Promise<Record<string, TemplateInfo>> {
  const r = await fetch(BASE + "/templates");
  if (!r.ok) throw new Error(`Failed: ${r.statusText}`);
  return r.json();
}

export async function fetchTemplateDetail(id: string): Promise<TemplateDetail> {
  const r = await fetch(BASE + "/templates/" + encodeURIComponent(id));
  if (!r.ok) throw new Error(`Failed: ${r.statusText}`);
  return r.json();
}

export async function generateAdapter(req: GenerateRequest): Promise<{ success: boolean; files: Record<string, string>; file_count: number }> {
  const r = await fetch(BASE + "/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!r.ok) {
    const text = await r.text();
    throw new Error(`Generate failed: ${text}`);
  }
  return r.json();
}
