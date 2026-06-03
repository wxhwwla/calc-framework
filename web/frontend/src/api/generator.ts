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

// ---- AI 公式解析相关 ---- //

export interface AIFormulaRequest {
  api_key: string;
  api_base?: string;
  model?: string;
  formula_description: string;
  template_id: string;
  variables_context?: Record<string, unknown>[];
}

export interface AIFormulaResponse {
  variables: Array<{
    name: string;
    type: string;
    source: string;
    default: number;
    description: string;
  }>;
  formula_steps: Array<{
    id: string;
    op: string;
    lhs?: string;
    rhs?: string;
    cond?: string;
    true_val?: string;
    false_val?: string;
    expr?: string;
    input_map?: Record<string, string>;
    label: string;
  }>;
  outputs: Array<{
    name: string;
    node: string;
    label: string;
    is_primary: boolean;
  }>;
  raw_response: string;
  validation_warnings?: string[];
}

export interface AITestRequest {
  api_key: string;
  api_base?: string;
  model?: string;
}

export async function aiParseFormula(req: AIFormulaRequest): Promise<AIFormulaResponse> {
  const r = await fetch(BASE + "/ai/parse", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!r.ok) {
    const text = await r.text();
    throw new Error(`AI 解析失败: ${text}`);
  }
  return r.json();
}

export async function aiTestConnection(req: AITestRequest): Promise<{ status: string; model?: string; message?: string }> {
  const r = await fetch(BASE + "/ai/test", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  return r.json();
}
